# 🗣️ `pdf2mp3` — PDF to Natural Speech MP3s

A CLI-based toolchain for converting multipage PDFs (like AWS whitepapers or reports) into clean, page-grouped MP3 audio files using `mlx-audio`.

This tool:

* Splits a PDF into one `.txt` file per page
* Tokenizes each page into sentences (for natural speech pauses)
* Groups `.txt` files into batches of N pages
* Uses `mlx-audio` to generate a high-quality `.mp3` for each group
* Supports speed tuning, skipping TOC pages, and clean folder output

## 📦 Requirements

* Python 3.10+ (preferably managed with `pyenv`)
* `ffmpeg` (for `.wav` → `.mp3` conversion)
* `mlx-audio` installed and functional

## 🛠️ Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/YOUR-USERNAME/pdf2txt.git
cd pdf2txt
```

### 2. Create your virtual environment

We recommend naming it `mlx310` or similar to reflect your `mlx-audio` setup:

```bash
python3.10 -m venv mlx310
source mlx310/bin/activate
```

> 🧠 Tip: Use `pyenv` to install 3.10.13 if you don't already have it.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If you don’t have a `requirements.txt`, here's the minimum set:

```bash
pip install nltk PyPDF2 mlx-audio
```

And download the required NLTK tokenizers (only once):

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab')"
```

### 4. Ensure `ffmpeg` is available

Install via Homebrew on macOS:

```bash
brew install ffmpeg
```

Or Ubuntu/Debian:

```bash
sudo apt install ffmpeg
```

## 🚀 How to Use

### 🔄 Convert a PDF to MP3 audio files

This command does everything:

```bash
python process_pdf.py ~/Downloads/wellarchitected-security-pillar.pdf \
  --outdir ~/Downloads/security-pillar/ \
  --group 8 \
  --skip 6 \
  --speed 1.75
```

#### What it does:

| Step        | Behavior                                                                 |
| ----------- | ------------------------------------------------------------------------ |
| `split_pdf` | Splits the PDF into one `.txt` file per page, with one sentence per line |
| `--skip 6`  | Skips the first 6 pages (e.g. table of contents)                         |
| `--group 8` | Groups 8 pages at a time into one `.mp3` (e.g. `pages_007-014.mp3`)      |
| `--speed`   | Speaks at 1.75x speed (range: 0.5 to 2.0)                                |
| `--outdir`  | Saves the generated audio files into a clean output folder               |

## 🧪 Preview Mode

To preview which pages will be grouped without generating audio:

```bash
python process_pdf.py your.pdf --group 8 --skip 6 --dry-run
```

## 🗃️ Folder Structure

Example output:

```
temp_txt/
  wellarchitected-security-pillar/
    page_1.txt
    page_2.txt
    ...
audio_output/
  pages_007-014.mp3
  pages_015-022.mp3
  ...
```

## 🧩 Components

| Script              | Purpose                                         |
| ------------------- | ----------------------------------------------- |
| `split_pdf.py`      | Extracts and splits PDF text by page            |
| `generate_audio.py` | Converts groups of `.txt` files into one `.mp3` |
| `process_pdf.py`    | Orchestrates everything: PDF → grouped MP3s     |

## 🛠️ Tips & Troubleshooting

* Ensure you're always running within your `venv`:

  ```bash
  source mlx310/bin/activate
  ```
* If `generate_audio.py` fails, make sure `mlx-audio` supports your model/voice combo
* Want slower narration? Try `--speed 0.9`

## 🙌 Credits & Acknowledgments

* [`mlx-audio`](https://github.com/Blaizzy/mlx-audio) for the text-to-speech magic
* NLTK for sentence tokenization
* ChatGPT for helping write these tools and documentation.