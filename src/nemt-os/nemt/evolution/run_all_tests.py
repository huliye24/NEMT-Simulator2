"""
自演化系统完整测试套件

运行所有测试:
  cd nemt_os/nemt/evolution
  python run_all_tests.py
"""

import os
import sys

# 确保路径正确
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 70)
print("NEMT Self-Evolution System - Complete Test Suite")
print("=" * 70)
print()


def run_test_file(filename, description):
    """运行单个测试文件"""
    print(f"\n{'=' * 60}")
    print(f"Running: {description}")
    print(f"File: {filename}")
    print("-" * 60)

    try:
        import subprocess

        result = subprocess.run(
            [sys.executable, filename], capture_output=True, text=True, cwd=os.path.dirname(__file__)
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print(f"[PASS] {description}")
            return True
        else:
            print(f"[FAIL] {description} (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return False


def main():
    tests = [
        ("run_tests.py", "Core Evolution Modules"),
        ("test_business_constraints.py", "Business Constraints"),
        ("test_persistence.py", "State Persistence"),
    ]

    passed = 0
    failed = 0

    for filename, description in tests:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        if os.path.exists(filepath):
            if run_test_file(filename, description):
                passed += 1
            else:
                failed += 1
        else:
            print(f"[SKIP] {filename} not found")

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total:  {passed + failed}")

    if failed == 0:
        print("\n  ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("\n  SOME TESTS FAILED!")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
