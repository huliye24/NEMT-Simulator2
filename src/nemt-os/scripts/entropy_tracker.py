#!/usr/bin/env python3
"""
熵减追踪脚本
每天记录技术债务和熵减进度
"""

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class TechnicalDebt:
    """技术债务记录"""

    id: str
    description: str
    debt_type: str  # 坏账/低息/正常/高息/有毒
    interest_rate: str  # 低/中/高/极高
    status: str  # 活跃/已偿还/可忽略
    created_date: str
    resolved_date: str | None = None


@dataclass
class EntropyReduction:
    """熵减记录"""

    date: str
    work_done: str
    entropy_type: str  # 结构/逻辑/依赖/知识/测试
    files_changed: list[str]
    lines_added: int
    lines_deleted: int
    net_change: int


class EntropyTracker:
    """熵减追踪器"""

    def __init__(self, data_dir: str = "data/entropy"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.debt_file = self.data_dir / "debts.json"
        self.log_file = self.data_dir / "entropy_log.json"

    def add_debt(self, debt: TechnicalDebt):
        """添加技术债务"""
        debts = self.load_debts()
        debts.append(asdict(debt))
        self.save_debts(debts)

    def resolve_debt(self, debt_id: str):
        """偿还技术债务"""
        debts = self.load_debts()
        for debt in debts:
            if debt["id"] == debt_id:
                debt["status"] = "已偿还"
                debt["resolved_date"] = datetime.now().strftime("%Y-%m-%d")
        self.save_debts(debts)

    def log_entropy_reduction(self, work: EntropyReduction):
        """记录熵减工作"""
        log = self.load_log()
        log.append(asdict(work))
        self.save_log(log)

    def get_debt_health(self) -> dict:
        """计算债务健康度"""
        debts = self.load_debts()
        total = len(debts)
        if total == 0:
            return {"health": 100, "total": 0, "active": 0, "resolved": 0}

        active = sum(1 for d in debts if d["status"] == "活跃")
        resolved = sum(1 for d in debts if d["status"] == "已偿还")
        health = (resolved / total) * 100 if total > 0 else 100

        return {"health": round(health, 1), "total": total, "active": active, "resolved": resolved}

    def load_debts(self) -> list[dict]:
        if self.debt_file.exists():
            with open(self.debt_file, encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_debts(self, debts: list[dict]):
        with open(self.debt_file, "w", encoding="utf-8") as f:
            json.dump(debts, f, ensure_ascii=False, indent=2)

    def load_log(self) -> list[dict]:
        if self.log_file.exists():
            with open(self.log_file, encoding="utf-8") as f:
                return json.load(f)
        return []

    def save_log(self, log: list[dict]):
        with open(self.log_file, "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

    def print_report(self):
        """打印熵减报告"""
        print("=" * 60)
        print("NEMT 熵减追踪报告")
        print("=" * 60)

        health = self.get_debt_health()
        print(f"\n债务健康度: {health['health']}%")
        print(f"总债务数: {health['total']}")
        print(f"活跃债务: {health['active']}")
        print(f"已偿还: {health['resolved']}")

        print("\n最近熵减记录:")
        log = self.load_log()
        for entry in log[-5:]:
            print(f"  - [{entry['date']}] {entry['work_done']}")
            print(f"    类型: {entry['entropy_type']}, 净变化: {entry['net_change']:+d} 行")

    def get_git_diff_stats(self) -> dict:
        """获取 Git diff 统计"""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat", "HEAD"], capture_output=True, text=True, cwd=Path(__file__).parent.parent
            )

            stats = {"files": 0, "insertions": 0, "deletions": 0}
            for line in result.stdout.strip().split("\n"):
                if "files changed" in line:
                    parts = line.split()
                    for i, p in enumerate(parts):
                        if p == "changed":
                            stats["files"] = int(parts[i - 1])
                        if p == "insertions(+)":
                            stats["insertions"] = int(parts[i - 1])
                        if p == "deletions(-)":
                            stats["deletions"] = int(parts[i - 1])
            return stats
        except Exception:
            return {"files": 0, "insertions": 0, "deletions": 0}


def main():
    tracker = EntropyTracker()

    # 打印报告
    tracker.print_report()

    # 获取 Git 统计
    print("\n当前 Git 变更统计:")
    stats = tracker.get_git_diff_stats()
    print(f"  文件数: {stats['files']}")
    print(f"  新增行: {stats['insertions']}")
    print(f"  删除行: {stats['deletions']}")


if __name__ == "__main__":
    main()
