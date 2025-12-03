# CI/CD Documentation

This document explains the continuous integration and deployment setup for the pdf2txt project.

## Overview

The project uses GitHub Actions to automatically run tests, check code quality, and generate coverage reports on every push and pull request to the main branch.

## Workflows

### 1. Tests Workflow (`.github/workflows/tests.yml`)

The main testing workflow runs on every push and pull request.

#### Matrix Testing

Tests run on multiple configurations:
- **Operating Systems**: Ubuntu Latest, macOS Latest
- **Python Versions**: 3.10, 3.11, 3.12

This ensures compatibility across different platforms and Python versions.

#### Jobs

**`test` Job**
- Runs the full test suite on all matrix combinations
- Installs only core dependencies (pytest, nltk, PyPDF2)
- Uses pip caching to speed up builds
- Uploads test results as artifacts (retained for 7 days)

**`test-coverage` Job**
- Runs on Ubuntu with Python 3.10
- Generates coverage reports in multiple formats (XML, HTML, terminal)
- Uploads coverage reports as artifacts (retained for 30 days)
- Displays coverage summary in GitHub Actions summary

**`lint` Job**
- Runs ruff linter to check code quality
- Runs ruff formatter to check code formatting
- Continues on error (warnings only)
- Uses GitHub format for inline annotations

#### Triggers

```yaml
on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]
  workflow_dispatch:  # Manual trigger
```

### 2. Badge Workflow (`.github/workflows/badge.yml`)

Generates a dynamic badge showing test status.

#### Setup Required

To enable the badge, you need to:

1. **Create a GitHub Gist**:
   - Go to https://gist.github.com
   - Create a new gist named `pdf2txt-tests.json`
   - Note the Gist ID (from the URL)

2. **Create a Personal Access Token**:
   - Go to GitHub Settings → Developer Settings → Personal Access Tokens
   - Create token with `gist` scope
   - Save the token securely

3. **Add Secrets to Repository**:
   - Go to Repository Settings → Secrets and Variables → Actions
   - Add `GIST_SECRET` with your personal access token
   - Add `BADGE_GIST_ID` with your gist ID

4. **Add Badge to README**:
   ```markdown
   ![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/pdf2txt-tests.json)
   ```

## Artifacts

### Test Results
- **Location**: Available in GitHub Actions run summary
- **Retention**: 7 days
- **Contents**: pytest cache and any generated test files

### Coverage Reports
- **Location**: Available in GitHub Actions run summary
- **Retention**: 30 days
- **Contents**:
  - `coverage.xml` - Machine-readable coverage data
  - `htmlcov/` - Interactive HTML coverage report

To download and view coverage:
```bash
# Download artifact from GitHub Actions
unzip coverage-report.zip
open htmlcov/index.html
```

## Local Testing Before Push

To ensure your changes pass CI before pushing:

```bash
# Activate virtual environment
source mlx310/bin/activate

# Run tests exactly as CI does
pytest tests/ -v --tb=short

# Check coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run linter
ruff check .

# Check formatting
ruff format --check .
```

## Status Checks

GitHub can be configured to require status checks before merging:

1. Go to Repository Settings → Branches
2. Add branch protection rule for `main`
3. Enable "Require status checks to pass before merging"
4. Select:
   - `test (ubuntu-latest, 3.10)`
   - `test (macos-latest, 3.10)`
   - `test-coverage`
   - `lint`

This ensures all tests pass before code can be merged.

## Viewing Results

### In Pull Requests
- Test results appear as status checks at the bottom
- Click "Details" to see full test output
- Failed tests show which specific tests failed

### In Actions Tab
- View all workflow runs
- Download artifacts
- See detailed logs
- View coverage summaries

### In Commit History
- Green checkmark ✅ = All tests passed
- Red X ❌ = Some tests failed
- Yellow circle 🟡 = Tests running

## Troubleshooting

### Tests Pass Locally but Fail in CI

**Cause**: Environment differences between local and CI

**Solutions**:
1. Check Python version: CI uses 3.10, 3.11, 3.12
2. Check dependencies: CI installs from scratch
3. Check file paths: CI uses Linux paths on Ubuntu
4. Run in clean environment locally:
   ```bash
   deactivate
   rm -rf venv
   python3.10 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pytest
   ```

### Slow CI Runs

**Causes**:
- No pip cache
- Installing large dependencies
- Running on multiple matrix configurations

**Solutions**:
1. Pip cache is enabled by default in the workflow
2. Optimize `requirements.txt` (only include needed packages)
3. Consider reducing matrix size for faster feedback

### Failed Linting Checks

The lint job uses `continue-on-error: true`, so it won't block merges. However, you should fix linting issues:

```bash
# Auto-fix many issues
ruff check --fix .

# Format code
ruff format .
```

## Adding New Tests

When you add new tests:

1. **Write the test** in appropriate file under `tests/`
2. **Run locally** to ensure it passes
3. **Push to branch** - CI runs automatically
4. **Check CI results** in pull request
5. **Merge** when all checks pass

The CI will automatically:
- Run your new tests on all platforms
- Include them in coverage reports
- Fail the build if they fail

## Notifications

Configure notifications for CI failures:

1. Go to GitHub Settings → Notifications
2. Enable "Actions" notifications
3. Choose email or web notifications
4. Get alerted when builds fail

## Best Practices

1. **Run tests locally first** before pushing
2. **Keep tests fast** - CI runs on every push
3. **Write meaningful test names** - easier to debug CI failures
4. **Check coverage** - aim for >80% coverage
5. **Fix failures quickly** - don't let main branch break
6. **Review CI logs** when tests fail in CI but pass locally

## Security

### Secrets Management
- Never commit secrets to the repository
- Use GitHub Secrets for sensitive data
- Secrets are not exposed in logs
- Secrets are not accessible in pull requests from forks

### Dependency Security
- Dependabot is recommended for security updates
- Add `.github/dependabot.yml` to enable:
  ```yaml
  version: 2
  updates:
    - package-ecosystem: "pip"
      directory: "/"
      schedule:
        interval: "weekly"
  ```

## Advanced Configuration

### Adding More Jobs

To add a new job to the workflow:

```yaml
new-job:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - name: Run new checks
      run: |
        # Your commands here
```

### Conditional Execution

Run jobs only on certain conditions:

```yaml
deploy:
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  runs-on: ubuntu-latest
  steps:
    - name: Deploy
      run: echo "Deploying..."
```

### Secrets in Workflows

Access secrets in workflows:

```yaml
- name: Use secret
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: |
    # Secret is available in $API_KEY
```

## Monitoring

### Check CI Health
- Regularly review Actions tab
- Monitor test execution times
- Check for flaky tests
- Review coverage trends

### Metrics to Track
- Test pass rate
- Average CI duration
- Test coverage percentage
- Number of flaky tests

## Support

For issues with CI/CD:
1. Check workflow logs in Actions tab
2. Review this documentation
3. Open an issue in the repository
4. Check GitHub Actions status page

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
