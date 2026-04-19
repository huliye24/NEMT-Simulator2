#!/usr/bin/env python3
"""
Generate comparison report between local and cloud benchmarks
"""

import json
import os
from datetime import datetime

# Read results
with open("benchmark_results.json", "r") as f:
    local = json.load(f)

with open("benchmark_cloud_results.json", "r") as f:
    cloud = json.load(f)

# Read system info
local_sys = local['system_info']
cloud_sys = cloud['system_info']

def calc_speedup(local_time, cloud_time):
    """Calculate speedup ratio"""
    if cloud_time <= 0 or local_time <= 0:
        return None
    return local_time / cloud_time

def calc_improvement(local_time, cloud_time):
    """Calculate percentage improvement"""
    if cloud_time <= 0 or local_time <= 0:
        return None
    return ((local_time - cloud_time) / local_time) * 100

# Pre-compute all values
speedup_pi = calc_speedup(local['cpu_pi'], cloud['cpu_pi'])
speedup_sieve = calc_speedup(local['cpu_sieve'], cloud['cpu_sieve'])
speedup_fib = calc_speedup(local['cpu_fibonacci'], cloud['cpu_fibonacci'])
speedup_mem = calc_speedup(local['memory_copy'], cloud['memory_copy'])
speedup_write = calc_speedup(local['file_write'], cloud['file_write'])
speedup_read = calc_speedup(local['file_read'], cloud['file_read'])
speedup_sha = calc_speedup(local['sha256'], cloud['sha256'])
speedup_sort = calc_speedup(local['sort'], cloud['sort'])

improvement_pi = calc_improvement(local['cpu_pi'], cloud['cpu_pi'])
improvement_sieve = calc_improvement(local['cpu_sieve'], cloud['cpu_sieve'])
improvement_fib = calc_improvement(local['cpu_fibonacci'], cloud['cpu_fibonacci'])
improvement_mem = calc_improvement(local['memory_copy'], cloud['memory_copy'])
improvement_write = calc_improvement(local['file_write'], cloud['file_write'])
improvement_read = calc_improvement(local['file_read'], cloud['file_read'])
improvement_sha = calc_improvement(local['sha256'], cloud['sha256'])
improvement_sort = calc_improvement(local['sort'], cloud['sort'])

def fmt_speedup(val):
    if val is None: return "N/A"
    return f"{val:.2f}x"

def fmt_pct(val):
    if val is None: return "N/A"
    return f"{val:.1f}%"

def fmt_time(val):
    if val is None or val < 0: return "N/A"
    return f"{val:.4f}秒"

# Calculate averages
tests = ['cpu_pi', 'cpu_sieve', 'cpu_fibonacci', 'memory_copy', 'file_write', 'file_read', 'sha256', 'sort']
speedups = [calc_speedup(local[t], cloud[t]) for t in tests if cloud[t] > 0 and local[t] > 0]
avg_speedup = sum(speedups) / len(speedups) if speedups else 0

avg_improvements = [calc_improvement(local[t], cloud[t]) for t in tests if cloud[t] > 0 and local[t] > 0]
avg_improvement = sum(avg_improvements) / len(avg_improvements) if avg_improvements else 0

# Memory info
local_mem = local_sys.get('memory_total_gb', 0)
cloud_mem = cloud_sys.get('memory_total_gb', 0)
local_cpu = local_sys.get('cpu_count', 0)
cloud_cpu = cloud_sys.get('cpu_count', 0)

