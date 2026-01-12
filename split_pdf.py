# split_pdf.py
import os
import sys
import argparse
import nltk
import re
from pathlib import Path
from PyPDF2 import PdfReader

# Optional imports for OCR
try:
    import pypdfium2 as pdfium
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# Layout Analysis import
try:
    import layout_analysis
    LAYOUT_AVAILABLE = True
except ImportError:
    LAYOUT_AVAILABLE = False

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.tokenize import sent_tokenize

def clean_pdf_text(raw_text: str) -> str:
    # Replace hyphenated line breaks (e.g. "multi-\nline") with joined word
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', raw_text)

    # Replace line breaks that are not end of sentence with space
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Collapse multiple newlines into paragraph breaks
    text = re.sub(r'\n{2,}', '\n\n', text)

    # Remove weird extra spaces
    text = re.sub(r' +', ' ', text)

    # Fix common AI OCR misidentifications (whole words only)
    text = re.sub(r'\bAl\b', 'AI', text)
    text = re.sub(r'\bOpenAl\b', 'OpenAI', text)
    text = re.sub(r'\bEl\b', 'AI', text)

    return text.strip()

def process_page_image(page, columns: int, header_h: int, footer_h: int):
    """
    Render page to image, crop header/footer, split into columns.
    Returns list of PIL images (one per column).
    """
    # Render high-res image (scale=3 is usually good for OCR)
    bitmap = page.render(scale=3)
    pil_image = bitmap.to_pil()
    
    width, height = pil_image.size
    
    # Calculate crop box (left, upper, right, lower)
    # Ensure we don't crop beyond image bounds
    crop_top = min(header_h * 3, height) # scale factor 3
    crop_bottom = min(footer_h * 3, height)
    
    if crop_top + crop_bottom >= height:
        # If crops are too aggressive, return empty
        return []

    cropped_img = pil_image.crop((0, crop_top, width, height - crop_bottom))
    
    # Split into columns
    c_width, c_height = cropped_img.size
    col_width = c_width // columns
    
    column_images = []
    for i in range(columns):
        left = i * col_width
        # For the last column, take the rest of the width to avoid rounding errors
        right = (i + 1) * col_width if i < columns - 1 else c_width
        col_img = cropped_img.crop((left, 0, right, c_height))
        column_images.append(col_img)
        
    return column_images

class TextQualityFilter:
    def __init__(self):
        self.line_lengths = []
        
    def _get_stats(self):
        if not self.line_lengths:
            return 0, 0
        mean = sum(self.line_lengths) / len(self.line_lengths)
        variance = sum((x - mean) ** 2 for x in self.line_lengths) / len(self.line_lengths)
        std = variance ** 0.5
        return mean, std

    def is_valid(self, text: str) -> tuple[bool, str]:
        """
        Returns (is_valid, reason)
        """
        if not text.strip():
            return False, "Empty text"
            
        # 1. Broken Text Check (Alphanumeric Density)
        # Remove whitespace
        clean = re.sub(r'\s', '', text)
        if not clean:
            return False, "Whitespace only"
            
        alpha_count = len(re.findall(r'[a-zA-Z0-9]', clean))
        ratio = alpha_count / len(clean)
        
        if ratio < 0.5:
            return False, f"Low alphanumeric density: {ratio:.2f}"
            
        # 2. Line Length Outlier Check
        # Calculate average line length for this block
        lines = [l for l in text.split('\n') if l.strip()]
        if not lines:
            return False, "No valid lines"
            
        block_avg_len = sum(len(l) for l in lines) / len(lines)
        
        mean, std = self._get_stats()
        
        # Only check if we have enough history (e.g. > 5 blocks)
        if len(self.line_lengths) > 5:
            # Threshold: mean + 2 * std
            # We assume significantly longer is bad (e.g. table rows, full page headers)
            # significantly shorter is usually fine (short paragraphs)
            if block_avg_len > mean + 2 * std:
                return False, f"Line length outlier: {block_avg_len:.1f} > {mean:.1f} + 2*{std:.1f}"
        
        return True, "OK"

    def add(self, text: str):
        """Update stats with valid text block"""
        lines = [l for l in text.split('\n') if l.strip()]
        for l in lines:
            self.line_lengths.append(len(l))

    def deduplicate(self, candidates):
        """
        Filters out candidates that are subsets of other candidates.
        candidates: list of dicts {'text': str, ...}
        Returns: filtered list of candidates
        """
        accepted = []
        for cand in candidates:
            c_text = cand['text']
            # Normalize for comparison: lower case, single space
            c_norm = " ".join(c_text.split()).lower()
            if not c_norm:
                continue
            
            is_handled = False
            for i, acc in enumerate(accepted):
                a_text = acc['text']
                a_norm = " ".join(a_text.split()).lower()
                
                # Check 1: Current is strictly inside Accepted? -> Discard Current
                if c_norm in a_norm:
                    is_handled = True
                    # Log/Debug? "Discarding duplicate subset..."
                    break
                
                # Check 2: Accepted is strictly inside Current? -> Replace Accepted with Current
                if a_norm in c_norm:
                    accepted[i] = cand
                    is_handled = True
                    break
            
            if not is_handled:
                accepted.append(cand)
                
        return accepted

