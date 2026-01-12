import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from split_pdf import extract_sentences_from_pdf, process_page_image

class TestProcessPageImage:
    """Test suite for process_page_image function"""

    @patch('split_pdf.Image') # Mock PIL Image if needed, though we usually mock the instance
    def test_basic_image_processing(self, mock_image_cls):
        """Test basic processing without cropping or splitting"""
        # Create a mock PIL image
        mock_pil_image = Mock()
        mock_pil_image.size = (1000, 1000)
        # Mock crop to return itself or another mock
        mock_pil_image.crop.return_value = mock_pil_image

        # Mock page
        mock_page = Mock()
        mock_page.render.return_value.to_pil.return_value = mock_pil_image

        # Call function
        # columns=1, header=0, footer=0
        results = process_page_image(mock_page, 1, 0, 0)
        
        assert len(results) == 1
        # Check initial crop (header/footer)
        # crop_top=0, crop_bottom=0 -> crop(0, 0, 1000, 1000)
        # split crop (0, 0, 1000, 1000)
        assert mock_pil_image.crop.call_count == 2 

    def test_cropping(self):
        """Test header and footer cropping"""
        mock_pil_image = Mock()
        mock_pil_image.size = (1000, 1000)
        mock_cropped = Mock()
        mock_cropped.size = (1000, 800) # After 100 top and 100 bottom removed
        
        def crop_side_effect(box):
            # box is (left, upper, right, lower)
            if box == (0, 300, 1000, 700): # Header 100*3, Footer 100*3
                 return mock_cropped
            return mock_cropped # Default return for the column split

        mock_pil_image.crop.side_effect = crop_side_effect
        
        mock_page = Mock()
        mock_page.render.return_value.to_pil.return_value = mock_pil_image

        # header=100, footer=100 (scaled by 3 internally = 300)
        process_page_image(mock_page, 1, 100, 100)
        
        # Verify first crop call
        mock_pil_image.crop.assert_any_call((0, 300, 1000, 700))

    def test_column_splitting(self):
        """Test splitting into columns"""
        mock_pil_image = Mock()
        mock_pil_image.size = (1000, 1000)
        
        # First crop (header/footer) returns the full image (no crop)
        mock_pil_image.crop.return_value = mock_pil_image
        
        mock_page = Mock()
        mock_page.render.return_value.to_pil.return_value = mock_pil_image

        # columns=2
        results = process_page_image(mock_page, 2, 0, 0)
        
        assert len(results) == 2
        # Check split crops
        # Width 1000. Col 1: 0-500. Col 2: 500-1000.
        mock_pil_image.crop.assert_any_call((0, 0, 500, 1000))
        mock_pil_image.crop.assert_any_call((500, 0, 1000, 1000))

class TestExtractSentencesOCR:
    """Test suite for extract_sentences_from_pdf with OCR"""
    
    @patch('split_pdf.pdfium')
    @patch('split_pdf.pytesseract')
    @patch('split_pdf.sent_tokenize')
    def test_ocr_extraction(self, mock_sent_tokenize, mock_pytesseract, mock_pdfium, tmp_path):
        """Test standard OCR extraction workflow"""
        # Mock PDF
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 1
        mock_pdf.__iter__.return_value = [Mock()] # One page
        mock_pdfium.PdfDocument.return_value = mock_pdf
        
        # Mock Image processing
        with patch('split_pdf.process_page_image') as mock_proc:
            mock_img = Mock()
            mock_proc.return_value = [mock_img] # Single column/image
            
            # Mock OCR text
            mock_pytesseract.image_to_string.return_value = "OCR Text."
            
            # Mock Tokenizer
            mock_sent_tokenize.return_value = ["OCR Text."]
            
            extract_sentences_from_pdf("dummy.pdf", str(tmp_path), ocr=True)
            
            # Verify file created
            output_file = tmp_path / "page_1.txt"
            assert output_file.exists()
            assert output_file.read_text(encoding="utf-8").strip() == "OCR Text."
            
            # Verify OCR called
            mock_pytesseract.image_to_string.assert_called_with(mock_img)

    @patch('split_pdf.pytesseract')
    @patch('split_pdf.pdfium')
    def test_ocr_dry_run(self, mock_pdfium, mock_pytesseract, tmp_path):
        """Test OCR dry run mode"""
        mock_pdf = MagicMock()
        mock_pdf.__len__.return_value = 10
        # Create 10 mock pages
        mock_pages = [Mock() for _ in range(10)]
        
        # Allow indexing for loop: pdf[i]
        def get_item(i):
            return mock_pages[i]
        mock_pdf.__getitem__ = Mock(side_effect=get_item)
        
        mock_pdfium.PdfDocument.return_value = mock_pdf
        mock_pytesseract.image_to_string.return_value = "Preview Text"
        
        with patch('split_pdf.process_page_image') as mock_proc:
            mock_img = Mock()
            mock_proc.return_value = [mock_img]
            
            # Run with start_page=5
            extract_sentences_from_pdf("dummy.pdf", str(tmp_path), ocr=True, dry_run=True, start_page=5)
            
            # Verify preview directory created
            preview_dir = tmp_path / "ocr_preview"
            assert preview_dir.exists()
            
            # Should process 5 pages: 5, 6, 7, 8, 9 (indices) which correspond to page_6 to page_10
            # Check for page_6 (index 5)
            assert (preview_dir / "page_6_block_1.png").exists() or mock_img.save.call_count >= 1
            assert (preview_dir / "page_6_block_1.txt").exists()
            
            # Check content
            with open(preview_dir / "page_6_block_1.txt", "r") as f:
                assert f.read() == "Preview Text"
            
            # Ensure we started at index 5
            # We can check which pages were accessed via pdf[i]
            # but simpler to check the filenames saved or the calls to process_page_image
            # process_page_image(pdf[i], ...)
            
            # We expect 5 calls (indices 5,6,7,8,9)
            assert mock_proc.call_count == 5
            
            # Verify calls were for the correct pages
            mock_proc.assert_any_call(mock_pages[5], 1, 0, 0)
            mock_proc.assert_any_call(mock_pages[9], 1, 0, 0)
            
            # Ensure index 0 was NOT called
            with pytest.raises(AssertionError):
                mock_proc.assert_any_call(mock_pages[0], 1, 0, 0)
