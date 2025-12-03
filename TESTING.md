# Testing Guide for pdf2txt

This document provides comprehensive information about the automated test suite for the pdf2txt project.

## Overview

The test suite provides automated testing for all core functionality:
- PDF text extraction and cleaning (`split_pdf.py`)
- Text reformatting and paragraph detection (`reformat_text.py`)
- PDF processing workflow orchestration (`process_pdf.py`)

## Quick Start

### Installation

1. Ensure you have Python 3.10+ and your virtual environment activated:
```bash
source mlx310/bin/activate  # or your venv name
```

2. Install test dependencies (pytest should already be in requirements.txt):
```bash
pip install pytest pytest-asyncio
```

### Running Tests

**Easiest method** - Use the provided test runner:
```bash
./run_tests.sh
```

**Direct pytest usage**:
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_split_pdf.py

# Run specific test class
pytest tests/test_split_pdf.py::TestCleanPdfText

# Run specific test function
pytest tests/test_split_pdf.py::TestCleanPdfText::test_clean_hyphenated_line_breaks
```

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Shared pytest fixtures
├── test_split_pdf.py        # Tests for PDF splitting and text extraction
├── test_reformat_text.py    # Tests for text reformatting
├── test_process_pdf.py      # Tests for PDF processing workflow
└── README.md               # Test documentation

pytest.ini                   # Pytest configuration
run_tests.sh                 # Convenient test runner script
TESTING.md                   # This file
```

## Test Coverage by Module

### split_pdf.py (test_split_pdf.py)

**Functions Tested:**
- `clean_pdf_text()` - Text cleaning and normalization
  - Hyphenated line break removal
  - Space normalization
  - Paragraph break preservation
  - Whitespace trimming

- `extract_sentences_from_pdf()` - PDF extraction
  - Multi-page PDF handling
  - Empty page handling
  - Sentence tokenization
  - UTF-8 encoding
  - File creation and naming

**Test Classes:**
- `TestCleanPdfText` - 8 unit tests for text cleaning
- `TestExtractSentencesFromPdf` - 10 tests for PDF extraction
- `TestIntegration` - Full workflow test

**Total Tests:** 19

### reformat_text.py (test_reformat_text.py)

**Functions Tested:**
- `should_start_new_paragraph()` - Paragraph detection logic
  - List item detection
  - Headline detection
  - Sentence boundary detection
  - Continuation word handling

- `clean_text()` - Text reformatting
  - Hyphenation handling
  - Paragraph reconstruction
  - List formatting
  - Headline separation

- `write_output()` - File writing
  - File naming
  - UTF-8 encoding
  - Paragraph formatting

**Test Classes:**
- `TestRegexPatterns` - 8 tests for regex matching
- `TestShouldStartNewParagraph` - 11 tests for paragraph logic
- `TestCleanText` - 13 tests for text cleaning
- `TestWriteOutput` - 5 tests for file writing
- `TestIntegration` - 2 full workflow tests

**Total Tests:** 39

### process_pdf.py (test_process_pdf.py)

**Functions Tested:**
- `page_num()` - Page number extraction
  - Single/multi-digit numbers
  - Path handling
  - Error cases

- `group_text_files()` - File grouping
  - Group size handling
  - Numeric sorting
  - File skipping
  - Padding calculation

- `run_split_pdf()` - Subprocess execution
- `run_generate_audio()` - Audio generation orchestration

**Test Classes:**
- `TestPageNum` - 7 tests for page number extraction
- `TestGroupTextFiles` - 13 tests for file grouping
- `TestRunSplitPdf` - 3 tests for PDF splitting
- `TestRunGenerateAudio` - 4 tests for audio generation
- `TestIntegration` - 5 workflow tests
- `TestEdgeCases` - 4 edge case tests

**Total Tests:** 36

### Total Test Count: 94 tests

## Shared Fixtures (conftest.py)

Available fixtures for all tests:

| Fixture | Description | Usage |
|---------|-------------|-------|
| `temp_dir` | Temporary directory (auto-cleanup) | File operations |
| `sample_text_content` | Sample text with formatting issues | Text processing tests |
| `sample_cleaned_text` | Expected cleaned output | Verification |
| `mock_pdf_page` | Mock PDF page object | PDF extraction mocking |
| `create_test_files` | Factory for creating test files | Batch file creation |
| `sample_messy_document` | Complex formatted document | Integration tests |
| `sample_pdf_text_with_issues` | PDF text with extraction issues | PDF parsing tests |

## Test Configuration (pytest.ini)

The `pytest.ini` file configures:
- Test discovery patterns
- Output formatting (verbose, colored)
- Test markers
- Ignored directories
- Warning filters

### Available Test Markers

You can mark tests with these markers and run them selectively:

```python
@pytest.mark.unit          # Unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.slow          # Slow-running tests
@pytest.mark.requires_pdf  # Requires PDF files
@pytest.mark.requires_audio # Requires audio generation
```

Run tests by marker:
```bash
pytest -m unit                    # Only unit tests
pytest -m integration             # Only integration tests
pytest -m "not slow"              # Skip slow tests
```

## Writing New Tests

### Test Template

