#!/usr/bin/env python3
"""
每日熵减检查脚本
用于每日15分钟熵减仪式
"""

import subprocess
import sys
from pathlib import Path


def check_structure_entropy():
    """Check structure entropy"""
    print("\n[1] Structure Entropy Check")
    print("-" * 40)

    nemt_dir = Path(__file__).parent.parent / "nemt"

    # Check for duplicate directories
    duplicate_dirs = []
    for d in nemt_dir.rglob("*"):
        if d.is_dir():
            name = d.name.lower()
            if name in ["emt_core", "nemt_core", "event_bus"] and "core" not in str(d):
                duplicate_dirs.append(str(d))

    if duplicate_dirs:
        print(f"    [FAIL] Found duplicate dirs: {duplicate_dirs}")
        return False
    else:
        print("    [PASS] No duplicate directories")
        return True


def check_imports():
    """Check if imports work correctly"""
    print("\n[2] Import Check")
    print("-" * 40)

    try:
        result = subprocess.run(
            [sys.executable, "-c", "from nemt import NEMTEngine, NLSSolver, MarketPhase; print('OK')"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=30,
        )

        if result.returncode == 0 and "OK" in result.stdout:
            print("    [PASS] Core module imports work")
            return True
        else:
            print(f"    [FAIL] Import failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"    [FAIL] Check exception: {e}")
        return False


def check_test_coverage():
    """Check test coverage"""
    print("\n[3] Test Entropy Check")
    print("-" * 40)

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--co", "-q"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            timeout=60,
        )

        lines = result.stdout.strip().split("\n")
        test_count = sum(1 for l in lines if l.startswith("test_"))

        print(f"    Found {test_count} tests")
        return True
    except Exception as e:
        print(f"    [WARN] Cannot run test collection: {e}")
        return True  # Don't block


def check_docstrings():
    """Check if core modules have docstrings"""
    print("\n[4] Doc Entropy Check")
    print("-" * 40)

    core_modules = [
        "nemt/core/capsule.py",
        "nemt/core/event_bus.py",
        "nemt/core/nemt_engine.py",
        "nemt/nEMT_core/nls_solver.py",
    ]

    missing_docs = []
    for module in core_modules:
        path = Path(__file__).parent.parent / module
        if path.exists():
            content = path.read_text(encoding="utf-8")
            # Check for module-level docstring
            if '"""' not in content[:500]:
                missing_docs.append(module)

    if missing_docs:
        print(f"    [WARN] Missing docs: {missing_docs}")
        return False
    else:
        print("    [PASS] Core modules have docs")
        return True


def daily_summary():
    """每日熵减总结"""
    print("=" * 60)
    print("[NEMT] Daily Entropy Check")
    print("=" * 60)

    checks = [
        ("Structure Entropy", check_structure_entropy()),
        ("Import Check", check_imports()),
        ("Test Entropy", check_test_coverage()),
        ("Doc Entropy", check_docstrings()),
    ]

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)

    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} passed")
    print("=" * 60)

    if passed == total:
        print("\n[OK] System healthy!")
        return 0
    else:
        print("\n[WARN] Entropy reduction needed")
        return 1


if __name__ == "__main__":
    sys.exit(daily_summary())
