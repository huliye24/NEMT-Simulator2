"""确定性数学基元 (纯标准库)。

为什么不用 numpy:
    本模块的所有函数都必须在任何 CPU 机器上给出**逐位相同**的结果。
    纯 Python 实现避免了 BLAS / 多线程 / 版本差异带来的浮点结果漂移，
    从而使实验信封可复现。窗口很小 (<=512)，性能完全够用。

所有函数均为纯函数：不修改输入，不使用全局随机源。
"""

from __future__ import annotations

import math
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------- FFT


def next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p <<= 1
    return p


# 旋转因子与位反转表缓存。
# 纯 Python 的 FFT 是整条研究链路的性能瓶颈（每根 K 线要做数十次变换），
# 预计算后可将逐蝶形运算中的三角函数与位运算彻底消除。
# 缓存只改变常数因子，**不改变运算顺序**，因此结果逐位一致。
_REV_CACHE: dict = {}
_TWIDDLE_CACHE: dict = {}


def _tables(n: int):
    """返回 (位反转置换数组, 每级旋转因子表)。"""
    rev = _REV_CACHE.get(n)
    tw = _TWIDDLE_CACHE.get(n)
    if rev is not None and tw is not None:
        return rev, tw

    rbits = n.bit_length() - 1
    rev = [0] * n
    for i in range(n):
        x = i
        y = 0
        for _ in range(rbits):
            y = (y << 1) | (x & 1)
            x >>= 1
        rev[i] = y

    twiddle = []
    length = 2
    while length <= n:
        half = length >> 1
        cos_t = [0.0] * half
        sin_t = [0.0] * half
        ang0 = -2.0 * math.pi / length
        for k in range(half):
            ang = ang0 * k
            cos_t[k] = math.cos(ang)
            sin_t[k] = math.sin(ang)
        twiddle.append((length, half, cos_t, sin_t))
        length <<= 1

    _REV_CACHE[n] = rev
    _TWIDDLE_CACHE[n] = twiddle
    return rev, twiddle


def fft(re: Sequence[float], im: Sequence[float]) -> Tuple[List[float], List[float]]:
    """迭代式 radix-2 Cooley-Tukey FFT。

    输入长度必须是 2 的幂（调用方负责 pad）。返回未归一化的 DFT，
    与 numpy.fft.fft 定义一致（无 1/N 归一化）。

    已针对重复调用优化：位反转置换与旋转因子表按 n 缓存，
    蝶形内循环不含任何三角函数调用。
    """
    n = len(re)
    if n == 0:
        return [], []
    if n & (n - 1) != 0:
        raise ValueError(f"FFT 长度必须是 2 的幂, 收到 {n}")

    rev, twiddle = _tables(n)

    a_re = [0.0] * n
    a_im = [0.0] * n
    for i in range(n):
        j = rev[i]
        a_re[i] = re[j]
        a_im[i] = im[j]

    for length, half, cos_t, sin_t in twiddle:
        step = length
        for i in range(0, n, step):
            for k in range(half):
                c = cos_t[k]
                s = sin_t[k]
                p = i + k
                q = p + half
                ur, ui = a_re[p], a_im[p]
                vr = a_re[q] * c - a_im[q] * s
                vi = a_re[q] * s + a_im[q] * c
                a_re[p] = ur + vr
                a_im[p] = ui + vi
                a_re[q] = ur - vr
                a_im[q] = ui - vi

    return a_re, a_im


def real_power_spectrum(x: Sequence[float], n_fft: Optional[int] = None) -> List[float]:
    """实信号的单边功率谱（正频率部分，含 DC 与 Nyquist）。

    返回长度 n_fft//2 + 1，对应频率 k/N (k = 0..N/2)。
    功率定义为 |X[k]|^2 / N（与 numpy 的 (np.abs(fft)/N)**2 一致）。
    """
    n = len(x)
    if n == 0:
        return []
    if n_fft is None:
        n_fft = next_pow2(max(n, 2))
    if n_fft & (n_fft - 1) != 0:
        raise ValueError("n_fft 必须是 2 的幂")

    padded = [0.0] * n_fft
    padded[:n] = list(x)
    re, im = fft(padded, [0.0] * n_fft)
    half = n_fft // 2
    out = [0.0] * (half + 1)
    for k in range(half + 1):
        out[k] = (re[k] * re[k] + im[k] * im[k]) / (n_fft * n_fft)
    return out


def spectral_width_from_power(power: Sequence[float]) -> float:
    """由功率谱计算谱宽：功率加权的频率二阶矩的平方根。

        P_k      = power[k]                       (k = 0..N/2)
        w_k      = P_k / Σ P_k                    (归一化权重)
        f_k      = k / N                          (归一化频率, Nyquist = 0.5)
        mean     = Σ w_k * f_k
        width    = sqrt( Σ w_k * (f_k - mean)^2 )

    注意:
        - 必须使用**频率轴**，这是谱宽的定义。仓库历史实现中
          `enhanced_phase_detector.py:353` 用 np.std(功率谱数组值) 冒充谱宽，
          完全不含频率轴，属假指标，本实现已纠正。
        - 若总功率为 0（常数序列），返回 0.0，不伪造默认值。
    """
    if not power:
        return 0.0
    n_fft = (len(power) - 1) * 2
    if n_fft <= 0:
        return 0.0
    total = sum(power)
    if total <= 1e-300:
        return 0.0

    mean = 0.0
    for k, p in enumerate(power):
        mean += (p / total) * (k / n_fft)
    var = 0.0
    for k, p in enumerate(power):
        f = k / n_fft
        var += (p / total) * (f - mean) * (f - mean)
    return math.sqrt(max(var, 0.0))


