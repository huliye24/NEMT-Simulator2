#!/usr/bin/env python3
"""
NEMT Code Helper - 云端代码助手
用法: python3 code.py "你的编程问题"
"""

import os
import sys

try:
    import requests
except ImportError:
    os.system("pip install requests -q")
    import requests

API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

MODEL = "google/gemma-3-27b-it"

SYSTEM_PROMPT = """你是一个专业的Python/JS/Go/React全栈程序员。
- 提供简洁、可运行的代码
- 包含必要的注释
- 解释关键点
- 如果需要，展示如何运行"""

def main():
    if len(sys.argv) < 2:
        print("用法: python3 code.py "你的编程问题"")
        print("示例: python3 code.py "用Python写一个快速排序"")
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
    }

    print("AI生成代码中...\n")

    try:
        response = requests.post(API_URL, json=data, headers=headers, timeout=120)
        result = response.json()

        if "choices" in result:
            code = result["choices"][0]["message"]["content"]
            print(code)
        else:
            print(f"错误: {result}")

    except Exception as e:
        print(f"请求失败: {e}")

if __name__ == "__main__":
    main()
