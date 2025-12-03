# Test Suite for pdf2txt

This directory contains automated tests for the pdf2txt project.

## Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Shared fixtures and configuration
├── test_split_pdf.py     # Tests for split_pdf.py
├── test_reformat_text.py # Tests for reformat_text.py
├── test_process_pdf.py   # Tests for process_pdf.py
└── README.md            # This file
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run tests for a specific module
```bash
pytest tests/test_split_pdf.py
pytest tests/test_reformat_text.py
pytest tests/test_process_pdf.py
```

### Run tests with verbose output
```bash
pytest -v
```

### Run tests with coverage report
```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

### Run specific test classes or functions
```bash
# Run a specific test class
pytest tests/test_split_pdf.py::TestCleanPdfText

# Run a specific test function
pytest tests/test_split_pdf.py::TestCleanPdfText::test_clean_hyphenated_line_breaks
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

## Test Categories

### Unit Tests
- Test individual functions in isolation
- Use mocks for external dependencies
- Fast execution
- Located in: All test files

### Integration Tests
- Test complete workflows
- Test interaction between components
- May create temporary files
- Located in: `TestIntegration` classes

## Test Coverage

The test suite covers:

### split_pdf.py
- `clean_pdf_text()` - Text cleaning and normalization
- `extract_sentences_from_pdf()` - PDF extraction and sentence tokenization
- File I/O operations
- Error handling for empty/missing pages
- UTF-8 encoding support

### reformat_text.py
- `should_start_new_paragraph()` - Paragraph detection logic
- `clean_text()` - Text reformatting and cleaning
- `write_output()` - File writing operations
- Regex patterns (LIST_ITEM_RE, HEADLINE_RE)
- Hyphenation handling
- List and headline detection

### process_pdf.py
- `page_num()` - Page number extraction
- `group_text_files()` - File grouping logic
- `run_split_pdf()` - Subprocess execution
- `run_generate_audio()` - Audio generation orchestration
- Numeric sorting
- File skipping logic
- Padding calculation

## Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_dir` - Temporary directory for file operations
- `sample_text_content` - Sample text with formatting issues
- `sample_cleaned_text` - Expected cleaned text output
- `mock_pdf_page` - Mock PDF page object
- `create_test_files` - Factory for creating test files
- `sample_messy_document` - Complex document for testing
- `sample_pdf_text_with_issues` - PDF text with extraction issues

## Writing New Tests

### Test Organization
```python
class TestFunctionName:
    """Test suite for function_name"""

    def test_specific_behavior(self):
        """Test that specific behavior works correctly"""
        # Arrange
        input_data = "test"

        # Act
        result = function_name(input_data)

        # Assert
        assert result == expected_output
```

### Using Fixtures
```python
def test_with_fixture(temp_dir, sample_text_content):
    """Test using shared fixtures"""
    file_path = temp_dir / "test.txt"
    file_path.write_text(sample_text_content)
    # ... test code ...
```

### Mocking External Dependencies
```python
from unittest.mock import Mock, patch

@patch('module_name.external_function')
def test_with_mock(mock_external):
    """Test with mocked external dependency"""
    mock_external.return_value = "mocked result"
    # ... test code ...
```

## Dependencies

Tests require:
- `pytest` (installed via requirements.txt)
- Standard library modules: `unittest.mock`, `tempfile`, `pathlib`

Optional:
- `pytest-cov` for coverage reports
- `pytest-xdist` for parallel test execution

## Notes

- Tests use temporary directories that are automatically cleaned up
- PDF and audio dependencies are mocked to avoid requiring actual files
- Tests are designed to run quickly without external dependencies
- All file operations use UTF-8 encoding
- Tests verify both success cases and error handling

## Continuous Integration

These tests are designed to run in CI/CD environments:
- No external file dependencies
- Fast execution
- Clear error messages
- Deterministic results

## Troubleshooting

### Import Errors
If you see import errors, ensure you're running tests from the project root:
```bash
cd /path/to/pdf2txt
pytest
```

### NLTK Data
Some tests mock NLTK functions. If you need actual NLTK functionality:
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### Path Issues
Tests use absolute paths via `Path` objects. If you encounter path issues:
- Ensure temporary directories are writable
- Check file permissions
- Verify the working directory

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage above 80%
4. Add appropriate test markers
5. Update this README if needed
