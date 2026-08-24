#!/usr/bin/env python3
"""
NEMT 开发辅助脚本

常用开发任务快捷命令。
"""

import os
import sys
import subprocess
from pathlib import Path


def run(cmd: str, check: bool = True) -> int:
    """运行命令"""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f"命令失败: {cmd}")
    return result.returncode


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("""
NEMT 开发辅助工具

用法: python scripts/dev.py <命令>

命令:
  test          运行所有测试
  test-watch    监听模式运行测试
  test-cov      运行测试并生成覆盖率报告
  lint          代码检查
  format        代码格式化
  typecheck     类型检查
  run           运行示例
  new-capsule   创建新胶囊
  clean         清理缓存
  help          显示帮助
        """)
        return

    cmd = sys.argv[1].lower()

    if cmd == 'test':
        run("python -m pytest tests/ -v --tb=short")

    elif cmd == 'test-watch':
        run("python -m pytest tests/ -v --watch")

    elif cmd == 'test-cov':
        run("python -m pytest tests/ -v --cov=nemt --cov-report=html --cov-report=term")

    elif cmd == 'lint':
        print("检查代码...")
        run("python -m flake8 nemt/ --max-line-length=120 --extend-ignore=E203,W503")
        run("python -m black --check nemt/")

    elif cmd == 'format':
        print("格式化代码...")
        run("python -m black nemt/ tests/")
        run("python -m isort nemt/ tests/")

    elif cmd == 'typecheck':
        print("类型检查...")
        run("python -m mypy nemt/ --ignore-missing-imports")

    elif cmd == 'run':
        example = sys.argv[2] if len(sys.argv) > 2 else 'examples/simple_backtest.py'
        run(f"python {example}")

    elif cmd == 'new-capsule':
        if len(sys.argv) < 3:
            print("用法: python scripts/dev.py new-capsule <胶囊名称>")
            return
        name = sys.argv[2]
        run(f"python scripts/generate_capsule.py capsule {name} -s nemt.signal -p nemt.new_signal")

    elif cmd == 'clean':
        print("清理缓存...")
        for pattern in ['__pycache__', '*.pyc', '*.pyo', '.pytest_cache', '.mypy_cache', 'htmlcov', '.coverage']:
            for path in Path('.').rglob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path, ignore_errors=True)
        print("清理完成")

    elif cmd == 'help':
        print(__doc__)

    else:
        print(f"未知命令: {cmd}")
        print("运行 'python scripts/dev.py help' 查看帮助")


if __name__ == '__main__':
    main()
