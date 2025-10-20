# Repository Guidelines

## Project Structure & Module Organization
The repo is a small Python CLI toolkit. Core scripts live at the root: `process_pdf.py` orchestrates runs, `split_pdf.py` extracts per-page text, `generate_audio.py` handles mlx-audio TTS, and `reformat_text.py` normalizes sentence flow. Output defaults to `temp_txt/<pdf-stem>/` for intermediary text and `audio_output/` for MP3 batches. The `mlx310/` directory is a local virtual environment; do not rely on it in commits—recreate your own venv instead.

## Build, Test, and Development Commands
Create and activate a Python 3.10 environment before installing dependencies:
```bash
python3.10 -m venv mlx310
source mlx310/bin/activate
pip install -r requirements.txt
```
Run an end-to-end conversion (adjust paths as needed):
```bash
python process_pdf.py ~/Downloads/sample.pdf --group 8 --skip 2 --speed 1.5
```
Speed-check group planning without audio generation:
```bash
python process_pdf.py ~/Downloads/sample.pdf --group 6 --dry-run
```
Use the helper when you need to touch up sentence flow manually:
```bash
python reformat_text.py temp_txt/sample/page_12.txt
```

## Coding Style & Naming Conventions
Scripts target Python 3.10+ and lean on standard library modules plus `PyPDF2`, `nltk`, and `mlx-audio`. Follow PEP 8 with 4-space indents, prefer type hints for public helpers, and keep functions small and composable (see `group_text_files` and `text_file_to_mp3`). CLI options should use lowercase long flags (e.g., `--dry-run`), and filenames stay snake_case.

## Testing Guidelines
There is no automated test harness yet; rely on `--dry-run` to validate grouping logic and spot-check generated MP3s in `audio_output/`. When changing parsing heuristics, compare before/after outputs under `temp_txt/` to ensure sentence boundaries remain stable. New features should include a reproducible command sequence in the PR description so reviewers can verify behavior manually.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commits (e.g., “Skip existing mp3s”). Keep messages under ~72 characters with details in the body when needed. For PRs, describe the motivation, highlight any CLI or dependency changes, and link to tracked issues if they exist. Include sample before/after command output paths and mention any follow-up cleanup (such as rerunning `pip freeze`) so reviewers know what to expect.
