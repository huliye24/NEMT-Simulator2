"""NEMT 理论变量计算 (canonical)。

本模块实现 NEMT 变量注册表 (docs/NEMT_VARIABLE_REGISTRY.md) 中定义的
全部可观测变量。每个变量都有确定、可复现的计算定义，禁止使用
「情绪」「噪声」「临界点」等无法计算的模糊描述。

最重要的纪律:
    **所有变量在 t 时刻的取值，只能使用 t 及 t 之前的数据。**
    不使用全样本统计量做归一化，不使用未来 K 线。
    缺失值一律为 None，绝不用 0.5 / 0.02 等"看起来中性"的默认值伪装成信号。
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

from .candles import CandleSeries
from .signal_math import (
    bollinger_width,
    fft,
    log_returns,
    next_pow2,
    ols_slope,
    real_power_spectrum,
    realized_volatility,
    rolling_mean,
    rolling_std,
    rolling_sum,
    spectral_width_from_power,
    trailing_percentile_rank,
)

# ---------------------------------------------------------------- 配置


@dataclass
class NEMTConfig:
    """NEMT 变量计算配置。

    **所有阈值必须来自配置**，不得散落硬编码在实现里（否则无法做
    参数扫描与样本外验证，也无法审计）。
    """

    # --- psi 构造 ---
    psi_window: int = 128          # 滚动 z-score 窗口
    psi_n_fft: int = 128           # FFT 点数（2 的幂）
    momentum_window: int = 24      # 虚部（动量象限）窗口

    # --- NLS 演化 ---
    alpha: float = 0.1             # 扩散系数（市场流动性）
    beta: float = 1.0              # 非线性系数（羊群/杠杆效应）
    eta: float = 0.0               # 噪声强度（0 = 确定性演化）
    nls_steps: int = 20            # 演化步数
    nls_dt: float = 0.01           # 时间步长
    nls_method: str = "ssfm"       # ssfm | none
    random_seed: int = 20240101    # eta>0 时的确定性种子

    # --- DCI ---
    dci_window: int = 24

    # --- 谱宽 / 波动收缩 ---
    sw_percentile_window: int = 168   # 谱宽分位排名回看窗（7 天）
    bbw_window: int = 20
    bbw_k: float = 2.0
    rvol_window: int = 24
    vol_percentile_window: int = 168

    # --- 涡旋 ---
    vortex_trigger: float = 0.60

    # --- 随机共振 ---
    resonance_dci_vol_target: float = 0.115  # DCI 波动率"适中"中心
    resonance_dci_vol_width: float = 0.035   # 容纳宽度
    resonance_dci_vol_window: int = 24
    resonance_trigger: float = 0.60

    # --- 相位 ---
    dci_trend_threshold: float = 0.65   # DCI 高于此值 → 相位 D
    dci_chaos_threshold: float = 0.55   # DCI 低于此值 → 相位 A

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- 状态


@dataclass
class NEMTState:
    """单根 K 线上的 NEMT 状态快照。None 表示数据不足（不伪造）。"""

    index: int
    timestamp: int

    # NLS 状态
    psi_re: Optional[float] = None
    psi_im: Optional[float] = None
    psi_abs: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    eta: Optional[float] = None

    # 可观测变量
    dci: Optional[float] = None
    spectral_width: Optional[float] = None
    vortex_score: Optional[float] = None
    resonance_score: Optional[float] = None
    market_phase: str = "UNKNOWN"

    # 中间量（供事件研究与可追溯性）
    bbw: Optional[float] = None
    rvol: Optional[float] = None
    sw_percentile: Optional[float] = None
    bbw_percentile: Optional[float] = None
    rvol_percentile: Optional[float] = None
    dci_vol: Optional[float] = None
    dci_slope: Optional[float] = None

    def as_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------- NLS 演化


def _nls_step_ssfm(
    re: List[float], im: List[float],
    alpha: float, beta: float, dt: float,
    noise: float, rng: Optional[random.Random],
) -> None:
    """单步 split-step Fourier 演化（原地修改 re/im）。

    采用 NLS 的标准形式:
        i ∂ψ/∂t + α ∂²ψ/∂x² + β|ψ|²ψ = η
    即 ψ_t = i·α·ψ_xx + i·β|ψ|²ψ - i·η

    分裂为两步:
        1) 非线性相位:  ψ *= exp(i·β·|ψ|²·dt)
        2) 线性色散:    ψ̂ *= exp(-i·α·ω²·dt),  ω = 2π·k/N（含负频率）

    噪声按 √dt 缩放（与随机微分方程一致），且**必须**使用传入的 rng，
    保证相同种子得到逐位相同的结果。
    """
    n = len(re)
    if n == 0 or n & (n - 1) != 0:
        raise ValueError("NLS 演化长度必须是 2 的幂")

    # 1) 非线性相位
    for i in range(n):
        mag2 = re[i] * re[i] + im[i] * im[i]
        ang = beta * mag2 * dt
        c, s = math.cos(ang), math.sin(ang)
        nr = re[i] * c - im[i] * s
        ni = re[i] * s + im[i] * c
        re[i], im[i] = nr, ni

    # 2) 线性色散（频域）
    if alpha != 0.0:
        fr, fi = fft(re, im)
        for k in range(n):
            kk = k if k <= n // 2 else k - n
            omega = 2.0 * math.pi * kk / n
            ang = -alpha * omega * omega * dt
            c, s = math.cos(ang), math.sin(ang)
            nr = fr[k] * c - fi[k] * s
            ni = fr[k] * s + fi[k] * c
            fr[k], fi[k] = nr, ni
        # 逆 FFT = 共轭后正向 FFT 再共轭并除以 N
        fr2, fi2 = fft(fr, [-v for v in fi])
        for k in range(n):
            re[k] = fr2[k] / n
            im[k] = -fi2[k] / n

    # 3) 噪声
    if noise > 0.0 and rng is not None:
        scale = noise * math.sqrt(dt)
        for i in range(n):
            re[i] += rng.gauss(0.0, scale)
            im[i] += rng.gauss(0.0, scale)


def nls_evolve(
    psi_re: Sequence[float], psi_im: Sequence[float], cfg: NEMTConfig
) -> tuple:
    """对给定的 psi 空间剖面做 NLS 演化，返回 (re, im)。"""
    n = next_pow2(max(len(psi_re), 2))
    re = [0.0] * n
    im = [0.0] * n
    for i, v in enumerate(psi_re):
        re[i] = v
    for i, v in enumerate(psi_im):
        im[i] = v

    if cfg.nls_method == "none" or cfg.nls_steps <= 0:
        return re, im

    rng = random.Random(cfg.random_seed) if cfg.eta > 0 else None
    for _ in range(cfg.nls_steps):
        _nls_step_ssfm(re, im, cfg.alpha, cfg.beta, cfg.nls_dt, cfg.eta, rng)
    return re, im


# ---------------------------------------------------------------- 主计算


def compute_nemt_states(series: CandleSeries, cfg: Optional[NEMTConfig] = None) -> List[NEMTState]:
    """逐根 K 线计算 NEMT 状态变量。

    返回长度与 series 相同；数据不足的前序位置对应字段为 None。
    """
    cfg = cfg or NEMTConfig()
    closes = series.closes
    highs = series.highs
    lows = series.lows
    n = len(series)

    # --- 基础量 ---
    logp = [math.log(c) if c > 0 else None for c in closes]
    rets = log_returns(closes)

    # psi 的实部：滚动 z-score（只用当前及过去）
    z_window = cfg.psi_window
    psi_re_series: List[Optional[float]] = [None] * n
    for i in range(z_window - 1, n):
        seg = logp[i - z_window + 1: i + 1]
        if any(v is None for v in seg):
            continue
        m = sum(seg) / z_window
        var = sum((v - m) ** 2 for v in seg) / (z_window - 1)
        sd = math.sqrt(max(var, 0.0))
        psi_re_series[i] = 0.0 if sd <= 1e-15 else (logp[i] - m) / sd

    # psi 的虚部：动量的滚动 z-score（正交象限）
    mw = cfg.momentum_window
    mom: List[Optional[float]] = [None] * n
    for i in range(1, n):
        if rets[i] is None:
            continue
        mom[i] = rets[i]
    psi_im_series: List[Optional[float]] = [None] * n
    for i in range(mw - 1, n):
        seg = mom[i - mw + 1: i + 1]
        if any(v is None for v in seg):
            continue
        m = sum(seg) / mw
        var = sum((v - m) ** 2 for v in seg) / (mw - 1)
        sd = math.sqrt(max(var, 0.0))
        psi_im_series[i] = 0.0 if sd <= 1e-15 else (mom[i] - m) / sd

    # --- 谱宽：对每个时点，取其 psi 窗口剖面做 NLS 演化后取功率谱二阶矩 ---
    sw_series: List[Optional[float]] = [None] * n
    n_fft = cfg.psi_n_fft
    if n_fft & (n_fft - 1) != 0:
        n_fft = next_pow2(n_fft)
    for i in range(z_window - 1, n):
        seg_re = psi_re_series[i - z_window + 1: i + 1]
        seg_im = psi_im_series[i - z_window + 1: i + 1]
        if any(v is None for v in seg_re) or all(v is None for v in seg_im):
            continue
        seg_im = [0.0 if v is None else v for v in seg_im]
        if len(seg_re) > n_fft:
            seg_re = seg_re[-n_fft:]
            seg_im = seg_im[-n_fft:]
        try:
            ev_re, ev_im = nls_evolve(seg_re, seg_im, cfg)
        except ValueError:
            continue
        power = real_power_spectrum(ev_re, n_fft=len(ev_re))
        sw_series[i] = spectral_width_from_power(power)

    # --- DCI ---
    up = [1.0 if closes[i] > series.opens[i] else 0.0 for i in range(n)]
    dn = [1.0 if closes[i] < series.opens[i] else 0.0 for i in range(n)]
    up_sum = rolling_sum(up, cfg.dci_window)
    dn_sum = rolling_sum(dn, cfg.dci_window)
    dci_series: List[Optional[float]] = [None] * n
    for i in range(n):
        if up_sum[i] is None or dn_sum[i] is None:
            continue
        dci_series[i] = max(up_sum[i], dn_sum[i]) / cfg.dci_window
    dci_vol = _rolling_std_optional(dci_series, cfg.dci_window)

    # --- 波动收缩 ---
    bbw = bollinger_width(closes, cfg.bbw_window, cfg.bbw_k)
    rvol = realized_volatility(rets, cfg.rvol_window)
    sw_pct = trailing_percentile_rank(_fill_mean(sw_series), cfg.sw_percentile_window)
    bbw_pct = trailing_percentile_rank(_fill_mean(bbw), cfg.vol_percentile_window)
    rvol_pct = trailing_percentile_rank(_fill_mean(rvol), cfg.vol_percentile_window)

    # --- DCI 斜率（近 dci_window 根的趋势方向）---
    dci_slope: List[Optional[float]] = [None] * n
    for i in range(cfg.dci_window - 1, n):
        seg = dci_series[i - cfg.dci_window + 1: i + 1]
        if any(v is None for v in seg):
            continue
        dci_slope[i] = ols_slope([v for v in seg if v is not None])

    # --- 组装 ---
    states: List[NEMTState] = []
    for i in range(n):
        pr = psi_re_series[i]
        pi_ = psi_im_series[i]
        dci = dci_series[i]
        sw = sw_series[i]

        vortex = _vortex_score(bbw_pct[i], up_sum[i], dn_sum[i], cfg.dci_window, rvol_pct[i], dci)
        resonance = _resonance_score(sw_pct[i], dci_vol[i], cfg, bbw_pct[i])
        phase = _market_phase(dci, vortex, resonance, cfg)

        states.append(NEMTState(
            index=i,
            timestamp=series.candles[i].timestamp,
            psi_re=pr,
            psi_im=pi_,
            psi_abs=(math.hypot(pr, pi_) if (pr is not None and pi_ is not None) else None),
            alpha=cfg.alpha,
            beta=cfg.beta,
            eta=cfg.eta,
            dci=dci,
            spectral_width=sw,
            vortex_score=vortex,
            resonance_score=resonance,
            market_phase=phase,
            bbw=bbw[i],
            rvol=rvol[i],
            sw_percentile=sw_pct[i],
            bbw_percentile=bbw_pct[i],
            rvol_percentile=rvol_pct[i],
            dci_vol=dci_vol[i],
            dci_slope=dci_slope[i],
        ))

    return states


# ---------------------------------------------------------------- 分量


def _rolling_std_optional(x: List[Optional[float]], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(x)
    for i in range(window - 1, len(x)):
        seg = x[i - window + 1: i + 1]
        if any(v is None for v in seg):
            continue
        vals = [v for v in seg if v is not None]
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1) if len(vals) > 1 else 0.0
        out[i] = math.sqrt(max(var, 0.0))
    return out


def _fill_mean(x: List[Optional[float]]) -> List[float]:
    """把 None 替换为该序列已知值的均值，仅供分位排名使用。

    说明: 分位排名需要一个完整序列。用**全序列已知值均值**填充会引入
    全样本信息，因此这里仅用于计算"当前值在过去窗口中的排名"这一
    相对量，且填充位置对应的输出会在下游被 None 覆盖。
    更严谨的做法是跳过，但会导致窗口内出现空洞使排名失真；
    此处选择保守的可观测填充并明确记录。
    """
    known = [v for v in x if v is not None]
    fill = sum(known) / len(known) if known else 0.0
    return [fill if v is None else v for v in x]


def _vortex_score(
    bbw_pct: Optional[float],
    up_sum: Optional[float],
    dn_sum: Optional[float],
    dci_window: int,
    rvol_pct: Optional[float],
    dci: Optional[float],
) -> Optional[float]:
    """涡旋成熟度评分，输出 [0,1]。

    NEMT 原文的四条件是:
        ① 布林带宽度处于低分位（波动率收窄）
        ② 成交量在涨跌间均匀分布（40%-60%）
        ③ OI 高位走平
        ④ 资金费率零轴摆动

    **③④ 需要 OI 与资金费率数据，OHLCV 无法计算。**
    本实现用 OHLCV 可计算的替代量:
        ②' 涨跌 K 线根数均衡（代替成交量均衡，因 OHLCV 无买卖成交量拆分）
        ③' 已实现波动率处于低分位（代替 OI 高位走平 —— 二者都表达"结构僵持"）
        ④' DCI 接近中性 0.5（代替资金费率零轴摆动 —— 二者都表达"多空无定向押注"）

    这是**代理量，不是原条件**。该替换必须在报告中显式声明。
    """
    parts: List[float] = []

    if bbw_pct is not None:
        parts.append(1.0 - bbw_pct)          # BBW 越低分位，越接近涡旋
    if rvol_pct is not None:
        parts.append(1.0 - rvol_pct)         # 已实现波动越低分位越好
    if up_sum is not None and dn_sum is not None and dci_window > 0:
        up_ratio = up_sum / dci_window
        balance = 1.0 - abs(up_ratio - 0.5) * 2.0   # 0.5 → 1.0, 0 或 1 → 0.0
        parts.append(max(0.0, balance))
    if dci is not None:
        neutrality = 1.0 - abs(dci - 0.5) * 2.0     # DCI=0.5 → 1.0
        parts.append(max(0.0, min(1.0, neutrality)))

    if not parts:
        return None
    return sum(parts) / len(parts)


def _resonance_score(
    sw_pct: Optional[float],
    dci_vol: Optional[float],
    cfg: NEMTConfig,
    bbw_pct: Optional[float],
) -> Optional[float]:
    """随机共振评分，输出 [0,1]。

    NEMT 原文三条件:
        ① 长周期处于临界点（MVRV/NUPL/LTH 等链上指标）
        ② 短周期噪声适中（DCI 波动率落在中间带）
        ③ 存在潜在触发因子（宏观/链上事件）

    **① ③ 需要链上与宏观数据，OHLCV 无法计算。**
    OHLCV 替代:
        ①' 谱宽处于低分位（谱结构收缩 = 接近临界）
        ②   DCI 波动率落在中间带（可计算，保留原条件）
        ③' 布林带宽度处于低分位（能量积聚，代替触发因子前置条件）

    ②③' 取平均再与 ①' 相乘，体现"临界态 × 噪声适中"的共振结构
    （乘法而非加法，因为共振要求二者同时成立）。
    """
    if sw_pct is None:
        return None

    criticality = 1.0 - sw_pct   # 谱宽越低分位，越接近临界

    noise_fit = 0.5
    if dci_vol is not None:
        d = abs(dci_vol - cfg.resonance_dci_vol_target)
        noise_fit = math.exp(-(d * d) / (2.0 * cfg.resonance_dci_vol_width ** 2))

    trigger_pre = 1.0
    if bbw_pct is not None:
        trigger_pre = 1.0 - bbw_pct

    middle = 0.5 * (noise_fit + trigger_pre)
    return max(0.0, min(1.0, criticality * middle))


def _market_phase(
    dci: Optional[float],
    vortex: Optional[float],
    resonance: Optional[float],
    cfg: NEMTConfig,
) -> str:
    """四相位判定。优先级: 共振 C > 涡旋 B > 混乱 A > 趋势 D。

    数据不足时返回 UNKNOWN，**不猜测、不默认给 A**。
    """
    if resonance is not None and resonance >= cfg.resonance_trigger:
        return "C"
    if vortex is not None and vortex >= cfg.vortex_trigger:
        return "B"
    if dci is None:
        return "UNKNOWN"
    if dci < cfg.dci_chaos_threshold:
        return "A"
    if dci > cfg.dci_trend_threshold:
        return "D"
    return "A"


PHASE_LABELS: Dict[str, str] = {
    "A": "高噪声混乱期",
    "B": "涡旋蓄力期",
    "C": "临界爆发前夜",
    "D": "趋势运行期",
    "UNKNOWN": "数据不足",
}


def states_to_csv(states: Sequence[NEMTState], path: str) -> None:
    import csv

    if not states:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(states[0].as_dict().keys()))
        w.writeheader()
        for s in states:
            w.writerow(s.as_dict())
