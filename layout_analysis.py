import layoutparser as lp
import cv2
import numpy as np
from pathlib import Path
import os
import shutil

# Configuration for Layout Models
CACHE_DIR = Path.home() / ".torch/iopath_cache"

MODEL_CATALOG = {
    "publaynet": {
        "config_rel": "s/u9wbsfwz4y0ziki/config.yml",
        "model_rel": "s/d9fc9tahfzyl6df/model_final.pth",
        "label_map": {0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
        "text_types": ["Text", "Title", "List"],
        "threshold": 0.4
    },
    "prima": {
        "config_rel": "s/yc92x97k50abynt/config.yaml",
        "model_rel": "s/h7th27jfv19rxiy/model_final.pth",
        # Attempting 1-based indexing which is common for PRIMA in some contexts, 
        # or correcting for previous observation where Text was detected as class 1.
        "label_map": {1: "TextRegion", 2: "ImageRegion", 3: "TableRegion", 4: "MathsRegion", 5: "SeparatorRegion", 6: "OtherRegion"},
        "text_types": ["TextRegion", "TitleRegion"], # PRIMA doesn't strictly have Title/List separate often? TextRegion covers most.
        "threshold": 0.5
    }
}

def calculate_iou(box1, box2):
    """
    Calculate Intersection over Union (IoU) between two bounding boxes.
    Box format: [x1, y1, x2, y2]
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Intersection coordinates
    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)
    
    inter_width = max(0, xi2 - xi1)
    inter_height = max(0, yi2 - yi1)
    inter_area = inter_width * inter_height
    
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0
        
    return inter_area / union_area

def get_local_model_paths(model_name):
    """
    Ensures model files exist locally and returns their paths.
    """
    if model_name not in MODEL_CATALOG:
        raise ValueError(f"Unknown model: {model_name}")
        
    info = MODEL_CATALOG[model_name]
    config_path = CACHE_DIR / info["config_rel"]
    model_path = CACHE_DIR / info["model_rel"]
    
    # Check if they exist without query strings
    if config_path.exists() and model_path.exists():
        return str(config_path), str(model_path)
        
    # Check if they exist WITH query strings (from previous partial downloads)
    config_path_dl = Path(str(config_path) + "?dl=1")
    model_path_dl = Path(str(model_path) + "?dl=1")
    
    if config_path_dl.exists():
        print(f"Renaming cached config: {config_path_dl.name} -> {config_path.name}")
        config_path_dl.rename(config_path)
        
    if model_path_dl.exists():
        print(f"Renaming cached model: {model_path_dl.name} -> {model_path.name}")
        model_path_dl.rename(model_path)
        
    if config_path.exists() and model_path.exists():
        return str(config_path), str(model_path)

    # If still missing, trigger download via dummy init
    print(f"Downloading LayoutParser model weights ({model_name})... this may take a while...")
    
    # Map model_name back to LP URL for download trigger
    lp_url_map = {
        "publaynet": 'lp://PubLayNet/mask_rcnn_R_50_FPN_3x/config',
        "prima": 'lp://PrimaLayout/mask_rcnn_R_50_FPN_3x/config'
    }
    
    try:
        lp.Detectron2LayoutModel(
            config_path=lp_url_map[model_name],
            device='cpu'
        )
    except Exception as e:
        pass
        
    # Try renaming again
    if config_path_dl.exists():
        config_path_dl.rename(config_path)
    if model_path_dl.exists():
        model_path_dl.rename(model_path)
        
    if config_path.exists() and model_path.exists():
        return str(config_path), str(model_path)
        
    raise RuntimeError(f"Failed to download or locate LayoutParser model files for {model_name}.\nExpected:\n{config_path}\n{model_path}")

def init_layout_model(model_name="publaynet"):
    config_path, model_path = get_local_model_paths(model_name)
    info = MODEL_CATALOG[model_name]
    
    model = lp.Detectron2LayoutModel(
        config_path=config_path,
        model_path=model_path,
        extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", info["threshold"]],
        label_map=info["label_map"],
        device='cpu' 
    )
    # Store text_types in model object for easy access in analyze_image
    model.text_types = info["text_types"]
    return model

def analyze_image(image, model):
    """
    Analyzes the image and returns a list of cropped text images (columns/blocks).
    Uses content-aware filtering to remove headers and footers.
    """
    if not isinstance(image, np.ndarray):
        image = np.array(image)
        
    layout = model.detect(image)
    h, w = image.shape[:2]
    
    # 1. Initial Type Filtering
    # Use text_types stored in model, or default
    valid_types = getattr(model, "text_types", ["Text", "Title", "List"])
    
    raw_blocks = [b for b in layout if b.type in valid_types]
    
    # Debug unknown types
    # unknown = [b for b in layout if b.type not in valid_types]
    # if unknown:
    #     print(f"    [Debug] Ignored blocks types: {set(b.type for b in unknown)}")
    
    # 2. Deduplication (IoU)
    raw_blocks.sort(key=lambda x: x.score, reverse=True)
    unique_blocks = []
    for block in raw_blocks:
        is_duplicate = False
        for kept_block in unique_blocks:
            iou = calculate_iou(block.coordinates, kept_block.coordinates)
            if iou > 0.9: 
                is_duplicate = True
                break
        if not is_duplicate:
            unique_blocks.append(block)
            
    # 3. Smart Header/Footer Filtering (Anchor-based)
    anchors = []
    candidates = [] 
    
    height_threshold = h * 0.02
    
    # Define what constitutes an 'anchor' type (strong content)
    # For PubLayNet: Title, List are strong.
    # For PRIMA: TextRegion is broad, no explicit "Title". 
    # So for PRIMA, we rely more on height.
    anchor_types = ["Title", "List", "TitleRegion"]
    
    for b in unique_blocks:
        x1, y1, x2, y2 = b.coordinates
        b_h = y2 - y1
        
        if b.type in anchor_types:
            anchors.append(b)
            continue
            
        if b_h > height_threshold:
            anchors.append(b)
        else:
            candidates.append(b)
            
    final_blocks = []
    if anchors:
        min_y = min(b.coordinates[1] for b in anchors)
        max_y = max(b.coordinates[3] for b in anchors)
        
        final_blocks.extend(anchors)
        
        for b in candidates:
            x1, y1, x2, y2 = b.coordinates
            cy = (y1 + y2) / 2
            
            if cy < min_y:
                continue
            if cy > max_y:
                continue
            final_blocks.append(b)
    else:
        header_thresh = h * 0.10
        footer_thresh = h * 0.90
        
        for b in unique_blocks:
            x1, y1, x2, y2 = b.coordinates
            cy = (y1 + y2) / 2
            if header_thresh < cy < footer_thresh:
                final_blocks.append(b)
                
    text_layout = lp.Layout(final_blocks)
    return text_layout

def get_text_image_regions(image, layout):
    """
    Returns list of PIL images cropped from the main image based on layout blocks.
    Sorted in reading order.
    """
    # Sort layout
    # We will assume a general left-to-right, top-to-bottom reading order might be wrong for columns.
    # Let's use a custom sort:
    # Split into columns based on X overlap?
    
    # Simple Column Sorting:
    # 1. Identify columns.
    # If we strictly sort by (x, y), we might get Paragraph 1 (Col 1), Paragraph 1 (Col 2), Paragraph 2 (Col 1)... BAD.
    # We want (Col 1 Para 1, Col 1 Para 2...), (Col 2 Para 1...)
    
    # Heuristic:
    # If blocks overlap vertically significantly but are separated horizontally, they are in different columns.
    
    blocks = list(layout)
    if not blocks:
        return []
        
    # Group by rough X coordinate
    # We can use k-means or simple histogram.
    # Let's use a gap threshold.
    
    # Sort by x first to find columns
    blocks.sort(key=lambda b: b.coordinates[0])
    
    # Better approach for OCR:
    # If we have a good layout model, it gives us "TextRegion" blocks which are usually paragraphs.
    # If we process them in the wrong order, the audio will be garbled.
    # Standard academic paper: 2 columns.
    # We should sort by: X-bin, then Y.
    
    # Define bin function
    def get_column_bin(block, page_w):
        cx = (block.coordinates[0] + block.coordinates[2]) / 2
        if cx < page_w / 2:
            return 0 # Left
        else:
            return 1 # Right
            
    # Assuming max 2 columns for now (common case).
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    h, w = image.shape[:2]
    
    # Bin blocks
    left_col = []
    right_col = []
    
    for b in blocks:
        if get_column_bin(b, w) == 0:
            left_col.append(b)
        else:
            right_col.append(b)
            
    # Sort each column by Y
    left_col.sort(key=lambda b: b.coordinates[1])
    right_col.sort(key=lambda b: b.coordinates[1])
    
    sorted_blocks = left_col + right_col
    
    # Crop images
    cropped_images = []
    for b in sorted_blocks:
        x1, y1, x2, y2 = map(int, b.coordinates)
        # Pad slightly?
        pad = 10 # Increased from 5 to 10
        x1 = max(0, x1 - pad)
        y1 = max(0, y1 - pad)
        x2 = min(w, x2 + pad)
        y2 = min(h, y2 + pad)
        
        crop = image[y1:y2, x1:x2]
        # Convert to PIL for Tesseract compatibility downstream
        from PIL import Image
        crop_pil = Image.fromarray(crop)
        cropped_images.append(crop_pil)
        
    return cropped_images
