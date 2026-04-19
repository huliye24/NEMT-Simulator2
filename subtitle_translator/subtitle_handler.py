"""
字幕文件读写模块
使用 pysubs2 处理 SRT 文件
"""
import pysubs2


class SubtitleHandler:
    @staticmethod
    def load(file_path: str) -> pysubs2.SSAFile:
        """加载字幕文件"""
        return pysubs2.load(file_path, encoding="utf-8")

    @staticmethod
    def save(subs: pysubs2.SSAFile, output_path: str):
        """保存字幕文件"""
        subs.save(output_path, encoding="utf-8")

    @staticmethod
    def extract_texts(subs: pysubs2.SSAFile) -> list:
        """提取所有字幕事件的纯文本"""
        return [event.text for event in subs]

    @staticmethod
    def apply_translations(subs: pysubs2.SSAFile, translations: list, bilingual: bool = False):
        """
        将译文写回字幕。
        bilingual=True 时，保留原文并换行追加译文。
        """
        if len(subs) != len(translations):
            raise ValueError(
                f"字幕条数与翻译结果数量不匹配: {len(subs)} vs {len(translations)}"
            )

        for event, trans in zip(subs, translations):
            if bilingual:
                event.text = f"{event.text}\n{trans}"
            else:
                event.text = trans
