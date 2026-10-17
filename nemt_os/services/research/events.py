"""实验事件检测 (canonical)。

第四阶段命题（固定，不得在实验中途改写）:

    「当 BTC 市场进入低谱宽、波动收缩且 DCI 开始上升的临界状态后，
      未来 24、48、72 小时发生趋势扩张的概率显著高于随机时点和
      简单波动率收缩基准。」

本模块只负责**事件的客观定义与检测**，不做任何结论判断。
结论由 stats.py 的统计检验给出，且必须如实报告（包括"不支持"）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence

from .candles import CandleSeries
from .variables import NEMTState


# ---------------------------------------------------------------- 事件配置


@dataclass
class EventConfig:
    """临界事件判定配置。

    **所有阈值必须来自配置**，不得散落硬编码。
    这些阈值只允许在**训练集**上选择，测试集不得参与（见 validation.py）。
    """

    # 条件①：谱宽处于滚动历史低分位
    sw_percentile_max: float = 0.20

    # 条件②：波动收缩（布林带宽度低分位 或 已实现波动率低分位）
    vol_percentile_max: float = 0.20
    vol_condition_mode: str = "both"      # both | bbw | rvol | either

    # 条件③：DCI 从低位转为上升
    dci_low_max: float = 0.62             # 「低位」上界
    dci_slope_min: float = 0.0            # 斜率必须为正

    # 冷却期：同一事件簇内只取首次触发，避免样本自相关膨胀
    cooldown_bars: int = 12

    # 结果 horizons（小时）
    horizons: tuple = (24, 48, 72)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["horizons"] = list(self.horizons)
        return d


@dataclass
class RegimeConfig:
    """牛/熊/震荡分组配置。"""

    ma_window: int = 720          # 30 天均线
    slope_window: int = 168       # 判断均线方向的回看窗
    slope_eps: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- 事件检测


def detect_critical_events(
    states: Sequence[NEMTState],
    cfg: Optional[EventConfig] = None,
) -> List[int]:
    """检测临界事件，返回触发的 bar 索引列表（升序）。

    判定条件（三者同时成立）:
        ① sw_percentile <= sw_percentile_max
        ② 波动收缩条件成立（按 vol_condition_mode）
        ③ dci 不为空 且 dci <= dci_low_max 且 dci_slope > dci_slope_min

    任一输入为 None（数据不足）则**该 bar 不触发**，不做默认填充。
    """
    cfg = cfg or EventConfig()
    events: List[int] = []
    last_event: Optional[int] = None

    for i, st in enumerate(states):
        if st.sw_percentile is None or st.dci is None or st.dci_slope is None:
            continue

        c1 = st.sw_percentile <= cfg.sw_percentile_max

        bbw_ok = st.bbw_percentile is not None and st.bbw_percentile <= cfg.vol_percentile_max
        rvol_ok = st.rvol_percentile is not None and st.rvol_percentile <= cfg.vol_percentile_max
        mode = cfg.vol_condition_mode
        if mode == "both":
            c2 = bool(bbw_ok and rvol_ok)
        elif mode == "bbw":
            c2 = bool(bbw_ok)
        elif mode == "rvol":
            c2 = bool(rvol_ok)
        elif mode == "either":
            c2 = bool(bbw_ok or rvol_ok)
        else:
            raise ValueError(f"未知 vol_condition_mode: {mode!r}")

        c3 = (st.dci <= cfg.dci_low_max) and (st.dci_slope > cfg.dci_slope_min)

        if not (c1 and c2 and c3):
            continue

        if last_event is not None and (i - last_event) < cfg.cooldown_bars:
            continue

        events.append(i)
        last_event = i

    return events


def detect_bbw_contraction_events(
    states: Sequence[NEMTState],
    percentile_max: float = 0.20,
    cooldown_bars: int = 12,
) -> List[int]:
    """对照组：单独的布林带宽度收缩（不含谱宽与 DCI 条件）。

    这是命题中明确要求的「简单波动率收缩基准」。
    """
    events: List[int] = []
    last: Optional[int] = None
    for i, st in enumerate(states):
        if st.bbw_percentile is None:
            continue
        if st.bbw_percentile > percentile_max:
            continue
        if last is not None and (i - last) < cooldown_bars:
            continue
        events.append(i)
        last = i
    return events


# ---------------------------------------------------------------- 市场状态分组


def classify_regimes(series: CandleSeries, cfg: Optional[RegimeConfig] = None) -> List[str]:
    """把每根 K 线划分为 bull / bear / sideways / unknown。

    只用**当前及过去**数据：均线取 t-W+1..t，方向用均线自身的回看斜率。
    """
    cfg = cfg or RegimeConfig()
    closes = series.closes
    n = len(closes)
    out: List[str] = ["unknown"] * n

    ma: List[Optional[float]] = [None] * n
    s = 0.0
    for i, v in enumerate(closes):
        s += v
        if i >= cfg.ma_window:
            s -= closes[i - cfg.ma_window]
        if i >= cfg.ma_window - 1:
            ma[i] = s / cfg.ma_window

    for i in range(n):
        if ma[i] is None:
            continue
        j = i - cfg.slope_window + 1
        if j < 0:
            continue
        seg = ma[j: i + 1]
        if any(v is None for v in seg) or len(seg) < 2:
            continue
        slope = seg[-1] - seg[0]
        above = closes[i] > ma[i]
        if slope > cfg.slope_eps and above:
            out[i] = "bull"
        elif slope < -cfg.slope_eps and not above:
            out[i] = "bear"
        else:
            out[i] = "sideways"
    return out


# ---------------------------------------------------------------- 结果变量


def _max_over(series: CandleSeries, i: int, h: int, field: str) -> Optional[float]:
    end = min(i + h + 1, len(series))
    if i + 1 >= end:
        return None
    vals = getattr(series, field)[i + 1: end]
    return max(vals) if vals else None


def compute_outcomes(
    series: CandleSeries,
    index: int,
    horizon: int,
) -> Optional[Dict[str, float]]:
    """计算单个时点在未来 horizon 根 K 线上的结果变量。

    返回 None 表示未来数据不足（例如序列末尾），该样本不参与统计。

    字段:
        fwd_return      未来收益（相对当前 close）
        fwd_abs_return  未来绝对收益
        mfe             最大有利变动（相对当前 close，按 high）
        mae             最大不利变动（相对当前 close，按 low）
        fwd_rvol        未来已实现波动率（对数收益标准差，未年化）
        trend_duration  趋势持续根数（自 t+1 起价格相对 close[t] 符号保持不变的最长长度）
    """
    n = len(series)
    end = index + horizon
    if end >= n:
        return None

    c0 = series.closes[index]
    if c0 <= 0:
        return None

    closes = series.closes
    highs = series.highs
    lows = series.lows

    seg_h = highs[index + 1: end + 1]
    seg_l = lows[index + 1: end + 1]
    if not seg_h or not seg_l:
        return None

    c_end = closes[end]
    fwd_return = (c_end - c0) / c0
    mfe = (max(seg_h) - c0) / c0
    mae = (min(seg_l) - c0) / c0

    # 未来已实现波动率
    rets: List[float] = []
    for k in range(index + 1, end + 1):
        p0, p1 = closes[k - 1], closes[k]
        if p0 > 0 and p1 > 0:
            rets.append(math.log(p1 / p0))
    if len(rets) >= 2:
        m = sum(rets) / len(rets)
        fwd_rvol = math.sqrt(sum((v - m) ** 2 for v in rets) / (len(rets) - 1))
    elif len(rets) == 1:
        fwd_rvol = abs(rets[0])
    else:
        fwd_rvol = 0.0

    # 趋势持续时间
    if len(closes) <= index + 1:
        return None
    first_sign = 1 if closes[index + 1] > c0 else (-1 if closes[index + 1] < c0 else 0)
    duration = 0
    if first_sign == 0:
        duration = 0
    else:
        for k in range(index + 1, end + 1):
            diff = closes[k] - c0
            sgn = 1 if diff > 0 else (-1 if diff < 0 else 0)
            if sgn == first_sign:
                duration += 1
            else:
                break

    return {
        "fwd_return": fwd_return,
        "fwd_abs_return": abs(fwd_return),
        "mfe": mfe,
        "mae": mae,
        "fwd_rvol": fwd_rvol,
        "trend_duration": float(duration),
    }


def sample_random_indices(
    n_total: int,
    n_samples: int,
    seed: int = 20240101,
    min_index: int = 0,
    max_index: Optional[int] = None,
    exclude: Optional[Sequence[int]] = None,
) -> List[int]:
    """随机时点对照组。使用固定种子，保证可复现。"""
    import random

    if max_index is None:
        max_index = n_total - 1
    rng = random.Random(seed)
    excl = set(exclude or [])
    pool = [i for i in range(min_index, min(max_index, n_total - 1) + 1) if i not in excl]
    if not pool or n_samples <= 0:
        return []
    if n_samples >= len(pool):
        return sorted(pool)
    return sorted(rng.sample(pool, n_samples))
