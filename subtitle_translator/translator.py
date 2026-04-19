"""
DeepSeek 翻译核心模块
支持单条翻译、批量翻译、带自动重试和错误处理
"""
import time
from openai import OpenAI
from config import Config


class DeepSeekTranslator:
    SYSTEM_PROMPT = (
        "你是一个专业字幕翻译助手。将输入的英文句子翻译成简体中文，"
        "只返回译文，不要任何解释、注释或原文。保持字幕简洁自然。"
    )

    BATCH_PROMPT = (
        "你是一个专业字幕翻译助手。我会给你若干条英文句子，每条用行分隔。"
        "请将每条翻译成简体中文，每行只输出一个翻译结果，不要添加任何额外文字或编号。"
    )

    def __init__(self):
        self.client = OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_BASE_URL
        )
        self.model = Config.MODEL

    def _call_api(self, messages, retries=0):
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=Config.TEMPERATURE,
                timeout=Config.REQUEST_TIMEOUT
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if retries < Config.MAX_RETRIES:
                wait = 2 ** retries
                print(f"  请求失败，第 {retries + 1} 次重试，等待 {wait}s... ({e})")
                time.sleep(wait)
                return self._call_api(messages, retries + 1)
            else:
                raise RuntimeError(f"API 调用失败（已重试 {Config.MAX_RETRIES} 次）: {e}") from e

    def translate_single(self, english_text: str) -> str:
        """翻译单条字幕"""
        if not english_text or not english_text.strip():
            return ""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": english_text}
        ]
        return self._call_api(messages)

    def translate_batch(self, texts: list) -> list:
        """
        批量翻译多条字幕。通过特殊分隔符一次性请求，提高效率。
        返回翻译结果列表，数量与输入 texts 一致。
        """
        if not texts:
            return []

        # 过滤空字幕
        non_empty = [(i, t) for i, t in enumerate(texts) if t and t.strip()]
        if not non_empty:
            return texts

        # 如果全部为空，直接返回
        if len(non_empty) == len(texts):
            return self._do_batch_translate(texts)

        # 部分为空：翻译非空的，保留空的位置
        result = list(texts)
        non_empty_texts = [t for _, t in non_empty]
        translations = self._do_batch_translate(non_empty_texts)

        for (orig_idx, _), trans in zip(non_empty, translations):
            result[orig_idx] = trans

        return result

    # 不易与字幕文本冲突的分隔符
    DELIMITER = "\n"

    def _do_batch_translate(self, texts: list) -> list:
        """执行批量翻译核心逻辑"""
        concatenated = self.DELIMITER.join(texts)

        messages = [
            {"role": "system", "content": self.BATCH_PROMPT},
            {"role": "user", "content": concatenated}
        ]

        result_str = self._call_api(messages)

        # 按换行符拆分，去除空行
        translations = [t.strip() for t in result_str.split(self.DELIMITER) if t.strip()]

        # 数量不匹配时降级为逐条翻译
        if len(translations) != len(texts):
            print(f"  警告：批量翻译返回数量不匹配 ({len(translations)} vs {len(texts)})，切换为逐条翻译...")
            return [self.translate_single(t) if t and t.strip() else t for t in texts]

        return translations
