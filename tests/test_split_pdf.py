import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from split_pdf import clean_pdf_text, extract_sentences_from_pdf


class TestCleanPdfText:
    """Test suite for clean_pdf_text function"""

    def test_clean_hyphenated_line_breaks(self):
        """Test that hyphenated words across line breaks are joined"""
        raw_text = "This is a multi-\nline word"
        expected = "This is a multiline word"
        assert clean_pdf_text(raw_text) == expected

    def test_clean_simple_line_breaks(self):
        """Test that single line breaks are replaced with spaces"""
        raw_text = "First line\nSecond line"
        expected = "First line Second line"
        assert clean_pdf_text(raw_text) == expected

    def test_preserve_paragraph_breaks(self):
        """Test that multiple newlines are collapsed into paragraph breaks"""
        raw_text = "First paragraph\n\n\n\nSecond paragraph"
        expected = "First paragraph\n\nSecond paragraph"
        assert clean_pdf_text(raw_text) == expected

    def test_remove_extra_spaces(self):
        """Test that multiple spaces are collapsed into single spaces"""
        raw_text = "This  has    multiple     spaces"
        expected = "This has multiple spaces"
        assert clean_pdf_text(raw_text) == expected

    def test_strip_whitespace(self):
        """Test that leading and trailing whitespace is removed"""
        raw_text = "   Some text with spaces   \n"
        expected = "Some text with spaces"
        assert clean_pdf_text(raw_text) == expected

    def test_complex_text_cleaning(self):
        """Test cleaning with multiple transformations"""
        raw_text = "The pro-\ngramming language\n\n\nhas many  features.\nIt is powerful."
        expected = "The programming language\n\nhas many features. It is powerful."
        assert clean_pdf_text(raw_text) == expected

    def test_empty_string(self):
        """Test that empty strings are handled correctly"""
        assert clean_pdf_text("") == ""

    def test_only_whitespace(self):
        """Test that strings with only whitespace return empty string"""
        assert clean_pdf_text("   \n\n   ") == ""


class TestExtractSentencesFromPdf:
    """Test suite for extract_sentences_from_pdf function"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_pdf_reader(self):
        """Create a mock PDF reader"""
        with patch('split_pdf.PdfReader') as mock_reader:
            yield mock_reader

    def test_creates_output_directory(self, temp_output_dir, mock_pdf_reader):
        """Test that output directory is created if it doesn't exist"""
        output_dir = os.path.join(temp_output_dir, "new_dir")

        # Mock a simple PDF with one page
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test sentence."
        mock_reader.return_value.pages = [mock_page]

        extract_sentences_from_pdf("fake.pdf", output_dir)

        assert os.path.exists(output_dir)

    def test_extracts_multiple_pages(self, temp_output_dir, mock_pdf_reader):
        """Test that multiple pages are extracted correctly"""
        # Mock PDF with 3 pages
        mock_pages = []
        for i in range(3):
            mock_page = Mock()
            mock_page.extract_text.return_value = f"Page {i+1} content."
            mock_pages.append(mock_page)

        mock_reader.return_value.pages = mock_pages

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        # Check that 3 files were created
        assert len(os.listdir(temp_output_dir)) == 3
        assert os.path.exists(os.path.join(temp_output_dir, "page_1.txt"))
        assert os.path.exists(os.path.join(temp_output_dir, "page_2.txt"))
        assert os.path.exists(os.path.join(temp_output_dir, "page_3.txt"))

    def test_handles_empty_pages(self, temp_output_dir, mock_pdf_reader, capsys):
        """Test that empty pages are handled gracefully"""
        # Mock PDF with one empty page
        mock_page = Mock()
        mock_page.extract_text.return_value = ""
        mock_reader.return_value.pages = [mock_page]

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        captured = capsys.readouterr()
        assert "Page 1 is empty or unreadable" in captured.out

    def test_handles_none_text(self, temp_output_dir, mock_pdf_reader, capsys):
        """Test that pages returning None are handled gracefully"""
        # Mock PDF with one page returning None
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        mock_reader.return_value.pages = [mock_page]

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        captured = capsys.readouterr()
        assert "Page 1 is empty or unreadable" in captured.out

    @patch('split_pdf.sent_tokenize')
    def test_tokenizes_sentences(self, mock_tokenize, temp_output_dir, mock_pdf_reader):
        """Test that text is tokenized into sentences"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "First sentence. Second sentence."
        mock_reader.return_value.pages = [mock_page]

        mock_tokenize.return_value = ["First sentence.", "Second sentence."]

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        # Read the output file
        with open(os.path.join(temp_output_dir, "page_1.txt"), "r", encoding="utf-8") as f:
            content = f.read()

        assert "First sentence." in content
        assert "Second sentence." in content
        # Each sentence should be on its own line
        lines = content.strip().split("\n")
        assert len(lines) == 2

    def test_file_encoding_utf8(self, temp_output_dir, mock_pdf_reader):
        """Test that files are written with UTF-8 encoding"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test with unicode: café, naïve, 中文"
        mock_reader.return_value.pages = [mock_page]

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        # Read the file and verify encoding works
        with open(os.path.join(temp_output_dir, "page_1.txt"), "r", encoding="utf-8") as f:
            content = f.read()

        assert "café" in content
        assert "naïve" in content
        assert "中文" in content

    def test_output_file_naming(self, temp_output_dir, mock_pdf_reader):
        """Test that output files are named correctly with page numbers"""
        mock_pages = [Mock() for _ in range(10)]
        for i, page in enumerate(mock_pages):
            page.extract_text.return_value = f"Page {i+1}"

        mock_reader.return_value.pages = mock_pages

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        # Check files are named page_1.txt through page_10.txt
        for i in range(1, 11):
            assert os.path.exists(os.path.join(temp_output_dir, f"page_{i}.txt"))

    @patch('split_pdf.sent_tokenize')
    def test_strips_sentence_whitespace(self, mock_tokenize, temp_output_dir, mock_pdf_reader):
        """Test that sentences are stripped of extra whitespace"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test"
        mock_reader.return_value.pages = [mock_page]

        # Mock tokenizer returns sentences with whitespace
        mock_tokenize.return_value = ["  First sentence.  ", " Second sentence. "]

        extract_sentences_from_pdf("fake.pdf", temp_output_dir)

        with open(os.path.join(temp_output_dir, "page_1.txt"), "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert lines[0] == "First sentence.\n"
        assert lines[1] == "Second sentence.\n"


class TestIntegration:
    """Integration tests that test the full workflow"""

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @patch('split_pdf.PdfReader')
    def test_full_workflow_single_page(self, mock_reader, temp_output_dir):
        """Test full workflow with a single page PDF"""
        # Create a realistic PDF page with typical formatting issues
        mock_page = Mock()
        mock_page.extract_text.return_value = (
            "This is a docu-\nment with multiple issues.  "
            "It has extra  spaces.\n\n\n"
            "And paragraph breaks."
        )
        mock_reader.return_value.pages = [mock_page]

        extract_sentences_from_pdf("test.pdf", temp_output_dir)

        # Verify file was created
        output_file = os.path.join(temp_output_dir, "page_1.txt")
        assert os.path.exists(output_file)

        # Verify content is cleaned and tokenized
        with open(output_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Should not have hyphenated line breaks
        assert "docu-\nment" not in content
        # Should have cleaned text
        assert "document" in content
        # Should have multiple sentences on separate lines
        lines = [line for line in content.split("\n") if line.strip()]
        assert len(lines) > 0
