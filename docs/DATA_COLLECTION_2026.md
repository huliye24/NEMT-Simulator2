# 比特币数据收集指南

## 概述

本文档定义NEMT项目所需的比特币数据收集方案，服务于建模、回测和策略验证。

---

## 一、数据分组设计

### 1. 高频数据组（短期分析）

| 字段 | 类型 | 用途 | 保留周期 |
|------|------|------|----------|
| `open_time` | datetime | 时间索引 | 永久 |
| `open` | float | 开盘价 | 永久 |
| `high` | float | 最高价 | 永久 |
| `low` | float | 最低价 | 永久 |
| `close` | float | 收盘价 | 永久 |
| `volume` | float | 成交量 | 永久 |
| `quote_volume` | float | 成交额 | 永久 |
| `trades` | int | 成交笔数 | 永久 |
| `taker_buy_volume` | float | 主动买入量 | 永久 |

**采集周期与用途：**

| 周期 | 数据点数(2026全年) | 存储大小 | 适用场景 |
|------|-------------------|---------|---------|
| `1m` | 525,600 | ~50MB | 剥头皮、高频策略研究 |
| `5m` | 105,120 | ~10MB | 日内交易、短期波动 |
| `15m` | 35,040 | ~3MB | 短线策略、进场时机 |

### 2. 中频数据组（策略回测）

| 周期 | 数据点数(2026全年) | 存储大小 | 适用场景 |
|------|-------------------|---------|---------|
| `1h` | 8,760 | ~1MB | 波段策略、趋势跟踪 |
| `4h` | 2,190 | ~250KB | 日内到波段 |
| `1d` | 365 | ~50KB | 中长线策略 |

### 3. 宏观数据组（长期分析）

| 周期 | 数据点数(2026全年) | 存储大小 | 适用场景 |
|------|-------------------|---------|---------|
| `1w` | 52 | ~10KB | 宏观趋势、季节性分析 |
| `1M` | 12 | ~2KB | 长周期规律 |

---

## 二、数据文件结构

```
matlab_data/
├── BTC_1m_2026.mat      # 分钟级（可选存储）
├── BTC_5m_2026.mat      # 5分钟级
├── BTC_15m_2026.mat     # 15分钟级
├── BTC_1h_2026.mat      # 小时级（核心分析用）
├── BTC_4h_2026.mat      # 4小时级
├── BTC_1d_2026.mat      # 日级（长期分析用）
├── BTC_1w_2026.mat      # 周级
└── BTC_1M_2026.mat      # 月级
```

---

## 三、MATLAB数据格式

每个`.mat`文件包含以下字段：

```matlab
% 基本OHLCV数据
timestamp    % datetime数组 (N x 1)
open         % double数组   (N x 1)
high         % double数组   (N x 1)
low          % double数组   (N x 1)
close        % double数组   (N x 1)
volume       % double数组   (N x 1)

% 扩展数据
quote_volume % double数组   (N x 1)  - 成交额(USDT)
trades       % double数组   (N x 1)  - 成交笔数
taker_buy_base  % double数组 (N x 1) - 主动买入基准量

% 元数据
symbol       % char - 'BTCUSDT'
interval     % char - '1h'
start_date   % datetime - 数据起始时间
end_date     % datetime - 数据结束时间
```

---

## 四、Python数据收集脚本

