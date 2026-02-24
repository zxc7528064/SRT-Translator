import re
import time
from pathlib import Path
from openai import OpenAI

client = OpenAI()

MODEL = "gpt-4o-mini"


def translate_text(text):
    prompt = f"""
Translate the following subtitle text into natural Traditional Chinese.
Keep technical terms in English.
Only output the translation.
Do not add explanations.

{text}
"""

    for attempt in range(3):
        try:
            response = client.responses.create(
                model=MODEL,
                input=prompt,
            )

            output = response.output_text.strip()

            if not output:
                raise ValueError("Empty response")

            return output

        except Exception as e:
            print(f"⚠ Retry {attempt+1}: {e}")
            time.sleep(1)

    print("❌ Translation failed. Keeping original.")
    return text  # 永遠不炸


def parse_srt(content):
    blocks = re.split(r"\n\s*\n", content.strip())
    parsed = []

    for block in blocks:
        lines = block.split("\n")
        if len(lines) >= 3:
            index = lines[0]
            timestamp = lines[1]
            text = "\n".join(lines[2:])
            parsed.append((index, timestamp, text))

    return parsed


def process_srt(input_path: Path, output_path: Path):
    print(f"🔄 Translating: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    parsed = parse_srt(content)
    translated_blocks = []

    for index, timestamp, text in parsed:
        translated_text = translate_text(text)

        translated_blocks.append(
            f"{index}\n{timestamp}\n{translated_text}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(translated_blocks))

    print(f"✅ Done: {output_path}")


def batch_translate(source_dir: Path, target_dir: Path):
    srt_files = list(source_dir.rglob("*.srt"))

    for srt_file in srt_files:
        relative_path = srt_file.relative_to(source_dir)
        output_file = target_dir / relative_path
        output_file = output_file.with_name(output_file.stem + "_zh.srt")

        try:
            process_srt(srt_file, output_file)
        except Exception as e:
            print(f"❌ File error: {srt_file.name} → {e}")


if __name__ == "__main__":

    base = Path(r"C:\Users\noth\Desktop\CRTP\Course Video Library")

    source = base / "Course_output_en"
    target = base / "Course_output_zh"

    batch_translate(source, target)