# process_pdf.py
import argparse
import subprocess
import sys
import re
from pathlib import Path

import argparse
import subprocess
import sys
import re
from pathlib import Path

def run_split_pdf(pdf_path: Path, output_dir: Path, ocr: bool = False, 
                  columns: int = 1, header_h: int = 0, footer_h: int = 0, 
                  ocr_dry_run: bool = False, start_page: int = 0,
                  auto_layout: bool = False, model_name: str = "publaynet"):
    print(f"📄 Splitting PDF: {pdf_path.name}")
    cmd = [sys.executable, "split_pdf.py", str(pdf_path), str(output_dir)]
    
    if ocr:
        cmd.append("--ocr")
        cmd.extend(["--columns", str(columns)])
        cmd.extend(["--header-height", str(header_h)])
        cmd.extend(["--footer-height", str(footer_h)])
        if ocr_dry_run:
            cmd.append("--dry-run")
        if start_page > 0:
            cmd.extend(["--start-page", str(start_page)])
        if auto_layout:
            cmd.append("--auto-layout")
            cmd.extend(["--model", model_name])
            
    subprocess.run(cmd, check=True)

def page_num(p: Path) -> int:
    m = re.search(r'(\d+)(?=\.txt$)', p.name)
    return int(m.group(1)) if m else -1

def group_text_files(text_dir: Path, group_size: int, skip: int):
    all_txts = sorted(text_dir.glob("*.txt"), key=page_num)  # numeric sort
    if not all_txts:
        return [], 0
    # determine padding width from highest page number present
    pad_width = len(str(page_num(all_txts[-1])))

    # skip first N after numeric sort
    if skip > 0:
        all_txts = all_txts[skip:]

    # chunk into fixed-size groups
    groups = [all_txts[i:i + group_size] for i in range(0, len(all_txts), group_size)]
    # drop any empty chunk (defensive)
    groups = [g for g in groups if g]
    return groups, pad_width

def run_generate_audio(txt_group, output_path: Path, speed: float):
    cmd = [sys.executable, "generate_audio.py", *[str(p) for p in txt_group], "--output", str(output_path),"--speed",str(speed)]
    subprocess.run(cmd, check=True)

def main():
    parser = argparse.ArgumentParser(description="Wrapper: split_pdf -> group pages -> generate concatenated MP3s")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--group", type=int, default=3, help="Pages per MP3 (fixed-size groups). Default: 3")
    parser.add_argument("--skip", type=int, default=0, help="Skip first N pages (after numeric sort). Default: 0")
    parser.add_argument("--speed", type=float, default=1.0, help="Speaking speed (default: 1.0, range: 0.5 to 2.0)")
    parser.add_argument("--tempdir", default="temp_txt", help="Where to store extracted .txt files")
    parser.add_argument("--outdir", default="audio_output", help="Where to store generated MP3s")
    parser.add_argument("--dry-run", action="store_true", help="Preview groups and exit (no audio generation)")
    
    # OCR Options
    parser.add_argument("--ocr", action="store_true", help="Enable OCR (pypdfium2 + tesseract)")
    parser.add_argument("--columns", type=int, default=1, help="Number of columns to split page into (OCR only). Default: 1")
    parser.add_argument("--header-height", type=int, default=0, help="Pixels to crop from top (OCR only). Default: 0")
    parser.add_argument("--footer-height", type=int, default=0, help="Pixels to crop from bottom (OCR only). Default: 0")
    parser.add_argument("--ocr-dry-run", action="store_true", help="OCR Dry run: save preview images of first 5 pages and exit")
    parser.add_argument("--auto-layout", action="store_true", help="Use Deep Learning to detect layout (auto columns/header/footer)")
    parser.add_argument("--model", default="publaynet", choices=["publaynet", "prima"], help="Layout model: 'publaynet' (academic/scientific) or 'prima' (magazines/reports). Default: publaynet")

    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser()
    temp_dir = (Path(args.tempdir) / pdf_path.stem).expanduser()
    out_dir = Path(args.outdir).expanduser()
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Split PDF into per-page .txt using your existing script
    # Use skip as start_page ONLY for dry-run to avoid double-skipping in full run
    start_page = args.skip if args.ocr_dry_run else 0
    
    run_split_pdf(
        pdf_path, 
        temp_dir, 
        ocr=args.ocr, 
        columns=args.columns, 
        header_h=args.header_height, 
        footer_h=args.footer_height,
        ocr_dry_run=args.ocr_dry_run,
        start_page=start_page,
        auto_layout=args.auto_layout,
        model_name=args.model
    )

    if args.ocr_dry_run:
        print(f"\n✅ OCR Dry Run complete. Preview images saved in: {temp_dir}/ocr_preview")
        return

    # 2) Build fixed-size groups with numeric sort + skip
    groups, pad = group_text_files(temp_dir, args.group, args.skip)

    if not groups:
        print("⚠️ No .txt files found to process. Exiting.")
        return

    if not 0.5 <= args.speed <= 2.0:
        parser.error("Speed must be between 0.5 and 2.0")
        return

    # 3) Preview or generate
    if args.dry_run:
        print("\n🔎 Dry run: planned MP3 outputs")
        for g in groups:
            first = str(page_num(g[0])).zfill(pad)
            last  = str(page_num(g[-1])).zfill(pad)
            print(f"  {out_dir / f'pages_{first}-{last}.mp3'}  ←  {[p.name for p in g]}")
        return

    for g in groups:
        first = str(page_num(g[0])).zfill(pad)
        last  = str(page_num(g[-1])).zfill(pad)
        out_file = out_dir / f"pages_{first}-{last}.mp3"
        print(f"🎙️ Generating: {out_file.name}")
        run_generate_audio(g, out_file, args.speed)

    print(f"\n✅ All done! MP3s are in: {out_dir}")

if __name__ == "__main__":
    main()
