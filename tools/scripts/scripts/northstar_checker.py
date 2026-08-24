#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEMT NorthStar Code Checker
代码变更北极星检测器 - 每次写代码后自动检查是否对齐北极星
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

PROJECT_ROOT = Path(__file__).parent.parent
RULES_DIR = PROJECT_ROOT / ".cursor" / "rules"
COGNITIVE_DIR = RULES_DIR / "cognitive"

# NEMT 北极星
NORTHSTAR = {
    "statement": "构建一个让策略在生态中生存、竞争、进化的金融系统",
    "values": [
        "策略是生物体，不是规则集",
        "系统适应市场，不预测市场",
        "风控优先级高于收益",
        "民主化算法交易"
    ],
    "constellations": {
        "A": {
            "name": "可运行的多策略回测引擎",
            "kpis": ["策略类型支持≥5种", "回测时间<60秒", "回测报告完整"],
            "keywords": ["backtest", "回测", "strategy", "策略", "signal", "信号", "market", "市场"]
        },
        "B": {
            "name": "策略淘汰机制",
            "kpis": ["胜率<40%自动淘汰", "淘汰准确率>70%"],
            "keywords": ["eliminate", "淘汰", "filter", "filter", "selection", "选择", "evolve", "进化"]
        },
        "C": {
            "name": "大脑层动态权重分配",
            "kpis": ["夏普比率>1.5", "权重调整响应<5分钟"],
            "keywords": ["brain", "大脑", "weight", "权重", "dynamic", "动态", "adjust", "调整"]
        },
        "D": {
            "name": "实盘接入",
            "kpis": ["日交易量>100笔", "执行延迟<100ms"],
            "keywords": ["live", "实盘", "trade", "交易", "execute", "执行", "order", "订单"]
        }
    }
}


