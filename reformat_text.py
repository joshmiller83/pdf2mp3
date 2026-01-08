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

def strip_formatting(text: str) -> str:
    """
    Removes HTML tags and Markdown formatting (bold, italic, inline code).
    """
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Remove bold (**text** or __text__)
    text = re.sub(r'(\*\*|__)(.*?)\1', r'\2', text)
    # Remove italic (*text* or _text_)
    text = re.sub(r'(\*|_)(.*?)\1', r'\2', text)
    # Remove inline code (`text`)
    text = re.sub(r'`(.*?)`', r'\1', text)
    return text

def preprocess_markdown(lines: list[str]) -> list[str]:
    """
    Removes YAML frontmatter and transforms Markdown headers.
    """
    # 1. Remove YAML frontmatter if present
    # Check if first line is '---'
    if lines and lines[0].strip() == '---':
        # Find the next '---'
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].strip() == '---':
                end_idx = i
                break
        
        if end_idx != -1:
            # Remove everything from 0 to end_idx (inclusive)
            lines = lines[end_idx + 1:]

    # 2. Replace headers and strip formatting
    # #### -> Header level 4:
    # ###  -> Header Level 3:
    # ##   -> Header Level 2:
    # #    -> Header Level 1:
    
    processed_lines = []
    for line in lines:
        # Transform headers first
        if line.startswith('#### '):
            line = "Header level 4: " + line[5:]
        elif line.startswith('### '):
            line = "Header Level 3: " + line[4:]
        elif line.startswith('## '):
            line = "Header Level 2: " + line[3:]
        elif line.startswith('# '):
            line = "Header Level 1: " + line[2:]
        
        # Strip formatting from the line
        line = strip_formatting(line)
        processed_lines.append(line)
            
    return processed_lines

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
    clean_dir = original_path.parent / "clean"
    clean_dir.mkdir(exist_ok=True)
    
    output_path = clean_dir / (original_path.stem + ".txt")
    with open(output_path, "w", encoding="utf-8") as f:
        for para in paragraphs:
            f.write(para.strip() + "\n\n")
    print(f"✅ Cleaned version saved as: {output_path}")

def reformat_file(input_path: Path):
    """Processes a single .txt or .md file."""
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()

    # Preprocess if markdown
    if input_path.suffix.lower() == '.md':
        print(f"ℹ️ Processing Markdown file: {input_path}")
        raw_lines = preprocess_markdown(raw_lines)
    else:
        print(f"ℹ️ Processing Text file: {input_path}")

    cleaned_paragraphs = clean_text(raw_lines)
    write_output(input_path, cleaned_paragraphs)

def main():
    parser = argparse.ArgumentParser(description="Reformat bad line breaks and paragraphs in plain text.")
    parser.add_argument("input_path", type=str, help="Path to the original .txt or .md file, or a directory containing them")
    args = parser.parse_args()

    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"❌ Path not found: {input_path}")
        return

    if input_path.is_dir():
        print(f"📁 Processing directory: {input_path}")
        # Find all .txt and .md files in the directory
        txt_files = list(input_path.glob("*.txt"))
        md_files = list(input_path.glob("*.md"))
        files_to_process = sorted(txt_files + md_files)
        
        if not files_to_process:
            print(f"⚠️ No .txt or .md files found in {input_path}")
            return
        
        for file_path in files_to_process:
            reformat_file(file_path)
    else:
        reformat_file(input_path)

if __name__ == "__main__":
    main()