```python
"""
BTC数据收集脚本 - 2026年数据
用于收集并保存为MATLAB兼容格式
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

# 导入binance_fetcher
from binance_fetcher import BinanceFetcher, fetch_by_range, export_as_mat

def collect_2026_data():
    """收集2026年全年数据"""
    
    # 时间范围：2026-01-01 至 2026-04-15（当前）
    start_date = '2026-01-01'
    end_date = '2026-04-15'  # 今天是2026-04-15
    
    # 输出目录
    output_dir = 'matlab_data/2026'
    os.makedirs(output_dir, exist_ok=True)
    
    # 需要收集的周期
    intervals = {
        # 短期分析
        '5m':  '短期波动、剥头皮研究',
        '15m': '短线交易、进场信号',
        
        # 中期分析（核心）
        '1h':  '波段策略、趋势跟踪（核心数据）',
        '4h':  '日内波段、仓位管理',
        '1d':  '中长线策略、趋势确认',
        
        # 长期分析
        '1w':  '宏观趋势、季节性分析',
        '1M':  '长周期规律、年度复盘'
    }
    
    fetcher = BinanceFetcher()
    
    results = {}
    
    print("=" * 60)
    print("开始收集2026年BTC数据")
    print(f"时间范围: {start_date} ~ {end_date}")
    print("=" * 60)
    
    for interval, desc in intervals.items():
        print(f"\n{'─' * 50}")
        print(f"收集 {interval} 数据 - {desc}")
        print(f"{'─' * 50}")
        
        try:
            df = fetcher.fetch_range(
                symbol='BTCUSDT',
                interval=interval,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                # 清理数据
                clean_df = df[['open_time', 'open', 'high', 'low', 'close', 
                               'volume', 'quote_volume', 'trades', 
                               'taker_buy_base', 'taker_buy_quote']].copy()
                
                # 保存CSV
                csv_file = f"{output_dir}/BTC_{interval}_2026.csv"
                clean_df.to_csv(csv_file, index=False)
                print(f"  CSV已保存: {csv_file} ({len(clean_df)}条)")
                
                # 保存MATLAB格式
                mat_file = f"{output_dir}/BTC_{interval}_2026.mat"
                try:
                    import scipy.io as sio
                    mat_data = {
                        'timestamp': clean_df['open_time'].values,
                        'open': clean_df['open'].values.astype(np.float64),
                        'high': clean_df['high'].values.astype(np.float64),
                        'low': clean_df['low'].values.astype(np.float64),
                        'close': clean_df['close'].values.astype(np.float64),
                        'volume': clean_df['volume'].values.astype(np.float64),
                        'quote_volume': clean_df['quote_volume'].values.astype(np.float64),
                        'trades': clean_df['trades'].values.astype(np.float64),
                        'taker_buy_base': clean_df['taker_buy_base'].values.astype(np.float64),
                        'taker_buy_quote': clean_df['taker_buy_quote'].values.astype(np.float64),
                        'symbol': 'BTCUSDT',
                        'interval': interval,
                        'start_date': np.datetime64(start_date),
                        'end_date': np.datetime64(end_date)
                    }
                    sio.savemat(mat_file, mat_data)
                    print(f"  MAT已保存: {mat_file}")
                except ImportError:
                    print("  警告: scipy未安装，仅保存CSV")
                
                results[interval] = clean_df
                
            else:
                print(f"  获取失败")
                
            # 避免API限流
            import time
            time.sleep(0.5)
            
        except Exception as e:
            print(f"  错误: {e}")
    
    # 生成数据摘要
    print("\n" + "=" * 60)
    print("数据收集完成")
    print("=" * 60)
    
    summary_file = f"{output_dir}/data_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"NEMT 2026年BTC数据收集摘要\n")
        f.write(f"收集时间: {datetime.now()}\n")
        f.write(f"数据范围: {start_date} ~ {end_date}\n")
        f.write("=" * 50 + "\n\n")
        
        for interval, df in results.items():
            if df is not None and not df.empty:
                f.write(f"[{interval}]\n")
                f.write(f"  数据点数: {len(df)}\n")
                f.write(f"  时间范围: {df['open_time'].min()} ~ {df['open_time'].max()}\n")
                f.write(f"  价格范围: {df['low'].min():.2f} ~ {df['high'].max():.2f}\n")
                f.write(f"  总成交量: {df['volume'].sum():.2f}\n\n")
    
    print(f"摘要已保存: {summary_file}")
    
    return results


if __name__ == "__main__":
    collect_2026_data()
```

---

## 五、MATLAB加载数据

在MATLAB中加载收集的数据：

```matlab
% 加载1小时数据（核心分析用）
data = load('matlab_data/2026/BTC_1h_2026.mat');

% 提取数据
timestamps = data.timestamp;
close = data.close;
high = data.high;
low = data.low;
open = data.open;
volume = data.volume;

% 查看数据信息
fprintf('数据点数: %d\n', length(close));
fprintf('时间范围: %s ~ %s\n', ...
    datestr(timestamps(1)), datestr(timestamps(end)));

% 绘制K线图
plot(timestamps, close);
```

---

## 六、数据质量检查

收集完成后，执行以下检查：

| 检查项 | 预期结果 |
|--------|---------|
| 数据连续性 | 无缺失K线 |
| 时间戳连续 | 每条间隔一致 |
| 价格有效性 | close在high-low之间 |
| 成交量正常 | volume > 0 |
| 文件完整性 | MAT与CSV同时存在 |

检查脚本：

```python
def validate_data(df, interval):
    """验证数据完整性"""
    issues = []
    
    # 1. 检查缺失值
    if df.isnull().any().any():
        issues.append("存在缺失值")
    
    # 2. 检查价格关系
    invalid_price = (df['close'] > df['high']) | (df['close'] < df['low'])
    if invalid_price.any():
        issues.append("收盘��超出范围")
    
    # 3. 检查零值
    zero_volume = (df['volume'] <= 0).sum()
    if zero_volume > 0:
        issues.append(f"零成交量: {zero_volume}条")
    
    # 4. 检查时间连续性
    time_diff = df['open_time'].diff()
    expected_diff = pd.Timedelta(interval)
    gaps = time_diff[time_diff != expected_diff]
    if len(gaps) > 0:
        issues.append(f"时间不连续: {len(gaps)}处")
    
    return issues
```

---

## 七、数据使用对照表

| 分析目的 | 推荐数据 | 说明 |
|---------|---------|------|
| K线形态识别 | `1h`, `4h` | 主流波段分析 |
| 波动率聚类 | `1h`, `4h` | ARCH效应分析 |
| Hurst指数 | `1h`, `1d` | 长记忆性检测 |
| 多尺度分析 | `5m`, `15m`, `1h`, `4h`, `1d` | 跨周期共振 |
| 趋势跟踪 | `4h`, `1d` | 中长线策略 |
| 日内交易 | `5m`, `15m` | 短线操作 |
| 宏观分析 | `1w`, `1M` | 年度/季度规律 |

---

## 八、注意事项

1. **API限制**：Binance单次最多返回1000条，需要分批获取
2. **存储空间**：1m数据全年约50MB，根据需求选择保留
3. **数据更新**：建议每日运行一次更新最新数据
4. **时区处理**：统一使用UTC时间，避免夏令时问题