# ---------------------------------------------------------------- 滚动统计


def rolling_mean(x: Sequence[float], window: int) -> List[Optional[float]]:
    """滚动均值。前 window-1 个位置返回 None（数据不足，不伪造）。"""
    out: List[Optional[float]] = [None] * len(x)
    if window <= 0:
        return out
    s = 0.0
    for i, v in enumerate(x):
        s += v
        if i >= window:
            s -= x[i - window]
        if i >= window - 1:
            out[i] = s / window
    return out


def rolling_std(x: Sequence[float], window: int) -> List[Optional[float]]:
    """滚动样本标准差 (ddof=1)。数据不足返回 None。"""
    out: List[Optional[float]] = [None] * len(x)
    if window <= 1:
        return out
    for i in range(window - 1, len(x)):
        seg = x[i - window + 1: i + 1]
        m = sum(seg) / window
        var = sum((v - m) ** 2 for v in seg) / (window - 1)
        out[i] = math.sqrt(max(var, 0.0))
    return out


def trailing_percentile_rank(x: Sequence[float], window: int) -> List[Optional[float]]:
    """当前值在过去 window 个值（含当前）中的分位排名，返回 [0,1]。

    **只使用当前及过去的数据**，不使用全样本分布 —— 这是避免未来数据
    泄漏的关键。仓库历史实现 `nemt_signals.py:255` 对整段历史求分位，
    存在全样本前视，本实现已纠正。
    """
    out: List[Optional[float]] = [None] * len(x)
    if window <= 1:
        return out
    for i in range(window - 1, len(x)):
        seg = x[i - window + 1: i + 1]
        cur = x[i]
        # 小于等于当前值的占比（含自身，因此最小值为 1/window > 0）
        cnt = sum(1 for v in seg if v <= cur)
        out[i] = cnt / len(seg)
    return out


def rolling_sum(x: Sequence[float], window: int) -> List[Optional[float]]:
    out: List[Optional[float]] = [None] * len(x)
    if window <= 0:
        return out
    s = 0.0
    for i, v in enumerate(x):
        s += v
        if i >= window:
            s -= x[i - window]
        if i >= window - 1:
            out[i] = s
    return out


def ols_slope(y: Sequence[float]) -> float:
    """对 y 关于等距时间做最小二乘拟合，返回斜率。长度 < 3 返回 0.0。"""
    n = len(y)
    if n < 3:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(y) / n
    num = sum((xs[i] - mx) * (y[i] - my) for i in range(n))
    den = sum((xs[i] - mx) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return num / den


def log_returns(prices: Sequence[float]) -> List[Optional[float]]:
    """对数收益率。第一项为 None。价格非正时该项为 None。"""
    out: List[Optional[float]] = [None] * len(prices)
    for i in range(1, len(prices)):
        p0, p1 = prices[i - 1], prices[i]
        if p0 is None or p1 is None or p0 <= 0 or p1 <= 0:
            continue
        out[i] = math.log(p1 / p0)
    return out


def realized_volatility(returns: Sequence[Optional[float]], window: int) -> List[Optional[float]]:
    """滚动已实现波动率（收益率标准差，未年化）。"""
    out: List[Optional[float]] = [None] * len(returns)
    for i in range(window - 1, len(returns)):
        seg = returns[i - window + 1: i + 1]
        if any(v is None for v in seg):
            continue
        vals = [v for v in seg if v is not None]
        m = sum(vals) / len(vals)
        var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1) if len(vals) > 1 else 0.0
        out[i] = math.sqrt(max(var, 0.0))
    return out


def bollinger_width(closes: Sequence[float], window: int = 20, k: float = 2.0) -> List[Optional[float]]:
    """布林带宽度 (BBW) = (upper - lower) / mid，无量纲。"""
    means = rolling_mean(closes, window)
    out: List[Optional[float]] = [None] * len(closes)
    for i in range(window - 1, len(closes)):
        m = means[i]
        if m is None:
            continue
        seg = closes[i - window + 1: i + 1]
        var = sum((v - m) ** 2 for v in seg) / (window - 1)
        sd = math.sqrt(max(var, 0.0))
        upper = m + k * sd
        lower = m - k * sd
        if m > 0:
            out[i] = (upper - lower) / m
    return out


def percentile(sorted_vals: Sequence[float], q: float) -> float:
    """线性插值分位数，q ∈ [0,1]。输入需已升序。"""
    if not sorted_vals:
        return float("nan")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    q = min(max(q, 0.0), 1.0)
    pos = q * (len(sorted_vals) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def median(xs: Sequence[float]) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


def stdev(xs: Sequence[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    m = sum(xs) / n
    return math.sqrt(sum((v - m) ** 2 for v in xs) / (n - 1))
