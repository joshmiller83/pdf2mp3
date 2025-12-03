"""
Shared pytest fixtures and configuration for pdf2txt tests.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock


@pytest.fixture
def temp_dir():
    """Create a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_text_content():
    """Sample text content for testing."""
    return """This is a sample document with multiple sentences.
It has line breaks and formatting issues.
Some words are hyph-
enated across lines."""


@pytest.fixture
def sample_cleaned_text():
    """Sample cleaned text content."""
    return "This is a sample document with multiple sentences. It has line breaks and formatting issues. Some words are hyphenated across lines."


@pytest.fixture
def mock_pdf_page():
    """Create a mock PDF page object."""
    page = Mock()
    page.extract_text.return_value = "Sample page text."
    return page


@pytest.fixture
def create_test_files():
    """
    Factory fixture to create multiple test files in a directory.

    Usage:
        def test_something(create_test_files, temp_dir):
            create_test_files(temp_dir, count=5, prefix="page_", extension=".txt")
    """
    def _create_files(directory: Path, count: int, prefix: str = "page_",
                     extension: str = ".txt", content: str = "test content"):
        files = []
        for i in range(1, count + 1):
            file_path = directory / f"{prefix}{i}{extension}"
            file_path.write_text(content)
            files.append(file_path)
        return files
    return _create_files


@pytest.fixture
def sample_messy_document():
    """Sample document with various formatting issues for testing."""
    return """CHAPTER ONE: INTRODUCTION

This is the intro-
duction to our document.  It has extra  spaces.
And it continues here.

Here is a list:
1. First item with details
2. Second item with more info
3. Third item

SECTION TWO

The docu-
ment continues with hyphenated words.
It has many sentences. And some continue.
But this is a new thought.

CONCLUSION

Final paragraph here."""


@pytest.fixture
def sample_pdf_text_with_issues():
    """Sample PDF extracted text with typical extraction issues."""
    return """Title of Document

This is a multi-
page document with formatting issues.    Extra spaces.

Line breaks
that should
be joined.

Table of Contents
1. Introduction........................1
2. Main Content......................5
3. Conclusion.........................20

CHAPTER 1: INTRODUCTION

The introduction text goes here-
with hyphenation issues."""
