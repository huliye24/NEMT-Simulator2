#!/usr/bin/env python3
"""
CTO Agent - Daily Technical Health Scan Script

Features:
1. Check Git commit and change statistics
2. Run static analysis (ruff)
3. Run type checking (mypy)
4. Run test coverage
5. Scan tech debt markers (TODO: tech-debt)
6. Generate daily tech log

Usage:
    python cto_daily_scan.py
"""

import subprocess
import sys
import os
import io
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ============== Configuration ==============

PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "NEMT_Vision" / "Daily"
PYTHON_FILES = ["nemt_core.py", "nemt_signals.py", "nemt_state_machine.py",
                "nemt_risk.py", "nemt_execution.py", "nemt_model_node.py",
                "enhanced_phase_detector.py", "high_performance_nls.py"]


# ============== Utility Functions ==============

def run_command(cmd: List[str], cwd: Path = None, timeout: int = 60) -> Tuple[int, str, str]:
    """Execute command and return result"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timeout"
    except Exception as e:
        return -1, "", str(e)


def check_git_status() -> Dict:
    """Check Git status"""
    result = {
        "branch": "unknown",
        "ahead": 0,
        "behind": 0,
        "modified_files": [],
        "untracked_files": [],
        "staged_files": [],
        "last_commit": "unknown",
        "last_commit_date": "unknown"
    }

    # Get current branch
    code, stdout, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0:
        result["branch"] = stdout.strip()

    # Get diff from remote
    code, stdout, _ = run_command(["git", "rev-list", "--left-right", "--count", "@{u}...HEAD"])
    if code == 0:
        parts = stdout.strip().split()
        if len(parts) >= 2:
            result["ahead"] = int(parts[0])
            result["behind"] = int(parts[1])

    # Get changed files
    code, stdout, _ = run_command(["git", "status", "--porcelain"])
    if code == 0:
        for line in stdout.strip().split('\n'):
            if line:
                status = line[:2]
                filename = line[3:].strip()
                if status == "??":
                    result["untracked_files"].append(filename)
                elif status[0] in "MAD":
                    result["staged_files"].append(filename)
                else:
                    result["modified_files"].append(filename)

    # Get last commit
    code, stdout, _ = run_command(["git", "log", "-1", "--format=%H|%s|%ar"])
    if code == 0:
        parts = stdout.strip().split('|')
        if len(parts) >= 3:
            result["last_commit"] = parts[1]
            result["last_commit_date"] = parts[2]

    return result


def run_ruff_check() -> Dict:
    """Run Ruff static analysis"""
    result = {
        "passed": False,
        "errors": 0,
        "warnings": 0,
        "files_with_issues": []
    }

    # Check if ruff is installed
    code, _, _ = run_command(["python", "-m", "ruff", "--version"])
    if code != 0:
        result["message"] = "ruff not installed"
        return result

    # Run check
    code, stdout, stderr = run_command(
        ["python", "-m", "ruff", "check", "."] + PYTHON_FILES,
        timeout=120
    )

    # Parse output
    output = stdout + stderr
    errors = len(re.findall(r"[EF]\d+", output))
    warnings = len(re.findall(r"W\d+", output))

    result["errors"] = errors
    result["warnings"] = warnings
    result["passed"] = code == 0 and errors == 0
    result["output"] = output[:2000] if output else ""

    return result


def run_mypy_check() -> Dict:
    """Run mypy type checking"""
    result = {
        "passed": False,
        "errors": 0,
        "files_checked": 0
    }

    # Check if mypy is installed
    code, _, _ = run_command(["python", "-m", "mypy", "--version"])
    if code != 0:
        result["message"] = "mypy not installed"
        return result

    # Run check
    code, stdout, stderr = run_command(
        ["python", "-m", "mypy", "--ignore-missing-imports"] + PYTHON_FILES,
        timeout=120
    )

    output = stdout + stderr
    errors = len(re.findall(r"error:", output, re.IGNORECASE))

    result["errors"] = errors
    result["passed"] = code == 0 and errors == 0
    result["files_checked"] = len(PYTHON_FILES)
    result["output"] = output[:2000] if output else ""

    return result


def run_tests() -> Dict:
    """Run pytest and get coverage"""
    result = {
        "passed": False,
        "tests_run": 0,
        "tests_failed": 0,
        "tests_passed": 0,
        "coverage": None
    }

    # Check if pytest is installed
    code, _, _ = run_command(["python", "-m", "pytest", "--version"])
    if code != 0:
        result["message"] = "pytest not installed"
        return result

    # Run tests
    code, stdout, stderr = run_command(
        ["python", "-m", "pytest", "nemt_os/tests/", "-v", "--tb=short"],
        timeout=180
    )

    output = stdout + stderr

    # Parse test results
    passed = len(re.findall(r"PASSED", output))
    failed = len(re.findall(r"FAILED", output))

    result["tests_run"] = passed + failed
    result["tests_passed"] = passed
    result["tests_failed"] = failed
    result["passed"] = failed == 0

    return result


def scan_tech_debt() -> Dict:
    """Scan tech debt markers"""
    result = {
        "total": 0,
        "high_priority": [],
        "medium_priority": [],
        "low_priority": []
    }

    patterns = [
        (r"TODO.*tech.?debt", "high_priority"),
        (r"TODO.*P1", "high_priority"),
        (r"TODO.*critical", "high_priority"),
        (r"TODO.*P2", "medium_priority"),
        (r"TODO.*performance", "medium_priority"),
        (r"TODO.*refactor", "medium_priority"),
        (r"TODO.*low", "low_priority"),
        (r"TODO.*nice.?to.?have", "low_priority"),
    ]

    for py_file in PROJECT_ROOT.glob("**/*.py"):
        if "venv" in str(py_file) or ".venv" in str(py_file):
            continue

        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            for line_no, line in enumerate(content.split('\n'), 1):
                for pattern, priority in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        entry = {
                            "file": str(py_file.relative_to(PROJECT_ROOT)),
                            "line": line_no,
                            "text": line.strip()[:100]
                        }
                        result[priority].append(entry)
                        result["total"] += 1
        except Exception:
            pass

    return result


def calculate_health_score(git_status: Dict, ruff: Dict, mypy: Dict,
                          tests: Dict, tech_debt: Dict) -> Tuple[int, str, List[str]]:
    """Calculate technical health score (1-5)"""

    score = 5
    warnings = []

    # Git status check
    if git_status["modified_files"]:
        score -= 0.2
        warnings.append(f"有 {len(git_status['modified_files'])} 个未提交的修改")

    if git_status["behind"] > 0:
        score -= 0.3
        warnings.append(f"落后远程 {git_status['behind']} 个提交")

    # Ruff check
    if "message" not in ruff:
        if ruff["errors"] > 0:
            score -= 1
            warnings.append(f"Ruff发现 {ruff['errors']} 个错误")
        elif ruff["warnings"] > 5:
            score -= 0.3
            warnings.append(f"Ruff发现 {ruff['warnings']} 个警告")

    # mypy check
    if "message" not in mypy:
        if mypy["errors"] > 0:
            score -= 0.5
            warnings.append(f"mypy发现 {mypy['errors']} 个类型错误")

    # Test check
    if "message" not in tests:
        if tests["tests_failed"] > 0:
            score -= 1
            warnings.append(f"{tests['tests_failed']} 个测试失败")
        elif tests["tests_run"] == 0:
            score -= 0.5
            warnings.append("没有运行测试")

    # Tech debt check
    if tech_debt["total"] > 10:
        score -= 0.5
        warnings.append(f"有 {tech_debt['total']} 个技术债务标记")

    score = max(1, min(5, round(score)))

    # Score description
    if score == 5:
        health = "[GREEN] 优秀"
    elif score >= 4:
        health = "[GREEN] 良好"
    elif score >= 3:
        health = "[YELLOW] 一般"
    elif score >= 2:
        health = "[ORANGE] 较差"
    else:
        health = "[RED] 危急"

    return score, health, warnings


def generate_daily_log(
    git_status: Dict,
    ruff: Dict,
    mypy: Dict,
    tests: Dict,
    tech_debt: Dict,
    health_score: int,
    health_status: str,
    warnings: List[str]
) -> str:
    """Generate daily tech log"""

    today = datetime.now().strftime("%Y-%m-%d")
    weekday = datetime.now().strftime("%A")

    log = f"""# Daily Tech Log - {today} ({weekday})

