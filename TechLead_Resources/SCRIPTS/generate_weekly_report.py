#!/usr/bin/env python3
"""
生成每周开发报告
聚合 GitHub PR 统计、代码覆盖率等数据
"""

import os
import json
from datetime import datetime, timedelta


def get_git_stats(days: int = 7) -> dict:
    """获取 Git 统计"""
    try:
        import subprocess
        
        # 获取本周 commit 数量
        since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        result = subprocess.run(
            ['git', 'log', f'--since={since}', '--oneline', '--format=%h'],
            capture_output=True,
            text=True,
            check=True
        )
        commits = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        
        # 获取新增行数
        result = subprocess.run(
            ['git', 'diff', '--shortstat', f'HEAD@{yesterday}'.format(yesterday=days), 'HEAD'],
            capture_output=True,
            text=True,
            check=False
        )
        
        return {
            'commits': commits,
            'period_days': days
        }
    except Exception as e:
        return {'commits': 0, 'error': str(e)}


def get_test_coverage() -> dict:
    """获取测试覆盖率"""
    # 如果有 coverage.json 报告，读取它
    coverage_file = 'coverage/coverage.json'
    
    if os.path.exists(coverage_file):
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)
                return {
                    'total_coverage': data.get('totals', {}).get('percent_covered', 0)
                }
        except:
            pass
    
    return {'total_coverage': 0}


def generate_weekly_report() -> str:
    """生成周报"""
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    report = f"""# 每周开发报告 - {week_start.strftime('%Y-%m-%d')} 至 {week_end.strftime('%Y-%m-%d')}

> 生成时间: {today.strftime('%Y-%m-%d %H:%M')}

## 一、Git 统计

"""
    
    # Git 统计
    git_stats = get_git_stats(7)
    report += f"| 指标 | 数值 |\n|------|------|\n"
    report += f"| 本周 Commit 数 | {git_stats.get('commits', 0)} |\n"
    report += f"| 统计周期 | 7 天 |\n\n"
    
    # 测试覆盖率
    coverage = get_test_coverage()
    report += f"""## 二、测试覆盖率

| 模块 | 覆盖率 |
|------|--------|
| 整体 | {coverage.get('total_coverage', 0):.1f}% |

## 三、本周完成

(待填写)

## 四、阻塞项

(待填写)

## 五、下周计划

(待填写)

---

*由 TechLead Agent 自动生成*
"""
    
    return report


def save_report(report: str, filename: str = None):
    """保存报告"""
    if filename is None:
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"Weekly_Report_{today}.md"
    
    output_path = f"TechLead_Resources/{filename}"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存: {output_path}")
    return output_path


def main():
    print("📊 生成每周开发报告...\n")
    
    report = generate_weekly_report()
    print(report)
    
    # 保存报告
    save_report(report)
    
    return report


if __name__ == "__main__":
    main()
