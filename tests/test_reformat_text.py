import pytest
import os
import tempfile
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reformat_text import (
    should_start_new_paragraph,
    clean_text,
    write_output,
    LIST_ITEM_RE,
    HEADLINE_RE,
    CONTINUATION_WORDS
)


class TestRegexPatterns:
    """Test suite for regex patterns"""

    def test_list_item_regex_numbered_dot(self):
        """Test list item regex matches numbered items with dots"""
        assert LIST_ITEM_RE.match("1. First item")
        assert LIST_ITEM_RE.match("10. Tenth item")
        assert LIST_ITEM_RE.match("  1. Indented item")

    def test_list_item_regex_numbered_paren(self):
        """Test list item regex matches numbered items with parentheses"""
        assert LIST_ITEM_RE.match("1) First item")
        assert LIST_ITEM_RE.match("10) Tenth item")

    def test_list_item_regex_bullet(self):
        """Test list item regex matches bullet points"""
        assert LIST_ITEM_RE.match("• Bullet point")
        assert LIST_ITEM_RE.match("- Dash item")

    def test_list_item_regex_no_match(self):
        """Test list item regex doesn't match regular text"""
        assert not LIST_ITEM_RE.match("Regular text")
        assert not LIST_ITEM_RE.match("No number here")

    def test_headline_regex_all_caps(self):
        """Test headline regex matches all caps text"""
        assert HEADLINE_RE.match("THIS IS A HEADLINE")
        assert HEADLINE_RE.match("INTRODUCTION AND OVERVIEW")

    def test_headline_regex_with_punctuation(self):
        """Test headline regex matches headlines with allowed punctuation"""
        assert HEADLINE_RE.match("CHAPTER 1: THE BEGINNING")
        assert HEADLINE_RE.match("SECTION A-1")

    def test_headline_regex_no_match_mixed_case(self):
        """Test headline regex doesn't match mixed case"""
        assert not HEADLINE_RE.match("This Is Not A Headline")
        assert not HEADLINE_RE.match("Regular sentence here.")


class TestShouldStartNewParagraph:
    """Test suite for should_start_new_paragraph function"""

    def test_first_line_always_starts_paragraph(self):
        """Test that the first line (no previous line) starts a paragraph"""
        assert should_start_new_paragraph("", "First line")

    def test_list_item_starts_paragraph(self):
        """Test that list items start new paragraphs"""
        assert should_start_new_paragraph("Previous text.", "1. First item")
        assert should_start_new_paragraph("Previous text.", "• Bullet point")
        assert should_start_new_paragraph("Previous text.", "- Dash item")

    def test_headline_starts_paragraph(self):
        """Test that headlines start new paragraphs"""
        assert should_start_new_paragraph("Previous text.", "INTRODUCTION AND OVERVIEW")
        assert should_start_new_paragraph("Previous text.", "CHAPTER ONE")

    def test_single_word_headline_no_paragraph(self):
        """Test that single word all-caps behavior"""
        # Single word all-caps is not treated as headline (requires 2+ words)
        # "AND" (all caps) is NOT a continuation word (only "And" title case is)
        # So after sentence ending (period), "AND" starts a new paragraph
        result = should_start_new_paragraph("Previous text.", "AND")
        assert result == True, "AND (all caps) is not a continuation word"

        # But "And" (title case) IS a continuation word
        result = should_start_new_paragraph("Previous text.", "And this continues")
        assert result == False, "And (title case) is a continuation word"

        # Test with non-continuation single word after punctuation
        assert should_start_new_paragraph("Previous text.", "WORD")

        # Test single word without previous punctuation - no new paragraph
        assert not should_start_new_paragraph("Previous text without punctuation", "WORD")

    def test_sentence_ending_starts_paragraph(self):
        """Test that new sentence after period starts paragraph"""
        assert should_start_new_paragraph("Previous sentence.", "New sentence")

    def test_continuation_word_no_paragraph(self):
        """Test that continuation words don't start new paragraph"""
        assert not should_start_new_paragraph("Previous sentence.", "And this continues")
        assert not should_start_new_paragraph("Previous sentence.", "But wait")
        assert not should_start_new_paragraph("Previous sentence.", "Because of this")

    def test_no_sentence_ending_no_paragraph(self):
        """Test that text not ending with punctuation doesn't trigger paragraph"""
        assert not should_start_new_paragraph("Previous text", "Continuation text")

    def test_question_mark_starts_paragraph(self):
        """Test that question mark can start new paragraph"""
        assert should_start_new_paragraph("Is this a question?", "New thought here")

    def test_exclamation_starts_paragraph(self):
        """Test that exclamation mark can start new paragraph"""
        assert should_start_new_paragraph("This is exciting!", "New paragraph")

    def test_colon_starts_paragraph(self):
        """Test that colon can start new paragraph"""
        assert should_start_new_paragraph("As follows:", "New paragraph")