> Auto-generated by CTO Agent

---

## Health Score

**Score**: {health_score}/5 - {health_status}

{warnings[0] if warnings else 'All checks passed'}

---

## Git Status

| Item | Value |
|------|-------|
| Current Branch | `{git_status['branch']}` |
| Ahead of remote | {git_status['ahead']} |
| Behind remote | {git_status['behind']} |
| Modified files | {len(git_status['modified_files'])} |
| Untracked files | {len(git_status['untracked_files'])} |

"""

    if git_status['modified_files']:
        log += "### Modified Files\n\n"
        for f in git_status['modified_files'][:10]:
            log += f"- `{f}`\n"
        if len(git_status['modified_files']) > 10:
            log += f"- ... and {len(git_status['modified_files']) - 10} more files\n"
        log += "\n"

    log += f"""### Last Commit

- **Message**: {git_status['last_commit']}
- **Time**: {git_status['last_commit_date']}

---

## Static Analysis

### Ruff Check

| Status | Errors | Warnings |
|--------|--------|----------|
| {"[OK]" if ruff.get('passed') else "[FAIL]"} | {ruff.get('errors', 'N/A')} | {ruff.get('warnings', 'N/A')} |

"""

    if ruff.get('output'):
        log += "```\n" + ruff['output'][:500] + "\n```\n"

    log += f"""### Mypy Type Check

