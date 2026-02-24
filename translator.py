import re                      # 用於解析 SRT 格式（正規表示式）
import time                    # 用於 API retry 時暫停
from pathlib import Path       # 更安全的路徑處理方式
from openai import OpenAI      # OpenAI 官方 SDK

# 建立 OpenAI 客戶端（需先設定環境變數 OPENAI_API_KEY）
client = OpenAI()

# 指定使用的模型
MODEL = "gpt-4o-mini"


def translate_text(text):
    """
    將單一字幕區塊文字翻譯為繁體中文。
    若 API 失敗，最多重試 3 次。
    若仍失敗，回傳原文（確保程式永遠不會崩潰）。
    """

    # 建立翻譯 prompt
    prompt = f"""
Translate the following subtitle text into natural Traditional Chinese.
Keep technical terms in English.
Only output the translation.
Do not add explanations.

{text}
"""

    # 最多嘗試 3 次
    for attempt in range(3):
        try:
            # 呼叫 OpenAI API
            response = client.responses.create(
                model=MODEL,
                input=prompt,
            )

            # 取得模型回傳文字並去除前後空白
            output = response.output_text.strip()

            # 若模型回傳空字串，視為異常
            if not output:
                raise ValueError("Empty response")

            return output

        except Exception as e:
            # 發生錯誤時重試
            print(f"⚠ Retry {attempt+1}: {e}")
            time.sleep(1)

    # 若三次都失敗，回傳原文，避免整體翻譯中斷
    print("❌ Translation failed. Keeping original.")
    return text


def parse_srt(content):
    """
    將 SRT 檔案內容解析為結構化資料。
    回傳格式：
    [
        (index, timestamp, text),
        ...
    ]
    """

    # 依照空白行切割字幕區塊
    blocks = re.split(r"\n\s*\n", content.strip())
    parsed = []

    for block in blocks:
        lines = block.split("\n")

        # 合法 SRT 至少要 3 行
        if len(lines) >= 3:
            index = lines[0]          # 字幕編號
            timestamp = lines[1]      # 時間軸
            text = "\n".join(lines[2:])  # 字幕內容（可能多行）

            parsed.append((index, timestamp, text))

    return parsed


def process_srt(input_path: Path, output_path: Path):
    """
    處理單一 SRT 檔案：
    1. 讀取檔案
    2. 解析字幕區塊
    3. 逐區塊翻譯
    4. 重建 SRT 格式
    5. 輸出新檔案
    """

    print(f"🔄 Translating: {input_path}")

    # 讀取 SRT 檔案
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 解析字幕
    parsed = parse_srt(content)
    translated_blocks = []

    # 逐字幕區塊翻譯
    for index, timestamp, text in parsed:

        translated_text = translate_text(text)

        # 重建 SRT 格式
        translated_blocks.append(
            f"{index}\n{timestamp}\n{translated_text}"
        )

    # 若目標資料夾不存在則自動建立
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 寫入翻譯後的 SRT
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(translated_blocks))

    print(f"✅ Done: {output_path}")


def batch_translate(source_dir: Path, target_dir: Path):
    """
    批量處理整個資料夾內所有 .srt 檔案。
    會保留原本資料夾結構。
    """

    # 遞迴搜尋所有 srt 檔案
    srt_files = list(source_dir.rglob("*.srt"))

    for srt_file in srt_files:

        # 計算相對路徑（保留原資料夾結構）
        relative_path = srt_file.relative_to(source_dir)

        # 建立對應輸出路徑
        output_file = target_dir / relative_path

        # 在檔名後加上 _zh
        output_file = output_file.with_name(output_file.stem + "_zh.srt")

        try:
            process_srt(srt_file, output_file)
        except Exception as e:
            # 若單一檔案出錯，不影響其他檔案
            print(f"❌ File error: {srt_file.name} → {e}")


if __name__ == "__main__":

    # 設定主資料夾路徑
    base = Path(r"C:\Users\noth\Desktop\CRTP\Course Video Library")

    # 英文字幕來源資料夾
    source = base / "Course_output_en"

    # 中文字幕輸出資料夾
    target = base / "Course_output_zh"

    # 開始批量翻譯
    batch_translate(source, target)
