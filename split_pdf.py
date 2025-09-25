# split_pdf.py
import os
import sys
import nltk
import re
from PyPDF2 import PdfReader

nltk.download('punkt')  # sentence tokenizer
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

def clean_pdf_text(raw_text: str) -> str:
    # Replace hyphenated line breaks (e.g. "multi-\nline") with joined word
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', raw_text)

    # Replace line breaks that are not end of sentence with space
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)

    # Collapse multiple newlines into paragraph breaks
    text = re.sub(r'\n{2,}', '\n\n', text)

    # Remove weird extra spaces
    text = re.sub(r' +', ' ', text)

    return text.strip()

def extract_sentences_from_pdf(pdf_path: str, output_dir: str):
    reader = PdfReader(pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            print(f"Page {i + 1} is empty or unreadable.")
            continue
        
        cleaned_text = clean_pdf_text(text)
        sentences = sent_tokenize(cleaned_text)
        output_path = os.path.join(output_dir, f"page_{i + 1}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            for sentence in sentences:
                f.write(sentence.strip() + "\n")
        print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python split_pdf.py <path_to_pdf> <output_dir>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    extract_sentences_from_pdf(pdf_path, output_dir)