# Generate markdown report
report = f"""# 云服务器性能测评报告

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 一、测试环境

### 1.1 本地电脑配置

| 项目 | 参数 |
|------|------|
| 操作系统 | {local_sys.get('platform', 'Unknown')} |
| 处理器 | {local_sys.get('processor', 'Unknown')} |
| CPU核心数 | {local_cpu} 核 |
| 内存总量 | {local_mem:.1f} GB |
| Python版本 | {local_sys.get('python_version', 'Unknown').split()[0]} |

### 1.2 云服务器配置

| 项目 | 参数 |
|------|------|
| 操作系统 | {cloud_sys.get('platform', 'Unknown')} Linux |
| 处理器 | {cloud_sys.get('processor', 'Unknown')} |
| CPU核心数 | {cloud_cpu} 核 |
| 内存总量 | {cloud_mem:.1f} GB |
| Python版本 | {cloud_sys.get('python_version', 'Unknown').split()[0]} |

### 1.3 配置对比

| 资源 | 本地电脑 | 云服务器 | 对比 |
|------|----------|---------|------|
| CPU核心数 | {local_cpu} 核 | {cloud_cpu} 核 | 云服务器多 {cloud_cpu - local_cpu} 核 |
| 内存 | {local_mem:.1f} GB | {cloud_mem:.1f} GB | 云服务器多 {cloud_mem - local_mem:.1f} GB |

---

## 二、基准测试结果

### 2.1 CPU 性能测试

#### PI 计算测试 (10000次迭代)

| 指标 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 耗时 | {fmt_time(local['cpu_pi'])} | {fmt_time(cloud['cpu_pi'])} | **{fmt_speedup(speedup_pi)}** | {fmt_pct(improvement_pi)} |

#### 质数筛选测试 (Eratosthenes筛法, n=100000)

| 指标 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 耗时 | {fmt_time(local['cpu_sieve'])} | {fmt_time(cloud['cpu_sieve'])} | **{fmt_speedup(speedup_sieve)}** | {fmt_pct(improvement_sieve)} |

#### 斐波那契数列测试 (n=30)

| 指标 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 耗时 | {fmt_time(local['cpu_fibonacci'])} | {fmt_time(cloud['cpu_fibonacci'])} | **{fmt_speedup(speedup_fib)}** | {fmt_pct(improvement_fib)} |

### 2.2 内存性能测试

#### 内存拷贝测试 (100MB)

| 指标 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 耗时 | {fmt_time(local['memory_copy'])} | {fmt_time(cloud['memory_copy'])} | **{fmt_speedup(speedup_mem)}** | {fmt_pct(improvement_mem)} |

### 2.3 文件I/O测试 (10MB)

| 操作 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 写入 | {fmt_time(local['file_write'])} | {fmt_time(cloud['file_write'])} | **{fmt_speedup(speedup_write)}** | {fmt_pct(improvement_write)} |
| 读取 | {fmt_time(local['file_read'])} | {fmt_time(cloud['file_read'])} | **{fmt_speedup(speedup_read)}** | {fmt_pct(improvement_read)} |

### 2.4 加密哈希测试 (SHA256, 10MB x 10次)

| 指标 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 耗时 | {fmt_time(local['sha256'])} | {fmt_time(cloud['sha256'])} | **{fmt_speedup(speedup_sha)}** | {fmt_pct(improvement_sha)} |

### 2.5 排序测试 (100000个元素)

| 指标 | 本地电脑 | 云服务器 | 提速倍数 | 提升幅度 |
|------|----------|---------|----------|----------|
| 耗时 | {fmt_time(local['sort'])} | {fmt_time(cloud['sort'])} | **{fmt_speedup(speedup_sort)}** | {fmt_pct(improvement_sort)} |

---

## 三、综合性能对比

### 3.1 测试项目汇总

| 测试项目 | 本地耗时 | 云服务器耗时 | 提速倍数 | 评价 |
|----------|----------|-------------|----------|------|
| CPU PI计算 | {fmt_time(local['cpu_pi'])} | {fmt_time(cloud['cpu_pi'])} | {fmt_speedup(speedup_pi)} | {'显著更快' if speedup_pi and speedup_pi > 1.5 else '相当'} |
| 质数筛选 | {fmt_time(local['cpu_sieve'])} | {fmt_time(cloud['cpu_sieve'])} | {fmt_speedup(speedup_sieve)} | {'显著更快' if speedup_sieve and speedup_sieve > 1.5 else '相当'} |
| 斐波那契 | {fmt_time(local['cpu_fibonacci'])} | {fmt_time(cloud['cpu_fibonacci'])} | {fmt_speedup(speedup_fib)} | {'显著更快' if speedup_fib and speedup_fib > 1.5 else '相当'} |
| 内存拷贝 | {fmt_time(local['memory_copy'])} | {fmt_time(cloud['memory_copy'])} | {fmt_speedup(speedup_mem)} | {'显著更快' if speedup_mem and speedup_mem > 1.5 else '相当'} |
| 文件写入 | {fmt_time(local['file_write'])} | {fmt_time(cloud['file_write'])} | {fmt_speedup(speedup_write)} | {'显著更快' if speedup_write and speedup_write > 1.5 else '相当'} |
| 文件读取 | {fmt_time(local['file_read'])} | {fmt_time(cloud['file_read'])} | {fmt_speedup(speedup_read)} | {'显著更快' if speedup_read and speedup_read > 1.5 else '相当'} |
| SHA256哈希 | {fmt_time(local['sha256'])} | {fmt_time(cloud['sha256'])} | {fmt_speedup(speedup_sha)} | {'显著更快' if speedup_sha and speedup_sha > 1.5 else '相当'} |
| 排序算法 | {fmt_time(local['sort'])} | {fmt_time(cloud['sort'])} | {fmt_speedup(speedup_sort)} | {'显著更快' if speedup_sort and speedup_sort > 1.5 else '相当'} |

### 3.2 综合评分

**平均提速倍数: {avg_speedup:.2f}x**
**平均性能提升: {avg_improvement:.1f}%**

---

## 四、结论与建议

### 4.1 测试结论

根据本次基准测试，得出以下结论：

1. **CPU性能**: 云服务器的{cloud_cpu}核CPU在并行计算任务上表现更优
2. **内存性能**: 云服务器拥有{cloud_mem:.1f}GB大内存，避免本地电脑的内存压力
3. **整体速度**: 云服务器平均提速 **{avg_speedup:.2f}倍**，性能提升 **{avg_improvement:.1f}%**

### 4.2 使用建议

| 使用场景 | 建议 |
|----------|------|
| 大型代码编译 | 推荐使用云服务器 |
| Python数据分析 | 推荐使用云服务器 |
| 前端开发 | 本地即可 |
| 小型脚本运行 | 本地即可 |
| 机器学习训练 | 强烈推荐使用云服务器 |
| 实时交易策略回测 | 推荐使用云服务器 |

### 4.3 注意事项

1. 网络延迟会影响云服务器的使用体验
2. 建议在网络稳定的环境下使用远程开发
3. 定期保存代码，避免数据丢失

---

## 五、附录

### 5.1 测试方法

- 测试脚本: benchmark.py
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 测试项目: 8项基准测试

### 5.2 云服务器信息

- IP地址: 42.51.42.123
- SSH端口: 22
- 用户名: root

---

> 本报告由 NEMT 量化系统自动生成
"""

# Save report
with open("云服务器测评报告.md", "w", encoding="utf-8") as f:
    f.write(report)

print("=" * 60)
print("Report Generated: 云服务器测评报告.md")
print("=" * 60)
print()
print("Summary:")
print(f"  Average Speedup: {avg_speedup:.2f}x")
print(f"  Average Improvement: {avg_improvement:.1f}%")
print()
print("Detailed Results:")
print(f"  CPU PI Calculation: {fmt_speedup(speedup_pi)} faster")
print(f"  Prime Sieve: {fmt_speedup(speedup_sieve)} faster")
print(f"  Fibonacci: {fmt_speedup(speedup_fib)} faster")
print(f"  Memory Copy: {fmt_speedup(speedup_mem)} faster")
print(f"  File Write: {fmt_speedup(speedup_write)} faster")
print(f"  File Read: {fmt_speedup(speedup_read)} faster")
print(f"  SHA256 Hash: {fmt_speedup(speedup_sha)} faster")
print(f"  Sorting: {fmt_speedup(speedup_sort)} faster")