class TestCleanText:
    """Test suite for clean_text function"""

    def test_join_hyphenated_words(self):
        """Test that hyphenated words at line end are joined"""
        lines = ["This is a docu-", "ment with text."]
        result = clean_text(lines)
        assert len(result) == 1
        assert "document" in result[0]
        assert "docu-" not in result[0]

    def test_blank_line_creates_paragraph_break(self):
        """Test that blank lines create paragraph breaks"""
        lines = ["First paragraph.", "", "Second paragraph."]
        result = clean_text(lines)
        assert len(result) == 2
        assert result[0] == "First paragraph."
        assert result[1] == "Second paragraph."

    def test_multiple_blank_lines(self):
        """Test that multiple blank lines don't create extra paragraphs"""
        lines = ["First paragraph.", "", "", "", "Second paragraph."]
        result = clean_text(lines)
        assert len(result) == 2

    def test_list_items_separate_paragraphs(self):
        """Test that list items are separated into paragraphs"""
        lines = [
            "Here is a list:",
            "1. First item",
            "2. Second item",
            "3. Third item"
        ]
        result = clean_text(lines)
        assert len(result) == 4
        assert result[0] == "Here is a list:"
        assert "1. First item" in result[1]
        assert "2. Second item" in result[2]
        assert "3. Third item" in result[3]

    def test_continuation_within_paragraph(self):
        """Test that continuation sentences stay in same paragraph"""
        lines = [
            "This is a sentence.",
            "And this continues it."
        ]
        result = clean_text(lines)
        assert len(result) == 1
        assert "This is a sentence. And this continues it." in result[0]

    def test_new_sentence_new_paragraph(self):
        """Test that new sentences (non-continuation) create paragraphs"""
        lines = [
            "This is a sentence.",
            "This is a new thought."
        ]
        result = clean_text(lines)
        assert len(result) == 2
        assert result[0] == "This is a sentence."
        assert result[1] == "This is a new thought."

    def test_headline_creates_paragraph(self):
        """Test that headlines create new paragraphs"""
        lines = [
            "Introduction text here.",
            "SECTION ONE",
            "",  # Blank line to separate
            "Section content."
        ]
        result = clean_text(lines)
        assert len(result) == 3
        assert "SECTION ONE" in result[1]
        assert "Section content." in result[2]

    def test_join_lines_within_paragraph(self):
        """Test that lines within paragraph are joined with spaces"""
        lines = [
            "This is a",
            "long sentence that",
            "spans multiple lines."
        ]
        result = clean_text(lines)
        assert len(result) == 1
        assert result[0] == "This is a long sentence that spans multiple lines."

    def test_empty_input(self):
        """Test that empty input returns empty list"""
        result = clean_text([])
        assert result == []

    def test_only_whitespace_lines(self):
        """Test that whitespace-only lines are treated as blank"""
        lines = ["First paragraph.", "   ", "  ", "Second paragraph."]
        result = clean_text(lines)
        assert len(result) == 2

    def test_strips_paragraph_whitespace(self):
        """Test that paragraphs are stripped of leading/trailing whitespace"""
        lines = ["  Text with spaces  "]
        result = clean_text(lines)
        assert result[0] == "Text with spaces"

    def test_complex_document(self):
        """Test cleaning a complex document structure"""
        lines = [
            "INTRODUCTION",
            "",
            "This is the intro-",
            "duction to the document.",
            "It has multiple sentences.",
            "",
            "MAIN CONTENT",
            "",
            "Here is the main content:",
            "1. First point",
            "2. Second point",
            "",
            "Conclusion text."
        ]
        result = clean_text(lines)

        # Should have: INTRODUCTION, intro sentence 1, intro sentence 2,
        # MAIN CONTENT, main content intro, 2 list items, conclusion
        assert len(result) >= 7
        assert "INTRODUCTION" in result[0]
        assert "introduction" in result[1]
        assert "It has multiple sentences." in result[2]
        assert "MAIN CONTENT" in result[3]