def extract_sentences_from_pdf(pdf_path: str, output_dir: str, 
                             ocr: bool = False, columns: int = 1, 
                             header_h: int = 0, footer_h: int = 0, 
                             dry_run: bool = False, start_page: int = 0,
                             auto_layout: bool = False, model_name: str = "publaynet"):
    
    if ocr and not OCR_AVAILABLE:
        print("Error: OCR dependencies (pypdfium2, pytesseract, Pillow) not found.")
        sys.exit(1)
        
    if auto_layout and not LAYOUT_AVAILABLE:
        print("Error: Layout Analysis dependencies (layoutparser, detectron2, torch) not found or failed to load.")
        sys.exit(1)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize Text Quality Filter
    quality_filter = TextQualityFilter()

    if ocr:
        print(f"📷 Processing with OCR: {pdf_path}")
        pdf = pdfium.PdfDocument(pdf_path)
        
        layout_model = None
        if auto_layout:
            print(f"🤖 Initializing Layout Analysis Model ({model_name})...")
            layout_model = layout_analysis.init_layout_model(model_name)
        
        if dry_run:
            preview_dir = output_path / "ocr_preview"
            preview_dir.mkdir(exist_ok=True)
            print(f"🔎 Dry Run: Saving pages {start_page+1} to {min(start_page+5, len(pdf))} to {preview_dir}")
            
            all_dry_run_text = []
            limit = min(start_page + 5, len(pdf))
            
            for i in range(start_page, limit):
                if auto_layout:
                    # Render full page
                    bitmap = pdf[i].render(scale=3)
                    pil_image = bitmap.to_pil()
                    layout = layout_analysis.analyze_image(pil_image, layout_model)
                    col_imgs = layout_analysis.get_text_image_regions(pil_image, layout)
                    
                    if not col_imgs:
                        print(f"  ⚠️ No text blocks detected for Page {i+1}. Saving full page debug image.")
                        pil_image.save(preview_dir / f"page_{i+1}_debug_full.png")
                        continue
                else:
                    col_imgs = process_page_image(pdf[i], columns, header_h, footer_h)
                
                # 1. Collect all candidates for the page
                page_candidates = []
                for c_idx, img in enumerate(col_imgs):
                    text = pytesseract.image_to_string(img)
                    page_candidates.append({
                        'text': text,
                        'img': img,
                        'id': c_idx + 1 # 1-based index
                    })
                
                # 2. Deduplicate
                unique_candidates = quality_filter.deduplicate(page_candidates)
                if len(unique_candidates) < len(page_candidates):
                    print(f"  ✂️  Deduplicated {len(page_candidates) - len(unique_candidates)} blocks on page {i+1}.")

                page_text_blocks = []
                for cand in unique_candidates:
                    text = cand['text']
                    img = cand['img']
                    c_id = cand['id']
                    
                    base_name = f"page_{i+1}_block_{c_id}"
                    img_path = preview_dir / f"{base_name}.png"
                    img.save(img_path)
                    
                    # Check Quality
                    is_valid, reason = quality_filter.is_valid(text)
                    
                    status = "✅" if is_valid else "❌"
                    print(f"  {status} Block {c_id}: {reason}")
                    
                    if is_valid:
                        quality_filter.add(text)
                        txt_path = preview_dir / f"{base_name}.txt"
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write(text)
                        page_text_blocks.append(text)
                    else:
                        # Save rejected text with reason for inspection
                        txt_path = preview_dir / f"{base_name}_REJECTED.txt"
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write(f"REASON: {reason}\n\n{text}")
                
                # Save stitched page text
                if page_text_blocks:
                    raw_page_text = "\n".join(page_text_blocks)
                    cleaned_page_text = clean_pdf_text(raw_page_text)
                    all_dry_run_text.append(cleaned_page_text)
                    
                    page_txt_path = preview_dir / f"page_{i+1}.txt"
                    with open(page_txt_path, "w", encoding="utf-8") as f:
                        f.write(cleaned_page_text)
                    print(f"  📄 Saved stitched page: {page_txt_path.name}")

            # Save full text for dry run
            if all_dry_run_text:
                full_text_path = preview_dir / "full_text.txt"
                with open(full_text_path, "w", encoding="utf-8") as f:
                    f.write("\n\n".join(all_dry_run_text))
                print(f"📁 Combined dry-run text saved: {full_text_path}")
                
            return

        all_pages_text = []
        for i in range(start_page, len(pdf)):
            page = pdf[i]
            
            if auto_layout:
                bitmap = page.render(scale=3)
                pil_image = bitmap.to_pil()
                layout = layout_analysis.analyze_image(pil_image, layout_model)
                col_imgs = layout_analysis.get_text_image_regions(pil_image, layout)
            else:
                col_imgs = process_page_image(page, columns, header_h, footer_h)
            
            # 1. Collect
            page_candidates = []
            for img in col_imgs:
                text = pytesseract.image_to_string(img)
                page_candidates.append({'text': text})
            
            # 2. Deduplicate
            unique_candidates = quality_filter.deduplicate(page_candidates)
            if len(unique_candidates) < len(page_candidates):
                print(f"  ✂️  Deduplicated {len(page_candidates) - len(unique_candidates)} blocks on page {i+1}.")
            
            # 3. Filter and Accumulate
            full_text = ""
            for cand in unique_candidates:
                text = cand['text']
                is_valid, reason = quality_filter.is_valid(text)
                if is_valid:
                    quality_filter.add(text)
                    full_text += text + "\n"
                else:
                    print(f"  ⚠️ Page {i+1}: Skipped block due to: {reason}")
            
            cleaned_text = clean_pdf_text(full_text)
            all_pages_text.append(cleaned_text)
            sentences = sent_tokenize(cleaned_text)
            
            out_file = output_path / f"page_{i + 1}.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                for sentence in sentences:
                    f.write(sentence.strip() + "\n")
            print(f"✅ Saved: {out_file}")

        # Save concatenated full text
        full_text_path = output_path / "full_text.txt"
        with open(full_text_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_pages_text))
        print(f"📁 Combined text saved: {full_text_path}")

    else:
        # Standard text extraction
        reader = PdfReader(pdf_path)
        all_pages_text = []
        for i in range(start_page, len(reader.pages)):
            page = reader.pages[i]
            text = page.extract_text()
            if not text:
                print(f"Page {i + 1} is empty or unreadable.")
                continue
            
            cleaned_text = clean_pdf_text(text)
            all_pages_text.append(cleaned_text)
            sentences = sent_tokenize(cleaned_text)
            out_file = output_path / f"page_{i + 1}.txt"
            with open(out_file, "w", encoding="utf-8") as f:
                for sentence in sentences:
                    f.write(sentence.strip() + "\n")
            print(f"✅ Saved: {out_file}")

        # Save concatenated full text
        full_text_path = output_path / "full_text.txt"
        with open(full_text_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_pages_text))
        print(f"📁 Combined text saved: {full_text_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split PDF into sentences per page.")
    parser.add_argument("pdf_path", help="Path to source PDF")
    parser.add_argument("output_dir", help="Directory to save output files")
    
    # OCR options
    parser.add_argument("--ocr", action="store_true", help="Use OCR (pypdfium2 + tesseract)")
    parser.add_argument("--columns", type=int, default=1, help="Number of columns to split page into (for OCR)")
    parser.add_argument("--header-height", type=int, default=0, help="Pixels to crop from top (at 72dpi equivalent)")
    parser.add_argument("--footer-height", type=int, default=0, help="Pixels to crop from bottom (at 72dpi equivalent)")
    parser.add_argument("--dry-run", action="store_true", help="OCR Dry run: save images of first 5 pages")
    parser.add_argument("--start-page", type=int, default=0, help="Start processing from this page number (0-indexed)")
    parser.add_argument("--auto-layout", action="store_true", help="Use Deep Learning to detect layout (ignore manual cols/header)")
    parser.add_argument("--model", default="publaynet", choices=["publaynet", "prima"], help="Layout analysis model to use")

    args = parser.parse_args()

    extract_sentences_from_pdf(
        args.pdf_path, 
        args.output_dir, 
        ocr=args.ocr,
        columns=args.columns,
        header_h=args.header_height,
        footer_h=args.footer_height,
        dry_run=args.dry_run,
        start_page=args.start_page,
        auto_layout=args.auto_layout,
        model_name=args.model
    )

