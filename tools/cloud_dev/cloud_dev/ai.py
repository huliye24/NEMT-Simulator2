#!/usr/bin/env python3
"""
NEMT Cloud AI - 云端AI对话工具
用法: python3 ai.py
"""

import os
import sys

try:
    import requests
except ImportError:
    print("安装requests库...")
    os.system("pip install requests -q")
    import requests

# API配置
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# 内置免费模型
MODELS = {
    "1": ("google/gemma-3-27b-it", "Gemma 27B (免费推荐)"),
    "2": ("qwen/qwen3-30b-a3b", "Qwen3 30B (免费推荐)"),
    "3": ("deepseek/deepseek-prover-v2:free", "DeepSeek Prover (免费)"),
    "4": ("anthropic/claude-3-haiku", "Claude 3 Haiku (免费)"),
}

def chat(model, messages):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": messages,
    }
    response = requests.post(API_URL, json=data, headers=headers, timeout=120)
    return response.json()

def main():
    print("=" * 60)
    print("  NEMT Cloud AI - 云端智能助手")
    print("=" * 60)

    # 检查API Key
    if not API_KEY:
        print("\n首次使用请设置API Key（免费）：")
        print("  1. 访问 https://openrouter.ai/keys")
        print("  2. 点击 'Create Key' 获取密钥")
        print("  3. 运行: export OPENROUTER_API_KEY='your-key'")
        print("\n免费模型推荐（无需API Key）：google/gemma-3-27b-it")
        print("-" * 60)

    # 选择模型
    print("\n可用模型：")
    for k, (model, desc) in MODELS.items():
        print(f"  {k}. {desc}")

    choice = input("\n选择模型 (1-4，默认1): ").strip() or "1"
    model = MODELS.get(choice, MODELS["1"])[0]

    print(f"\n使用模型: {model}")
    print("-" * 60)
    print("开始对话（输入 'exit' 退出，'clear' 清屏）")
    print("=" * 60 + "\n")

    messages = []

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\n再见！")
                break
            if user_input.lower() == "clear":
                messages = []
                print("对话已清空\n")
                continue
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})

            print("\nAI思考中...\n")

            try:
                result = chat(model, messages)
                if "choices" in result:
                    response = result["choices"][0]["message"]["content"]
                    messages.append({"role": "assistant", "content": response})
                    print(response)
                else:
                    print(f"错误: {result}")
            except Exception as e:
                print(f"请求失败: {e}")

            print()

        except KeyboardInterrupt:
            print("\n\n再见！")
            break

if __name__ == "__main__":
    main()
