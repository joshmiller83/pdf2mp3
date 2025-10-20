import argparse
from pathlib import Path
import re

# Detect common list starters (numbered or bulleted)
LIST_ITEM_RE = re.compile(r'^\s*(\d+[\.\)]|[•\-])\s+')
# Detect headlines (all caps, 2+ words)
HEADLINE_RE = re.compile(r'^[A-Z0-9\s\-:,]+$')
# Continuation signal words (to avoid false paragraph breaks)
CONTINUATION_WORDS = {'And', 'But', 'So', 'Because', 'At', 'As', 'Yet', 'Though', 'While', 'When', 'If'}

def should_start_new_paragraph(prev_line: str, curr_line: str) -> bool:
    """Heuristic: should curr_line begin a new paragraph?"""
    if not prev_line:
        return True
    if LIST_ITEM_RE.match(curr_line):
        return True
    if HEADLINE_RE.match(curr_line.strip()) and len(curr_line.strip().split()) >= 2:
        return True
    if prev_line.endswith(('.', '?', '!', ':')):
        first_word = curr_line.strip().split()[0] if curr_line.strip() else ''
        if first_word and first_word not in CONTINUATION_WORDS:
            return True
    return False

def clean_text(lines: list[str]) -> list[str]:
    paragraphs = []
    buffer = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Handle hyphenated word breaks: join with no space
        if buffer.endswith('-') and line:
            buffer = buffer[:-1] + line
            i += 1
            continue

        # Blank line signals paragraph break
        if not line:
            if buffer:
                paragraphs.append(buffer.strip())
                buffer = ""
            i += 1
            continue

        # List item or new paragraph
        if buffer and should_start_new_paragraph(buffer, line):
            paragraphs.append(buffer.strip())
            buffer = line
        else:
            # Join with space if buffer isn't empty
            buffer = f"{buffer} {line}" if buffer else line

        i += 1

    if buffer:
        paragraphs.append(buffer.strip())

    return paragraphs

def write_output(original_path: Path, paragraphs: list[str]):
    output_path = original_path.with_name(original_path.stem + "_cleaned.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for para in paragraphs:
            f.write(para.strip() + "\n\n")
    print(f"✅ Cleaned version saved as: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Reformat bad line breaks and paragraphs in plain text.")
    parser.add_argument("input_file", type=str, help="Path to the original .txt file")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        return

    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    cleaned_paragraphs = clean_text(raw_lines)
    write_output(input_path, cleaned_paragraphs)

if __name__ == "__main__":
    main()
