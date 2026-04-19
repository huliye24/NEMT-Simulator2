"""
配置模块
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    MODEL = "deepseek-chat"

    # 翻译参数
    MAX_RETRIES = 3
    REQUEST_TIMEOUT = 30
    TEMPERATURE = 0.1

    # 批处理大小（一次请求翻译多少条字幕）
    BATCH_SIZE = 10
