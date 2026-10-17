"""统计验证工具 (canonical)。

纪律:
    - 结论只能由统计量给出，**禁止用图形印象代替统计结果**
    - 必须报告置信区间，禁止只报点估计
    - 必须给出「支持 / 部分支持 / 不支持」的明确判定
    - 禁止只展示成功案例
    - bootstrap 使用固定种子，保证可复现
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Sequence


@dataclass
class StatConfig:
    n_bootstrap: int = 2000
    ci_alpha: float = 0.05          # 95% 置信区间
    seed: int = 20240101
    min_samples: int = 30           # 低于此样本量不得下结论

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- 描述统计


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def median(xs: Sequence[float]) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def stdev(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    m = sum(xs) / n
    return math.sqrt(sum((v - m) ** 2 for v in xs) / (n - 1))


def win_rate(xs: Sequence[float]) -> float:
    """正值占比。"""
    if not xs:
        return float("nan")
    return sum(1 for v in xs if v > 0) / len(xs)


def bootstrap_ci(
    xs: Sequence[float],
    statistic=mean,
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 20240101,
) -> tuple:
    """对给定统计量做 bootstrap，返回 (low, high)。

    样本量不足 (< 2) 返回 (nan, nan)，由调用方决定是否下结论。
    """
    n = len(xs)
    if n < 2:
        return (float("nan"), float("nan"))
    rng = random.Random(seed)
    vals: List[float] = []
    for _ in range(n_boot):
        sample = [xs[rng.randrange(n)] for _ in range(n)]
        vals.append(statistic(sample))
    vals.sort()
    lo_pos = int(math.floor((alpha / 2) * (n_boot - 1)))
    hi_pos = int(math.ceil((1 - alpha / 2) * (n_boot - 1)))
    return (vals[lo_pos], vals[hi_pos])


def describe(
    xs: Sequence[float],
    cfg: Optional[StatConfig] = None,
    label: str = "",
    win_definition: str = "positive",
) -> Dict[str, float]:
    """一组样本的完整描述统计。"""
    cfg = cfg or StatConfig()
    n = len(xs)
    d: Dict[str, float] = {
        "label": label,
        "n": float(n),
        "mean": mean(xs) if n else float("nan"),
        "median": median(xs) if n else float("nan"),
        "stdev": stdev(xs) if n > 1 else float("nan"),
        "win_rate": win_rate(xs) if n else float("nan"),
    }
    if n >= 2:
        lo, hi = bootstrap_ci(xs, mean, cfg.n_bootstrap, cfg.ci_alpha, cfg.seed)
        d["ci_low"] = lo
        d["ci_high"] = hi
    else:
        d["ci_low"] = float("nan")
        d["ci_high"] = float("nan")
    return d


# ---------------------------------------------------------------- 组间比较


def bootstrap_diff_ci(
    a: Sequence[float],
    b: Sequence[float],
    n_boot: int = 2000,
    alpha: float = 0.05,
    seed: int = 20240101,
) -> tuple:
    """两组均值之差 (mean(a) - mean(b)) 的 bootstrap 置信区间。"""
    if len(a) < 2 or len(b) < 2:
        return (float("nan"), float("nan"), float("nan"))
    rng = random.Random(seed)
    diffs: List[float] = []
    for _ in range(n_boot):
        sa = [a[rng.randrange(len(a))] for _ in range(len(a))]
        sb = [b[rng.randrange(len(b))] for _ in range(len(b))]
        diffs.append(mean(sa) - mean(sb))
    diffs.sort()
    lo = diffs[int(math.floor((alpha / 2) * (n_boot - 1)))]
    hi = diffs[int(math.ceil((1 - alpha / 2) * (n_boot - 1)))]
    obs = mean(a) - mean(b)
    # 双尾 bootstrap p 值：把 bootstrap 分布平移到"零假设为 0"的位置，
    # 统计抽样差异达到或超过观测值的比例。
    centered = [d - obs for d in diffs]
    extreme = sum(1 for d in centered if abs(d) >= abs(obs))
    p_value = (extreme + 1) / (n_boot + 1)
    return (obs, lo, hi, min(p_value, 1.0))


def compare_to_control(
    event_vals: Sequence[float],
    control_vals: Sequence[float],
    cfg: Optional[StatConfig] = None,
) -> Dict[str, float]:
    """事件组 vs 对照组，给出差值、置信区间与判定。

    判定规则（明确、不得事后修改）:
        - 差值 CI 完全 > 0  且 p < 0.05  → "显著优于对照"
        - 差值点估计 > 0 但 CI 含 0      → "方向一致但不显著"
        - 差值 CI 完全 < 0              → "显著劣于对照"
        - 样本量不足                     → "样本不足，不判定"
    """
    cfg = cfg or StatConfig()
    out: Dict[str, float] = {
        "event_n": float(len(event_vals)),
        "control_n": float(len(control_vals)),
    }
    if len(event_vals) < 2 or len(control_vals) < 2:
        out["verdict"] = float("nan")
        out["verdict_text"] = "样本不足，不判定"
        return out

    obs, lo, hi, p_value = bootstrap_diff_ci(
        event_vals, control_vals, cfg.n_bootstrap, cfg.ci_alpha, cfg.seed
    )
    out["diff"] = obs
    out["diff_ci_low"] = lo
    out["diff_ci_high"] = hi
    out["p_value"] = p_value
    cm = mean(control_vals)
    out["lift_pct"] = (obs / cm * 100.0) if cm != 0 else float("nan")

    if len(event_vals) < cfg.min_samples:
        text = "样本不足，不判定"
    elif lo > 0 and p_value < cfg.ci_alpha:
        text = "显著优于对照"
    elif hi < 0 and p_value < cfg.ci_alpha:
        text = "显著劣于对照"
    else:
        text = "方向一致但不显著" if obs > 0 else ("方向相反但不显著" if obs < 0 else "无差异")

    out["verdict_text"] = text
    return out


def overall_verdict(results: Sequence[Dict[str, float]]) -> str:
    """汇总多个 horizon 的比较结果，给出命题级结论。

    规则:
        全部「显著优于对照」            → 支持
        至少一个显著优于，其余不显著     → 部分支持
        至少一个显著劣于                → 不支持
        其余                            → 不支持
    """
    texts = [r.get("verdict_text", "") for r in results if "verdict_text" in r]
    if not texts:
        return "不支持（无任何可判定结果）"
    n_sig = sum(1 for t in texts if t == "显著优于对照")
    n_bad = sum(1 for t in texts if t == "显著劣于对照")
    n_total = len(texts)
    if n_bad > 0:
        return "不支持"
    if n_sig == n_total:
        return "支持"
    if n_sig > 0:
        return "部分支持"
    return "不支持"