| Status | Errors | Files Checked |
|--------|--------|--------------|
| {"[OK]" if mypy.get('passed') else "[FAIL]"} | {mypy.get('errors', 'N/A')} | {mypy.get('files_checked', 'N/A')} |

"""

    if mypy.get('output'):
        log += "```\n" + mypy['output'][:500] + "\n```\n"

    log += f"""---

## Test Status

| Status | Passed | Failed | Total |
|--------|--------|--------|-------|
| {"[OK] All Passed" if tests.get('passed') else "[FAIL] Some Failed"} | {tests.get('tests_passed', 'N/A')} | {tests.get('tests_failed', 'N/A')} | {tests.get('tests_run', 'N/A')} |

"""

    log += """---

## Tech Debt Scan

| Priority | Count |
|----------|-------|
"""

    log += f"| High (P1) | {len(tech_debt.get('high_priority', []))} |\n"
    log += f"| Medium (P2) | {len(tech_debt.get('medium_priority', []))} |\n"
    log += f"| Low (P3) | {len(tech_debt.get('low_priority', []))} |\n"

    if tech_debt.get('high_priority'):
        log += "\n### High Priority Debt\n\n"
        for item in tech_debt['high_priority'][:5]:
            log += f"- [{item['file']}:{item['line']}] {item['text']}\n"
        if len(tech_debt['high_priority']) > 5:
            log += f"- ... and {len(tech_debt['high_priority']) - 5} more high priority debts\n"

    log += f"""

---

## Recommended Actions

"""

    if warnings:
        for w in warnings:
            log += f"- {w}\n"
    else:
        log += "- System status is healthy, keep it up\n"

    log += f"""

---

## Meta

- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Script Version**: 1.0.0
- **Scope**: nemt_os/, root Python files

---

*This log is auto-generated by CTO Agent*
"""

    return log


def main():
    print("=" * 60)
    print("CTO Agent - Daily Technical Health Scan")
    print("=" * 60)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Git status
    print("[1/5] Checking Git status...")
    git_status = check_git_status()
    print(f"      Branch: {git_status['branch']}")
    print(f"      Modified files: {len(git_status['modified_files'])}")

    # 2. Ruff check
    print("\n[2/5] Running Ruff static analysis...")
    ruff = run_ruff_check()
    if "message" in ruff:
        print(f"      [!] {ruff['message']}")
    else:
        status = "[OK]" if ruff['passed'] else "[FAIL]"
        print(f"      {status} - Errors: {ruff['errors']}, Warnings: {ruff['warnings']}")

    # 3. Mypy check
    print("\n[3/5] Running Mypy type check...")
    mypy = run_mypy_check()
    if "message" in mypy:
        print(f"      [!] {mypy['message']}")
    else:
        status = "[OK]" if mypy['passed'] else "[FAIL]"
        print(f"      {status} - Errors: {mypy['errors']}")

    # 4. Tests
    print("\n[4/5] Running tests...")
    tests = run_tests()
    if "message" in tests:
        print(f"      [!] {tests['message']}")
    else:
        status = "[OK] All Passed" if tests['passed'] else "[FAIL] Some Failed"
        print(f"      {status} - Passed: {tests['tests_passed']}, Failed: {tests['tests_failed']}")

    # 5. Tech debt scan
    print("\n[5/5] Scanning tech debt...")
    tech_debt = scan_tech_debt()
    print(f"      High priority: {len(tech_debt['high_priority'])}")
    print(f"      Medium priority: {len(tech_debt['medium_priority'])}")
    print(f"      Low priority: {len(tech_debt['low_priority'])}")

    # Calculate health score
    print("\n" + "=" * 60)
    score, health, warnings = calculate_health_score(
        git_status, ruff, mypy, tests, tech_debt
    )
    print(f"Tech Health Score: {score}/5 - {health}")
    if warnings:
        for w in warnings:
            print(f"  [!] {w}")
    print("=" * 60)

    # Generate log
    log = generate_daily_log(
        git_status, ruff, mypy, tests, tech_debt,
        score, health, warnings
    )

    # Save log
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = OUTPUT_DIR / f"Daily_Tech_Log_{today}.md"

    output_file.write_text(log, encoding='utf-8')
    print(f"\n[DONE] Log saved: {output_file}")

    # Print log preview
    print("\n--- Log Preview ---")
    print(log[:2000])
    print("...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
