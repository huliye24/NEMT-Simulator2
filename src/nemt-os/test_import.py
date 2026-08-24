"""测试导入问题"""
import sys
from pathlib import Path

# 设置路径
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("测试 NEMT 导入")
print("=" * 60)

# 测试各个模块
modules = [
    ("nemt.core", "ConfigCenter"),
    ("nemt.core", "EventBus"),
    ("nemt.core", "ModuleCapsule"),
    ("nemt.core", "create_engine"),
]

errors = []
for module_name, obj_name in modules:
    try:
        module = __import__(module_name, fromlist=[obj_name])
        obj = getattr(module, obj_name)
        print(f"[OK] {module_name}.{obj_name}")
    except Exception as e:
        print(f"[FAIL] {module_name}.{obj_name}: {e}")
        errors.append((module_name, obj_name, str(e)))

print("\n" + "=" * 60)
if errors:
    print(f"发现 {len(errors)} 个导入错误")
    for m, o, e in errors:
        print(f"  - {m}.{o}: {e}")
else:
    print("所有核心模块导入成功!")
print("=" * 60)