class NorthStarChecker:
    """北极星检测器"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.changed_files = []
        self.alignment_score = 0
        self.suggestions = []
    
    def get_git_changes(self) -> List[str]:
        """获取 Git 变更的文件"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 也检查暂存区
            staged_result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            files = set()
            if result.stdout:
                files.update(result.stdout.strip().split('\n'))
            if staged_result.stdout:
                files.update(staged_result.stdout.strip().split('\n'))
            
            # 过滤有效的代码文件
            valid_extensions = ['.py', '.go', '.ts', '.tsx', '.js', '.jsx', '.java', '.rs', '.cpp']
            valid_files = [f for f in files if f and any(f.endswith(ext) for ext in valid_extensions)]
            
            return list(valid_files)
        except Exception as e:
            print(f"[WARN] Failed to get git changes: {e}")
            return []
    
    def analyze_file(self, file_path: str) -> Dict:
        """分析单个文件"""
        result = {
            "file": file_path,
            "constellation": None,
            "alignment_score": 0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return result
            
            content = full_path.read_text(encoding='utf-8', errors='ignore').lower()
            filename_lower = file_path.lower()
            
            # 检查与星座的关联
            for constellation_id, const_info in NORTHSTAR["constellations"].items():
                score = 0
                matches = []
                
                # 检查文件名
                for kw in const_info["keywords"]:
                    if kw.lower() in filename_lower:
                        score += 2
                        matches.append(f"文件名含 '{kw}'")
                
                # 检查文件内容
                for kw in const_info["keywords"]:
                    if kw.lower() in content:
                        score += 1
                        if kw not in matches:
                            matches.append(f"内容含 '{kw}'")
                
                if score > 0:
                    if result["constellation"] is None or score > result["alignment_score"]:
                        result["constellation"] = constellation_id
                        result["alignment_score"] = score
                        result["recommendations"].extend(matches)
            
            # 检查架构违规
            issues = self._check_architecture(content, file_path)
            result["issues"].extend(issues)
            
            return result
            
        except Exception as e:
            result["issues"].append(f"分析失败: {str(e)}")
            return result
    
    def _check_architecture(self, content: str, file_path: str) -> List[str]:
        """检查架构违规"""
        issues = []
        
        # 检查是否在正确的目录
        if "/core/" in file_path or "\\core\\" in file_path:
            # core 层不应有 UI 代码
            ui_keywords = ["<div>", "<span>", "render", "html", "css", "className"]
            for kw in ui_keywords:
                if kw in content.lower():
                    issues.append(f"[架构] core 层不应有 UI 代码 (发现 '{kw}')")
        
        if "/web/" in file_path or "\\web\\" in file_path or "/ui/" in file_path:
            # UI 层不应有核心业务逻辑
            biz_keywords = ["database", "db.", "connection", "sql"]
            for kw in biz_keywords:
                if kw in content.lower() and "mock" not in content.lower():
                    issues.append(f"[架构] UI 层不应有数据库逻辑 (发现 '{kw}')")
        
        return issues
    
    def check_all(self) -> Dict:
        """检查所有变更"""
        print("\n" + "="*60)
        print("   [NORTHSTAR] 北极星代码检查器")
        print("="*60)
        print()
        
        # 获取变更
        self.changed_files = self.get_git_changes()
        
        if not self.changed_files:
            print("[INFO] 没有检测到代码变更")
            return {"status": "no_changes"}
        
        print(f"[INFO] 检测到 {len(self.changed_files)} 个变更文件:")
        for f in self.changed_files[:10]:
            print(f"    - {f}")
        if len(self.changed_files) > 10:
            print(f"    ... 还有 {len(self.changed_files) - 10} 个文件")
        print()
        
        # 分析每个文件
        results = []
        aligned_count = 0
        
        for file_path in self.changed_files:
            result = self.analyze_file(file_path)
            results.append(result)
            
            if result["constellation"]:
                aligned_count += 1
        
        # 计算整体对齐度
        alignment_rate = (aligned_count / len(self.changed_files)) * 100 if self.changed_files else 0
        
        # 构建报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(self.changed_files),
            "aligned_files": aligned_count,
            "alignment_rate": alignment_rate,
            "file_results": results,
            "northstar": NORTHSTAR["statement"]
        }
        
        # 显示结果
        self._print_results(report)
        
        return report
    
    def _print_results(self, report: Dict):
        """打印结果"""
        print("-"*60)
        print("[STAR] STAR 北极星测试")
        print("-"*60)
        print()
        print(f"  北极星: {report['northstar']}")
        print()
        print(f"  变更文件数: {report['total_files']}")
        print(f"  对齐星座数: {report['aligned_files']}")
        print(f"  对齐率: {report['alignment_rate']:.1f}%")
        print()
        
        # 按星座分组
        by_constellation = {}
        for result in report["file_results"]:
            if result["constellation"]:
                cid = result["constellation"]
                if cid not in by_constellation:
                    by_constellation[cid] = []
                by_constellation[cid].append(result)
        
        if by_constellation:
            print("-"*60)
            print("[CONSTELLATION] 星座对齐")
            print("-"*60)
            print()
            
            for cid in sorted(by_constellation.keys()):
                const_info = NORTHSTAR["constellations"][cid]
                results = by_constellation[cid]
                
                print(f"  星座 {cid}: {const_info['name']}")
                for r in results:
                    print(f"    - {r['file']}")
                    for rec in r.get("recommendations", [])[:3]:
                        print(f"      → {rec}")
                print()
        
        # 检查未对齐文件
        unaligned = [r for r in report["file_results"] if not r["constellation"]]
        if unaligned:
            print("-"*60)
            print("[WARNING] 未对齐文件 (建议检查)")
            print("-"*60)
            print()
            
            for r in unaligned[:5]:
                print(f"  - {r['file']}")
            if len(unaligned) > 5:
                print(f"  ... 还有 {len(unaligned) - 5} 个文件")
            print()
        
        # 架构问题
        all_issues = []
        for r in report["file_results"]:
            all_issues.extend(r.get("issues", []))
        
        if all_issues:
            print("-"*60)
            print("[ARCH] 架构问题")
            print("-"*60)
            print()
            
            for issue in all_issues[:10]:
                print(f"  {issue}")
            print()
        
        # 给出建议
        print("-"*60)
        print("[TIP] 北极星建议")
        print("-"*60)
        print()
        
        if report['alignment_rate'] >= 80:
            print("  [OK] 非常好！你的代码变更高度对齐北极星")
            print("  继续聚焦于核心星座目标")
        elif report['alignment_rate'] >= 50:
            print("  [WARN] 不错，但有改进空间")
            print("  建议：优先处理与星座相关的文件")
        elif report['alignment_rate'] > 0:
            print("  [FAIL] 对齐度较低")
            print("  建议：在继续之前，先确认这些变更的必要性")
        else:
            print("  [FAIL][FAIL] 严重偏离！")
            print("  建议：在提交之前进行 STAR 测试")
            print()
            print("  请先问自己：")
            print("  1. 这些变更为什么做？")
            print("  2. 它们对哪个星座有贡献？")
            print("  3. 不做会怎样？")
        
        print()
        print("="*60)
    
    def star_test(self, decision_desc: str = None) -> Dict:
        """运行 STAR 测试"""
        if decision_desc is None:
            decision_desc = f"提交 {len(self.changed_files)} 个文件"
        
        print()
        print("="*60)
        print("   🌟 STAR 北极星测试")
        print("="*60)
        print()
        print(f"  决策: {decision_desc}")
        print()
        
        # 简化的 STAR 测试
        questions = [
            ("S - 战略对齐", "这个决策直接服务于北极星/星座目标吗？"),
            ("T - 权衡检验", "牺牲了什么？获得的收益是否值得？"),
            ("A - 目标对齐", "能在3步内说清楚与最终目标的关系吗？"),
            ("R - 可逆性评估", "如果错了，撤销需要多少成本？"),
            ("O - 主动选择", "是主动追求还是被动的'看起来不错'？")
        ]
        
        results = []
        yes_count = 0
        
        for q_id, q_text in questions:
            print(f"  {q_text}")
            answer = input(f"    [y/n/d=需要讨论] > ").strip().lower()
            
            if answer in ['y', 'yes', '是', '1']:
                result = "YES"
                yes_count += 1
            elif answer in ['n', 'no', '否', '0']:
                result = "NO"
            else:
                result = "需要讨论"
            
            results.append((q_id, result))
            print()
        
        # 结论
        print("-"*60)
        print("📋 测试结论")
        print("-"*60)
        print()
        
        print(f"  S - 战略对齐: {results[0][1]}")
        print(f"  T - 权衡检验: {results[1][1]}")
        print(f"  A - 目标对齐: {results[2][1]}")
        print(f"  R - 可逆性评估: {results[3][1]}")
        print(f"  O - 主动选择: {results[4][1]}")
        print()
        print(f"  YES 数量: {yes_count}/5")
        print()
        
        if yes_count >= 4:
            print("  ✅ 建议执行")
        elif yes_count >= 3:
            print("  ⚠️  需要进一步讨论")
        else:
            print("  ❌ 建议放弃或重新设计")
        
        print()
        print("="*60)
        
        return {
            "decision": decision_desc,
            "results": dict(results),
            "yes_count": yes_count,
            "conclusion": "执行" if yes_count >= 4 else ("讨论" if yes_count >= 3 else "放弃")
        }


def main():
    checker = NorthStarChecker()
    
    if len(sys.argv) < 2:
        # 自动检查
        checker.check_all()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "check":
        checker.check_all()
    
    elif cmd == "star":
        decision = sys.argv[2] if len(sys.argv) > 2 else None
        checker.star_test(decision)
    
    elif cmd == "both":
        checker.check_all()
        print()
        input("按回车键继续 STAR 测试...")
        checker.star_test()
    
    elif cmd in ["help", "--help"]:
        print("""
NEMT NorthStar Code Checker
===========================
Usage: python northstar_checker.py [command]

Commands:
  check    检查代码变更是否对齐北极星
  star     运行 STAR 测试
  both     检查 + STAR 测试
  help     显示帮助

Examples:
  python northstar_checker.py check
  python northstar_checker.py star "重构数据层"
  python northstar_checker.py both
""")


if __name__ == "__main__":
    main()