class TestWriteOutput:
    """Test suite for write_output function"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_creates_cleaned_file(self, temp_dir):
        """Test that output file is created in clean/ directory"""
        original_path = Path(temp_dir) / "test.txt"
        original_path.touch()

        paragraphs = ["First paragraph.", "Second paragraph."]
        write_output(original_path, paragraphs)

        expected_path = Path(temp_dir) / "clean" / "test.txt"
        assert expected_path.exists()

    def test_writes_paragraphs_with_blank_lines(self, temp_dir):
        """Test that paragraphs are separated by blank lines"""
        original_path = Path(temp_dir) / "test.txt"
        original_path.touch()

        paragraphs = ["First paragraph.", "Second paragraph.", "Third paragraph."]
        write_output(original_path, paragraphs)

        expected_path = Path(temp_dir) / "clean" / "test.txt"
        with open(expected_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Each paragraph should be followed by double newline
        assert "First paragraph.\n\n" in content
        assert "Second paragraph.\n\n" in content
        assert "Third paragraph.\n\n" in content

    def test_utf8_encoding(self, temp_dir):
        """Test that file is written with UTF-8 encoding"""
        original_path = Path(temp_dir) / "test.txt"
        original_path.touch()

        paragraphs = ["Unicode test: café, naïve, 中文"]
        write_output(original_path, paragraphs)

        expected_path = Path(temp_dir) / "clean" / "test.txt"
        with open(expected_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "café" in content
        assert "naïve" in content
        assert "中文" in content

    def test_strips_paragraph_whitespace_on_write(self, temp_dir):
        """Test that paragraphs are stripped before writing"""
        original_path = Path(temp_dir) / "test.txt"
        original_path.touch()

        paragraphs = ["  First paragraph.  ", " Second paragraph. "]
        write_output(original_path, paragraphs)

        expected_path = Path(temp_dir) / "clean" / "test.txt"
        with open(expected_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert lines[0] == "First paragraph.\n"

    def test_empty_paragraphs(self, temp_dir):
        """Test handling of empty paragraph list"""
        original_path = Path(temp_dir) / "test.txt"
        original_path.touch()

        paragraphs = []
        write_output(original_path, paragraphs)

        expected_path = Path(temp_dir) / "clean" / "test.txt"
        assert expected_path.exists()

        with open(expected_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert content == ""


class TestIntegration:
    """Integration tests for the full reformat workflow"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_full_reformatting_workflow(self, temp_dir):
        """Test complete workflow from input to output"""
        # Create input file with messy formatting
        input_path = Path(temp_dir) / "messy.txt"
        messy_content = """CHAPTER ONE: INTRODUCTION

This is a docu-
ment with poor formatting.  It has many issues.
And continuation sentences.

Here is a list:
1. First item
2. Second item

CONCLUSION

The document ends here."""

        with open(input_path, "w", encoding="utf-8") as f:
            f.write(messy_content)

        # Process the file
        with open(input_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        cleaned_paragraphs = clean_text(raw_lines)
        write_output(input_path, cleaned_paragraphs)

        # Verify output
        output_path = Path(temp_dir) / "clean" / "messy.txt"
        assert output_path.exists()

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check key features
        assert "document" in content  # hyphenation fixed
        assert "docu-\nment" not in content
        assert "CHAPTER ONE: INTRODUCTION" in content
        assert "1. First item" in content
        assert "CONCLUSION" in content

        # Verify paragraphs are separated
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        assert len(paragraphs) > 5

    def test_preserves_special_characters(self, temp_dir):
        """Test that special characters are preserved"""
        input_path = Path(temp_dir) / "special.txt"
        content_with_special = """Test with special chars:
"Quotes" and 'apostrophes'
Symbols: @#$%^&*()
Unicode: ñ, é, ü, 日本語"""

        with open(input_path, "w", encoding="utf-8") as f:
            f.write(content_with_special)

        with open(input_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        cleaned_paragraphs = clean_text(raw_lines)
        write_output(input_path, cleaned_paragraphs)

        output_path = Path(temp_dir) / "clean" / "special.txt"
        with open(output_path, "r", encoding="utf-8") as f:
            output_content = f.read()

        assert '"Quotes"' in output_content
        assert "@#$%^&*()" in output_content
        assert "ñ" in output_content
        assert "日本語" in output_content