```python
import pytest
from module_name import function_to_test

class TestFunctionName:
    """Test suite for function_name"""

    def test_expected_behavior(self):
        """Test that function works correctly in normal case"""
        # Arrange
        input_data = "test input"
        expected_output = "expected result"

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result == expected_output

    def test_error_handling(self):
        """Test that function handles errors correctly"""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)

    @pytest.fixture
    def sample_data(self):
        """Fixture for test data"""
        return {"key": "value"}

    def test_with_fixture(self, sample_data):
        """Test using fixture"""
        result = function_to_test(sample_data)
        assert result is not None
```

### Using Mocks

```python
from unittest.mock import Mock, patch, MagicMock

@patch('module_name.external_dependency')
def test_with_mock(mock_dependency):
    """Test with mocked external dependency"""
    # Configure mock
    mock_dependency.return_value = "mocked result"

    # Run test
    result = function_that_uses_dependency()

    # Verify
    assert result == "expected"
    mock_dependency.assert_called_once()
```

### Best Practices

1. **Naming**: Test names should describe what they test
   - Good: `test_clean_hyphenated_line_breaks`
   - Bad: `test_clean1`

2. **Structure**: Use Arrange-Act-Assert pattern
   ```python
   def test_something(self):
       # Arrange: Set up test data
       input_data = create_test_data()

       # Act: Execute the function
       result = function_under_test(input_data)

       # Assert: Verify the result
       assert result == expected_value
   ```

3. **Isolation**: Each test should be independent
   - Use fixtures for shared setup
   - Don't rely on test execution order
   - Clean up resources (fixtures do this automatically)

4. **Coverage**: Test both success and failure cases
   - Normal operation
   - Edge cases
   - Error conditions
   - Boundary values

5. **Documentation**: Add clear docstrings
   ```python
   def test_function_with_empty_input(self):
       """Test that function handles empty input correctly"""
   ```

## Continuous Integration

These tests are designed for CI/CD environments:

- **Fast execution**: Most tests run in milliseconds
- **No external dependencies**: PDFs and audio are mocked
- **Deterministic**: Same input always produces same output
- **Clear output**: Verbose mode shows exactly what failed
- **Exit codes**: Proper exit codes for CI systems

### Example CI Configuration

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: ./run_tests.sh -v
```

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'split_pdf'`

**Solution**: Tests add parent directory to Python path automatically, but ensure you're running from project root:
```bash
cd /path/to/pdf2txt
pytest
```

### Pytest Not Found

**Problem**: `command not found: pytest`

**Solution**:
```bash
# Activate virtual environment
source mlx310/bin/activate  # or your venv name

# Install pytest
pip install pytest pytest-asyncio
```

### NLTK Data Errors

**Problem**: NLTK tokenizers not found

**Solution**: Tests mock NLTK functions, so this shouldn't occur. If needed:
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### Permission Errors

**Problem**: Can't write to temp directories

**Solution**: Tests use Python's `tempfile` which should have proper permissions. Check:
```bash
# Verify TMPDIR is writable
echo $TMPDIR
ls -ld $TMPDIR
```

### Test Failures

If tests fail:

1. **Read the error message carefully**: Pytest provides detailed output
2. **Run individual test**: Isolate the failing test
   ```bash
   pytest tests/test_split_pdf.py::TestCleanPdfText::test_clean_hyphenated_line_breaks -vv
   ```
3. **Check the traceback**: Use `-vv` for full tracebacks
4. **Verify environment**: Ensure clean virtual environment

## Coverage Reports

To generate coverage reports:

1. Install coverage tool:
```bash
pip install pytest-cov
```

2. Run tests with coverage:
```bash
pytest --cov=. --cov-report=html --cov-report=term
```

3. View HTML report:
```bash
open htmlcov/index.html
```

The report shows:
- Which lines are covered by tests
- Which branches are tested
- Overall coverage percentage
- Files that need more tests

## Performance

Test execution times (approximate):
- `test_split_pdf.py`: ~0.5 seconds (19 tests)
- `test_reformat_text.py`: ~0.8 seconds (39 tests)
- `test_process_pdf.py`: ~0.6 seconds (36 tests)
- **Total**: ~2 seconds for all 94 tests

Fast execution is achieved through:
- Mocking external dependencies (PDFs, audio)
- Using in-memory operations where possible
- Efficient fixtures
- No network calls

## Maintenance

### When to Update Tests

Update tests when:
- Adding new features
- Fixing bugs (add regression test)
- Changing function signatures
- Refactoring code

### When to Add Tests

Add tests for:
- New functions or classes
- Bug fixes (prevent regression)
- Edge cases discovered
- User-reported issues

### Keeping Tests Clean

Regularly:
- Remove obsolete tests
- Refactor duplicated test code into fixtures
- Update docstrings
- Review test coverage
- Update this documentation

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)

## Support

If you encounter issues with the test suite:
1. Check this documentation
2. Review test output carefully
3. Run with `-vv` for detailed information
4. Check that dependencies are installed
5. Verify virtual environment is activated

## Contributing

When contributing tests:
1. Follow existing patterns
2. Add docstrings to all tests
3. Use appropriate fixtures
4. Test both success and failure cases
5. Keep tests fast and isolated
6. Update documentation
