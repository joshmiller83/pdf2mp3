# GitHub Actions Workflows

This directory contains CI/CD workflows for the pdf2txt project.

## Workflows

### `tests.yml` - Main Testing Workflow
Runs on every push and pull request to main/master branches.

**Jobs**:
- **test**: Runs tests on Ubuntu and macOS with Python 3.10, 3.11, 3.12
- **test-coverage**: Generates coverage reports
- **lint**: Checks code quality with ruff

**Status**: 🟢 Active

### `badge.yml` - Test Status Badge
Generates a dynamic badge showing test status.

**Status**: ⚠️ Requires setup (see [CICD.md](../CICD.md))

## Quick Start

No setup required! Workflows run automatically when you:
- Push to main branch
- Create a pull request to main
- Manually trigger via Actions tab

## Local Testing

Run the same checks locally before pushing:

```bash
# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=. --cov-report=html

# Lint code
ruff check .

# Format code
ruff format --check .
```

## Viewing Results

1. Go to the **Actions** tab in GitHub
2. Click on a workflow run
3. View job details and logs
4. Download artifacts if needed

## Configuration

Workflows use:
- Python versions: 3.10, 3.11, 3.12
- Operating systems: Ubuntu Latest, macOS Latest
- Test framework: pytest
- Linter: ruff
- Coverage tool: pytest-cov

## Support

For detailed documentation, see [CICD.md](../CICD.md).

For issues, check:
- Workflow logs in Actions tab
- [TESTING.md](../../TESTING.md) for test documentation
- [TEST_FIXES.md](../../TEST_FIXES.md) for known issues
