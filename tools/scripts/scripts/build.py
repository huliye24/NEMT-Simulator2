#!/usr/bin/env python3
"""
NEMT 构建脚本

自动化构建、测试和打包。
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def run_command(cmd: str, cwd: str = None, check: bool = True) -> int:
    """运行命令"""
    print(f"执行: {cmd}")
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        stdout=sys.stdout, stderr=subprocess.STDOUT
    )
    if check and result.returncode != 0:
        print(f"命令失败: {cmd}")
        sys.exit(1)
    return result.returncode


def clean():
    """清理构建目录"""
    print("\n[1/5] 清理构建目录...")

    dirs_to_clean = ['build', 'dist', '*.egg-info', '__pycache__']
    for pattern in dirs_to_clean:
        for path in Path('.').rglob(pattern):
            if path.is_dir():
                print(f"  删除: {path}")
                shutil.rmtree(path, ignore_errors=True)

    # 清理 pyc 文件
    for path in Path('.').rglob('*.pyc'):
        path.unlink(missing_ok=True)

    print("清理完成")


def check_dependencies():
    """检查依赖"""
    print("\n[2/5] 检查依赖...")

    required = ['pytest', 'yaml', 'numpy', 'pandas']
    for module in required:
        try:
            __import__(module)
            print(f"  {module}: OK")
        except ImportError:
            print(f"  {module}: 缺失!")
            print("请运行: pip install -r requirements.txt")
            sys.exit(1)

    print("依赖检查完成")


def run_tests():
    """运行测试"""
    print("\n[3/5] 运行测试...")

    # 运行 pytest
    result = run_command(
        "python -m pytest tests/ -v --tb=short -x",
        check=False
    )

    if result != 0:
        print("测试失败!")
        sys.exit(1)

    print("测试完成")


def build_package():
    """构建包"""
    print("\n[4/5] 构建包...")

    # 使用 setup.py 构建
    if Path('setup.py').exists():
        run_command("python setup.py sdist bdist_wheel")
    else:
        print("  setup.py 不存在，跳过打包")

    print("构建完成")


def generate_docs():
    """生成文档"""
    print("\n[5/5] 生成文档...")

    # 创建简单的文档结构
    docs_dir = Path('docs')
    docs_dir.mkdir(exist_ok=True)

    # 生成 API 文档
    api_doc = docs_dir / 'API.md'
    api_doc.write_text("""# NEMT API 文档

## 核心组件

### EventBus
```python
from nemt.core import EventBus

eb = EventBus()
eb.subscribe('event.type', handler)
eb.publish('event.type', data)
```

### ConfigCenter
```python
from nemt.core import ConfigCenter

cc = ConfigCenter()
cc.set('key', value)
cc.get('key')
```

## 胶囊

### MarketCapsule
### SignalCapsule
### RiskCapsule
### ExecutionCapsule
### BrainCapsule
### MonitorCapsule
### PhaseCapsule
""", encoding='utf-8')

    print("文档生成完成")


def main():
    """主函数"""
    print("=" * 60)
    print("NEMT 构建系统")
    print("=" * 60)

    # 解析参数
    args = sys.argv[1:]

    if '--help' in args or '-h' in args:
        print("""
用法: python scripts/build.py [选项]

选项:
  --clean      只清理
  --test       只运行测试
  --no-test    跳过测试
  --no-docs    跳过文档生成
  --help       显示帮助
        """)
        return

    clean_only = '--clean' in args
    test_only = '--test' in args
    skip_test = '--no-test' in args
    skip_docs = '--no-docs' in args

    if test_only:
        run_tests()
        return

    if clean_only:
        clean()
        return

    if not skip_test:
        run_tests()
    else:
        print("\n[跳过] 测试")

    check_dependencies()
    build_package()

    if not skip_docs:
        generate_docs()
    else:
        print("\n[跳过] 文档生成")

    print("\n" + "=" * 60)
    print("构建完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
