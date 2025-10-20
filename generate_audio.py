import argparse
import os
import subprocess
import sys
import contextlib
from pathlib import Path
from mlx_audio.tts.generate import generate_audio

# Realtime print flushing
sys.stdout.reconfigure(line_buffering=True)

# Suppress stdout/stderr for code blocks
@contextlib.contextmanager
def suppress_output():
    with open(os.devnull, 'w') as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield

# Suppress noisy loggers
def quiet_loggers():
    import logging
    for logger_name in [
        "transformers",
        "phonemizer",
        "huggingface_hub",
        "nltk",
        "urllib3",
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)

def run_quietly(command):
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def text_file_to_mp3(txt_path: Path, model: str, voice: str, lang_code: str, bitrate: str, speed: float) -> Path:
    prefix = str(txt_path.with_suffix(''))  # remove .txt
    wav_path = f"{prefix}.wav"
    mp3_path = f"{prefix}.mp3"

    with open(txt_path, "r", encoding="utf-8") as f:
        text = f.read()

    print(f"🎙️ {txt_path.name} → {mp3_path}")

    # Suppress internal logging/output
    quiet_loggers()
    with suppress_output():
        generate_audio(
            text=text,
            model_path=model,
            voice=voice,
            speed=speed,  # ← new variable from argument
            lang_code=lang_code,
            file_prefix=prefix,
            audio_format="wav",
            sample_rate=24000,
            join_audio=True,
            verbose=False
        )

    if os.path.exists(wav_path):
        run_quietly([
            "ffmpeg", "-y", "-i", wav_path,
            "-codec:a", "libmp3lame", "-b:a", bitrate, mp3_path
        ])
        os.remove(wav_path)
        return Path(mp3_path)
    else:
        print(f"❌ Failed to generate WAV for: {txt_path.name}")
        return None

def concat_mp3s(mp3_files: list[Path], output_file: Path):
    print(f"🔗 Merging {len(mp3_files)} files → {output_file}")
    list_file = "concat_list.txt"
    with open(list_file, "w") as f:
        for mp3 in mp3_files:
            f.write(f"file '{mp3.resolve()}'\n")

    run_quietly([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy", str(output_file)
    ])

    os.remove(list_file)
    print(f"✅ Done: {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description="Convert one or more .txt files to MP3 using mlx-audio TTS"
    )
    parser.add_argument("input_txts", nargs="+", help="Path(s) to .txt file(s) or folders containing them")
    parser.add_argument("--output", help="Final output MP3 file (e.g., all_audio.mp3)")
    parser.add_argument("--model", default="prince-canuma/Kokoro-82M", help="Model path or repo ID")
    parser.add_argument("--voice", default="af_heart", help="Voice style to use")
    parser.add_argument("--speed", type=float, default=1.0, help="Speaking speed (default: 1.0, range: 0.5 to 2.0)")
    parser.add_argument("--lang", default="a", help="Language code (default: 'a' for American English)")
    parser.add_argument("--bitrate", default="96k", help="MP3 bitrate (default: 96k)")
    parser.add_argument("--no-concat", action="store_true", help="Skip concatenating all MP3s into a single file")

    args = parser.parse_args()

    should_concat = bool(args.output) and not args.no_concat
    if not should_concat and not args.no_concat:
        print("ℹ️ No --output provided; skipping concatenation.")
        args.no_concat = True
    elif args.no_concat and args.output:
        print("ℹ️ --output is ignored when --no-concat is provided.")

    generated_mp3s = []

    def iter_txts(inputs: list[str]):
        for item in inputs:
            path = Path(item)
            if path.is_dir():
                txts = sorted(p for p in path.glob("*.txt") if p.is_file())
                if not txts:
                    print(f"⚠️ No .txt files found in directory: {path}")
                for txt in txts:
                    yield txt
            elif path.suffix.lower() == ".txt" and path.is_file():
                yield path
            else:
                print(f"⚠️ Skipping: {item}")

    for txt_path in iter_txts(args.input_txts):
        mp3_path = txt_path.with_suffix(".mp3")
        if mp3_path.exists():
            print(f"⏭️ MP3 already exists, skipping generation: {mp3_path.name}")
            generated_mp3s.append(mp3_path)
            continue

        mp3 = text_file_to_mp3(txt_path, args.model, args.voice, args.lang, args.bitrate, args.speed)
        if mp3:
            generated_mp3s.append(mp3)

    if should_concat and generated_mp3s:
        concat_mp3s(generated_mp3s, Path(args.output))
    elif args.no_concat:
        print("🛑 Concatenation skipped.")

if __name__ == "__main__":
    main()
