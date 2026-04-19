"""
SRT 字幕翻译器 — 命令行入口
用法:
    python main.py <srt文件或文件夹路径> [--bilingual]
"""
import sys
from pathlib import Path

from config import Config
from translator import DeepSeekTranslator
from subtitle_handler import SubtitleHandler
from utils import chunk_list, get_output_path


def process_single_file(file_path: str, bilingual: bool = False):
    print(f"\n>>> 处理文件: {file_path}")

    handler = SubtitleHandler()
    subs = handler.load(file_path)
    texts = handler.extract_texts(subs)
    total = len(texts)

    if total == 0:
        print("  警告: 文件中没有字幕，跳过")
        return

    print(f"  共 {total} 条字幕")

    translator = DeepSeekTranslator()
    translations = []

    total_batches = (total + Config.BATCH_SIZE - 1) // Config.BATCH_SIZE

    for i, batch in enumerate(chunk_list(texts, Config.BATCH_SIZE), 1):
        print(f"  [{i}/{total_batches}] 翻译中 ({len(batch)} 条)...")
        batch_trans = translator.translate_batch(batch)
        translations.extend(batch_trans)

    print(f"  正在写入译文...")
    handler.apply_translations(subs, translations, bilingual=bilingual)

    output_path = get_output_path(file_path, "_zh")
    handler.save(subs, output_path)
    print(f"  完成! -> {output_path}")


def main():
    print("=" * 50)
    print("SRT 字幕翻译器 (DeepSeek)")
    print("=" * 50)

    if not Config.DEEPSEEK_API_KEY:
        print("错误: 未设置 DEEPSEEK_API_KEY")
        print("请复制 .env.example 为 .env 并填入你的 API Key")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("\n用法:")
        print("  python main.py <srt文件>           # 翻译为中文")
        print("  python main.py <srt文件> --bilingual  # 保留原文+中文双语")
        print("  python main.py <文件夹>           # 翻译文件夹内所有 srt")
        sys.exit(1)

    input_path = sys.argv[1]
    bilingual = "--bilingual" in sys.argv

    if bilingual:
        print("模式: 双语 (原文 + 中文)")

    path_obj = Path(input_path)

    if not path_obj.exists():
        print(f"错误: 路径不存在 '{input_path}'")
        sys.exit(1)

    if path_obj.is_file() and path_obj.suffix.lower() == ".srt":
        process_single_file(str(path_obj), bilingual)
    elif path_obj.is_dir():
        srt_files = [f for f in path_obj.glob("*.srt") if "_zh" not in f.stem]
        if not srt_files:
            print(f"文件夹中未找到未翻译的 srt 文件: {input_path}")
            return
        print(f"找到 {len(srt_files)} 个 srt 文件（已过滤已翻译文件）")
        for f in srt_files:
            process_single_file(str(f), bilingual)
    else:
        print(f"请提供有效的 .srt 文件或包含 .srt 文件的文件夹路径")


if __name__ == "__main__":
    main()
