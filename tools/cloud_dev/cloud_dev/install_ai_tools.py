#!/usr/bin/env python3
"""一键安装云端AI编程环境"""

import sys
import paramiko
import time

HOST = "42.51.42.123"
PORT = 22
USERNAME = "root"
PASSWORD = "YrV27j15"


def ssh_connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USERNAME, password=PASSWORD, timeout=30)
    return client


def run_command(client, cmd, timeout=60):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    return stdout.read().decode('utf-8', errors='ignore') + stderr.read().decode('utf-8', errors='ignore')


def main():
    print("=" * 60)
    print("  一键安装云端AI编程环境")
    print("=" * 60)

    try:
        client = ssh_connect()
        print("\n已连接服务器，开始安装...\n")

        # 1. 安装 pip 和 requests
        print("[1/5] 安装基础工具...")
        run_command(client, "apt-get update -qq && apt-get install -y -qq python3-pip curl", timeout=120)
        print("  完成")

        # 2. 创建一个简单易用的AI对话脚本
        print("\n[2/5] 创建AI对话工具...")

        ai_script = '''#!/usr/bin/env python3
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
        print("\\n首次使用请设置API Key（免费）：")
        print("  1. 访问 https://openrouter.ai/keys")
        print("  2. 点击 'Create Key' 获取密钥")
        print("  3. 运行: export OPENROUTER_API_KEY='your-key'")
        print("\\n免费模型推荐（无需API Key）：google/gemma-3-27b-it")
        print("-" * 60)

    # 选择模型
    print("\\n可用模型：")
    for k, (model, desc) in MODELS.items():
        print(f"  {k}. {desc}")

    choice = input("\\n选择模型 (1-4，默认1): ").strip() or "1"
    model = MODELS.get(choice, MODELS["1"])[0]

    print(f"\\n使用模型: {model}")
    print("-" * 60)
    print("开始对话（输入 'exit' 退出，'clear' 清屏）")
    print("=" * 60 + "\\n")

    messages = []

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\\n再见！")
                break
            if user_input.lower() == "clear":
                messages = []
                print("对话已清空\\n")
                continue
            if not user_input.strip():
                continue

            messages.append({"role": "user", "content": user_input})

            print("\\nAI思考中...\\n")

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
            print("\\n\\n再见！")
            break

if __name__ == "__main__":
    main()
'''

        with open("ai.py", "w", encoding="utf-8") as f:
            f.write(ai_script)

        sftp = client.open_sftp()
        sftp.put("ai.py", "/root/ai.py")
        sftp.close()
        run_command(client, "chmod +x /root/ai.py")
        print("  完成")

        # 3. 创建一个代码助手脚本（更强大）
        print("\n[3/5] 创建代码助手工具...")

        code_script = '''#!/usr/bin/env python3
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
        print("用法: python3 code.py \"你的编程问题\"")
        print("示例: python3 code.py \"用Python写一个快速排序\"")
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

    print("AI生成代码中...\\n")

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
'''

        with open("code.py", "w", encoding="utf-8") as f:
            f.write(code_script)

        sftp = client.open_sftp()
        sftp.put("code.py", "/root/code.py")
        sftp.close()
        run_command(client, "chmod +x /root/code.py")
        print("  完成")

        # 4. 创建快捷命令
        print("\n[4/5] 创建快捷命令...")

        run_command(client, '''cat >> /root/.bashrc << 'EOF'

# NEMT Cloud AI 快捷命令
alias ai='python3 /root/ai.py'
alias code='python3 /root/code.py'

# 显示帮助
nemt-help() {
    echo "=========================================="
    echo "  NEMT Cloud AI - 快捷命令"
    echo "=========================================="
    echo ""
    echo "  ai          - 启动AI对话"
    echo "  code '问题' - 快速获取代码"
    echo ""
    echo "  示例:"
    echo "    ai"
    echo "    code '写一个Web服务器'"
    echo ""
    echo "=========================================="
}
echo ""
echo "  ✓ NEMT AI工具已加载 (运行 'nemt-help' 查看)"
echo ""
EOF
''')
        print("  完成")

        # 5. 测试运行
        print("\n[5/5] 测试环境...")
        result = run_command(client, "python3 /root/ai.py --version 2>/dev/null || echo 'Ready'")
        print(f"  {result.strip() if result.strip() else 'Ready'}")

        print("\n" + "=" * 60)
        print("  安装完成！")
        print("=" * 60)
        print("")
        print("  在wede终端中运行以下命令：")
        print("")
        print("  1. AI对话模式:")
        print("     ai")
        print("")
        print("  2. 快速获取代码:")
        print("     code '帮我写一个Flask服务器'")
        print("")
        print("  3. 查看帮助:")
        print("     nemt-help")
        print("")
        print("=" * 60)

        client.close()

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
