#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NEMT NorthStar Code Checker - Optimized Version
排除 node_modules，只检查真实项目代码
"""
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set

PROJECT_ROOT = Path(__file__).parent.parent

# 北极星定义
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
            "keywords": [
                "backtest", "回测", "strategy", "策略", "signal", "信号", 
                "market", "market", "kline", "蜡烛图", "indicator", "指标",
                "rsi", "macd", "bollinger", "均线", "趋势"
            ],
            "paths": ["backtest", "strategy", "signal", "market", "engine"]
        },
        "B": {
            "name": "策略淘汰机制",
            "kpis": ["胜率<40%自动淘汰", "淘汰准确率>70%"],
            "keywords": [
                "eliminate", "淘汰", "filter", "过滤", "selection", "选择",
                "evolve", "进化", "survival", "生存", "fitness", "适应度",
                "crossover", "交叉", "mutation", "变异"
            ],
            "paths": ["evolution", "selection", "eliminate", "genetic", "fitness"]
        },
        "C": {
            "name": "大脑层动态权重分配",
            "kpis": ["夏普比率>1.5", "权重调整响应<5分钟"],
            "keywords": [
                "brain", "大脑", "weight", "权重", "dynamic", "动态",
                "adjust", "调整", "balance", "平衡", "neural", "神经",
                "gradient", "梯度", "allocation", "分配"
            ],
            "paths": ["brain", "weight", "dynamic", "neural", "gradient"]
        },
        "D": {
            "name": "实盘接入",
            "kpis": ["日交易量>100笔", "执行延迟<100ms"],
            "keywords": [
                "live", "实盘", "trade", "交易", "execute", "执行",
                "order", "订单", "broker", "券商", "exchange", "交易所",
                "position", "仓位", "fill", "成交"
            ],
            "paths": ["trading", "execution", "order", "live", "broker", "exchange"]
        }
    }
}


class NorthStarChecker:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.changed_files = []
        self.aligned_files = []
        self.unaligned_files = []
        self.alignment_score = 0
        self.suggestions = []
        
        # 排除的目录
        self.exclude_dirs = {
            'node_modules', '.git', '__pycache__', '.venv', 'venv',
            'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache',
            'bin', 'obj', '.idea', '.vscode', '.cursor'
        }
        
        # 排除的文件扩展名
        self.exclude_extensions = {
            '.min.js', '.min.css', '.map', '.lock', '.pem', '.key',
            '.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff',
            '.woff2', '.ttf', '.eot'
        }
        
        # 架构规则
        self.architecture_rules = {
            'core': {
                'exclude': ['<div>', '<span>', 'render', 'html(', 'className'],
                'message': 'core 层不应有 UI 代码'
            },
            'backend': {
                'exclude': ['DOM', 'document.', 'window.'],
                'message': 'backend 不应有 DOM 操作'
            },
            'frontend': {
                'exclude': ['sql.', 'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE '],
                'message': 'frontend 不应有 SQL 操作'
            }
        }
    
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
            
            # 过滤
            valid_files = []
            for f in files:
                if not f:
                    continue
                    
                # 检查是否在排除目录
                path_parts = f.replace('\\', '/').split('/')
                if any(excluded in path_parts for excluded in self.exclude_dirs):
                    continue
                
                # 检查扩展名
                if any(f.endswith(ext) for ext in self.exclude_extensions):
                    continue
                
                # 只保留代码文件
                valid_exts = ['.py', '.go', '.ts', '.tsx', '.js', '.jsx', '.java', '.rs', '.cpp', '.c', '.h']
                if any(f.endswith(ext) for ext in valid_exts):
                    valid_files.append(f)
            
            return valid_files
            
        except Exception as e:
            print(f"[WARN] Failed to get git changes: {e}")
            return []
    
    def analyze_file(self, file_path: str) -> Dict:
        """分析单个文件"""
        result = {
            "file": file_path,
            "constellation": None,
            "constellation_name": None,
            "alignment_score": 0,
            "matches": [],
            "issues": [],
            "recommendations": []
        }
        
        try:
            full_path = self.project_root / file_path
            if not full_path.exists():
                return result
            
            content = full_path.read_text(encoding='utf-8', errors='ignore').lower()
            filename_lower = file_path.replace('\\', '/').lower()
            
            best_score = 0
            best_constellation = None
            best_matches = []
            
            # 检查与星座的关联
            for constellation_id, const_info in NORTHSTAR["constellations"].items():
                score = 0
                matches = []
                
                # 检查路径
                for path_kw in const_info.get("paths", []):
                    if path_kw.lower() in filename_lower:
                        score += 3
                        matches.append(f"路径含 '{path_kw}'")
                
                # 检查文件名
                for kw in const_info["keywords"][:10]:  # 限制关键词数量
                    if kw.lower() in filename_lower:
                        score += 2
                        matches.append(f"文件名 '{kw}'")
                
                # 检查文件内容
                for kw in const_info["keywords"][:15]:
                    if kw.lower() in content:
                        score += 1
                        if kw not in matches:
                            matches.append(f"内容 '{kw}'")
                
                if score > best_score:
                    best_score = score
                    best_constellation = constellation_id
                    best_constellation_name = const_info['name']
                    best_matches = matches[:5]  # 只保留前5个匹配
            
            if best_score > 0:
                result["constellation"] = best_constellation
                result["constellation_name"] = best_constellation_name
                result["alignment_score"] = best_score
                result["matches"] = best_matches
            
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
        path_lower = file_path.replace('\\', '/').lower()
        
        # core 层检查
        if '/core/' in path_lower or '\\core\\' in path_lower:
            for kw in self.architecture_rules['core']['exclude']:
                if kw.lower() in content:
                    issues.append(f"[架构] {self.architecture_rules['core']['message']} (发现 '{kw}')")
                    break
        
        # backend 检查
        if any(x in path_lower for x in ['/server/', '/backend/', '/api/', '/service/']):
            for kw in self.architecture_rules['backend']['exclude']:
                if kw.lower() in content:
                    issues.append(f"[架构] {self.architecture_rules['backend']['message']} (发现 '{kw}')")
                    break
        
        return issues
    
    def check_all(self) -> Dict:
        """检查所有变更"""
        print()
        print("=" * 60)
        print("   [NORTHSTAR] 北极星代码检查器 v2.0")
        print("=" * 60)
        print()
        
        # 获取变更
        self.changed_files = self.get_git_changes()
        
        if not self.changed_files:
            print("[INFO] 没有检测到代码变更")
            return {"status": "no_changes"}
        
        print(f"[INFO] 检测到 {len(self.changed_files)} 个有效代码文件")
        print()
        
        # 分析每个文件
        results = []
        constellation_counts = {k: 0 for k in NORTHSTAR["constellations"].keys()}
        
        for file_path in self.changed_files:
            result = self.analyze_file(file_path)
            results.append(result)
            
            if result["constellation"]:
                self.aligned_files.append(result)
                constellation_counts[result["constellation"]] += 1
            else:
                self.unaligned_files.append(result)
        
        # 计算整体对齐度
        alignment_rate = (len(self.aligned_files) / len(self.changed_files)) * 100 if self.changed_files else 0
        
        # 构建报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_files": len(self.changed_files),
            "aligned_files": len(self.aligned_files),
            "unaligned_files": len(self.unaligned_files),
            "alignment_rate": alignment_rate,
            "constellation_counts": constellation_counts,
            "file_results": results,
            "northstar": NORTHSTAR["statement"]
        }
        
        # 显示结果
        self._print_results(report)
        
        return report
    
    def _print_results(self, report: Dict):
        """打印结果"""
        print("-" * 60)
        print("  [STAT] 统计概览")
        print("-" * 60)
        print()
        print(f"  北极星: {report['northstar']}")
        print()
        print(f"  总文件数: {report['total_files']}")
        print(f"  对齐文件: {report['aligned_files']} ({report['alignment_rate']:.1f}%)")
        print(f"  未对齐文件: {report['unaligned_files']}")
        print()
        
        # 星座分布
        print("-" * 60)
        print("  [CONSTELLATION] 星座分布")
        print("-" * 60)
        print()
        
        for cid, count in report['constellation_counts'].items():
            const_info = NORTHSTAR["constellations"][cid]
            pct = (count / report['aligned_files'] * 100) if report['aligned_files'] > 0 else 0
            bar_count = int(pct / 5)
            bar = "#" * bar_count + "-" * (20 - bar_count)
            print(f"  星座 {cid}: {const_info['name']}")
            print(f"    [{bar}] {count} 文件 ({pct:.1f}%)")
            print()
        
        # 架构问题
        all_issues = set()
        for r in report["file_results"]:
            for issue in r.get("issues", []):
                all_issues.add(issue)
        
        if all_issues:
            print("-" * 60)
            print("  [ARCH] 架构问题")
            print("-" * 60)
            print()
            for issue in sorted(all_issues):
                print(f"    {issue}")
            print()
        
        # 未对齐文件详情
        if self.unaligned_files:
            print("-" * 60)
            print("  [REVIEW] 未对齐文件 (需要重新评估)")
            print("-" * 60)
            print()
            
            # 按目录分组
            by_dir = {}
            for r in self.unaligned_files[:50]:  # 只显示前50个
                dir_name = str(Path(r["file"]).parent)
                if dir_name not in by_dir:
                    by_dir[dir_name] = []
                by_dir[dir_name].append(r["file"])
            
            for dir_name, files in sorted(by_dir.items()):
                print(f"  目录: {dir_name}/")
                for f in files[:5]:  # 每个目录最多显示5个
                    print(f"    - {Path(f).name}")
                if len(files) > 5:
                    print(f"    ... 还有 {len(files) - 5} 个文件")
                print()
            
            if len(self.unaligned_files) > 50:
                print(f"  ... 还有 {len(self.unaligned_files) - 50} 个文件")
                print()
        
        # 给出建议
        print("-" * 60)
        print("  [RECOMMENDATION] 北极星建议")
        print("-" * 60)
        print()
        
        if report['alignment_rate'] >= 80:
            print("  [OK] 非常好！代码高度对齐北极星")
            print("  继续聚焦核心星座目标")
        elif report['alignment_rate'] >= 50:
            print("  [WARN] 不错，但有改进空间")
            print("  建议：优先处理与星座相关的文件")
        elif report['alignment_rate'] > 0:
            print("  [FAIL] 对齐度较低")
            print("  建议：")
            print("    1. 检查未对齐文件的必要性")
            print("    2. 考虑将这些文件移到正确目录")
            print("    3. 如果是基础设施，可能需要更新关键词")
        else:
            print("  [FAIL][FAIL] 严重偏离！")
            print("  建议：在提交之前进行 STAR 测试")
            print()
            print("  请先问自己：")
            print("    1. 这些变更为什么做？")
            print("    2. 它们对哪个星座有贡献？")
            print("    3. 不做会怎样？")
        
        print()
        print("=" * 60)


def main():
    checker = NorthStarChecker()
    
    if len(sys.argv) < 2:
        checker.check_all()
        return
    
    cmd = sys.argv[1].lower()
    
    if cmd == "check":
        checker.check_all()
    elif cmd == "star":
        print("STAR test not yet implemented in v2.0")
    elif cmd in ["help", "--help"]:
        print("""
NEMT NorthStar Code Checker v2.0
===============================
Usage: python northstar_checker_v2.py [command]

Commands:
  check    检查代码变更是否对齐北极星
  help     显示帮助
""")


if __name__ == "__main__":
    main()
