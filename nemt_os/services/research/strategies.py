"""统一策略接口与四个基准策略 (canonical)。

协议约束（硬性）:
    1. 策略**只能**读取当前及历史 K 线与 NEMT 状态，不得访问未来 K 线
    2. 策略**不得**直接修改账户、不得直接调用交易所
    3. 策略输出的是「目标信号」，由回测引擎决定成交价格与成本

防未来数据泄漏的保证方式:
    策略通过 `past()` 辅助函数取数，该函数只返回 [i-n+1, i] 区间。
    另有等价性测试：用截断序列计算前 k 根的信号，必须与原序列前 k 根完全一致
    （见 tests/test_no_lookahead.py）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence

from .candles import CandleSeries
from .events import EventConfig, detect_critical_events
from .signal_math import bollinger_width, rolling_mean
from .variables import NEMTState


# ---------------------------------------------------------------- 信号


FLAT = 0.0
LONG = 1.0


@dataclass
class StrategyContext:
    """策略可见的上下文。只包含截至 index（含）的数据。"""

    series: CandleSeries
    states: List[NEMTState]
    index: int

    def past(self, values: Sequence[float], n: int) -> List[float]:
        """取截至当前 index 的最多 n 个历史值。**这是唯一的取数入口。**"""
        start = max(0, self.index - n + 1)
        return list(values[start: self.index + 1])

    def state(self) -> Optional[NEMTState]:
        if 0 <= self.index < len(self.states):
            return self.states[self.index]
        return None

    def close(self) -> float:
        return self.series.closes[self.index]

    def open_(self) -> float:
        return self.series.opens[self.index]


class Strategy:
    """策略基类。子类实现 `signal(ctx) -> float`（0 = 空仓, 1 = 满仓）。"""

    name: str = "base"

    def __init__(self, **params):
        self.params: Dict = {}
        self.set_params(**params)

    def set_params(self, **params) -> None:
        self.params.update(params)

    def get_params(self) -> Dict:
        return dict(self.params)

    def config_dict(self) -> Dict:
        return {"name": self.name, "params": self.get_params()}

    def prepare(self, series: CandleSeries, states: List[NEMTState]) -> None:
        """可选：一次性预计算（只允许使用全序列的**因果**计算）。"""
        return None

    def signal(self, ctx: StrategyContext) -> float:
        raise NotImplementedError


# ---------------------------------------------------------------- 策略实现


class BuyAndHold(Strategy):
    """买入并持有。第一个可交易 bar 买入，之后一直持有。"""

    name = "buy_and_hold"

    def __init__(self, **params):
        super().__init__(**params)
        self._entered = False

    def prepare(self, series, states):
        self._entered = False

    def signal(self, ctx: StrategyContext) -> float:
        if not self._entered:
            self._entered = True
        return LONG


class SMABaseline(Strategy):
    """SMA 双均线基准：快线上穿慢线做多，下穿离场。"""

    name = "sma_baseline"

    def __init__(self, fast: int = 20, slow: int = 60, **params):
        super().__init__(fast=fast, slow=slow, **params)

    def signal(self, ctx: StrategyContext) -> float:
        fast = int(self.params.get("fast", 20))
        slow = int(self.params.get("slow", 60))
        closes = ctx.series.closes
        f = ctx.past(closes, fast)
        s = ctx.past(closes, slow)
        if len(f) < fast or len(s) < slow:
            return FLAT
        mf = sum(f) / len(f)
        ms = sum(s) / len(s)
        return LONG if mf > ms else FLAT


class BollingerSqueezeBreakout(Strategy):
    """布林带收缩突破基准。

    逻辑:
        1. 布林带宽度处于低分位（收缩）→ 进入"待命"状态
        2. 收盘价突破上轨 → 做多
        3. 收盘价跌破中轨 → 离场

    这是命题中「简单波动率收缩基准」对应的**可执行策略**版本，
    用于检验"NEMT 是否带来超越简单波动率收缩的增量"。
    """

    name = "bollinger_squeeze_breakout"

    def __init__(self, window: int = 20, k: float = 2.0,
                 squeeze_percentile: float = 0.20, **params):
        super().__init__(window=window, k=k,
                         squeeze_percentile=squeeze_percentile, **params)

    def prepare(self, series: CandleSeries, states: List[NEMTState]) -> None:
        """一次性预计算 BBW 序列。

        BBW 在第 t 根只依赖 [t-w+1, t]，因此一次性算完仍是**因果**的，
        与逐根计算逐位等价。放在这里是为了避免每根 K 线重算整个前缀
        （那会是 O(n²)，在 4 万根数据上直接卡死）。
        """
        w = int(self.params.get("window", 20))
        kk = float(self.params.get("k", 2.0))
        raw = bollinger_width(series.closes, w, kk)
        self._bbw = [0.0 if v is None else v for v in raw]
        self._in_pos = False

    def signal(self, ctx: StrategyContext) -> float:
        window = int(self.params.get("window", 20))
        k = float(self.params.get("k", 2.0))
        sq_pct = float(self.params.get("squeeze_percentile", 0.20))

        if not hasattr(self, "_bbw"):
            self.prepare(ctx.series, ctx.states)

        i = ctx.index
        if i >= len(self._bbw) or self._bbw[i] == 0.0 and window > i:
            return FLAT

        closes = ctx.series.closes
        seg = ctx.past(closes, window)
        if len(seg) < window:
            return FLAT
        m = sum(seg) / len(seg)
        var = sum((v - m) ** 2 for v in seg) / (window - 1)
        sd = math.sqrt(max(var, 0.0))
        if m <= 0:
            return FLAT
        upper = m + k * sd

        # 收缩判定：当前 BBW 在过去 window*8 根 BBW 中的分位（只用历史）
        hist = ctx.past(self._bbw, window * 8)
        if len(hist) < 5:
            return FLAT
        cur = hist[-1]
        rank = sum(1 for v in hist if v <= cur) / len(hist)
        squeezed = rank <= sq_pct

        price = ctx.close()
        if squeezed and price > upper:
            self._in_pos = True
            return LONG
        if price < m:
            self._in_pos = False
            return FLAT
        return LONG if self._in_pos else FLAT


class NEMTCriticalState(Strategy):
    """NEMT 临界状态策略。

    **入场信号必须来自第四阶段的事件定义**，不得另起一套无关规则。
    本策略直接调用 `events.detect_critical_events`，其条件为:
        谱宽低分位 + 波动收缩 + DCI 由低位转升

    离场规则（两条，均需在报告中披露）:
        1. 持有 max_hold_bars 根后强制离场
        2. 市场相位回到 A（高噪声混乱期）时离场
    """

    name = "nemt_critical_state"

    def __init__(self, max_hold_bars: int = 72, exit_on_phase_a: bool = True,
                 **params):
        super().__init__(max_hold_bars=max_hold_bars,
                         exit_on_phase_a=exit_on_phase_a, **params)

    def prepare(self, series: CandleSeries, states: List[NEMTState]) -> None:
        cfg = EventConfig(**{
            k: v for k, v in self.params.items()
            if k in EventConfig.__dataclass_fields__
        })
        self._events = set(detect_critical_events(states, cfg))
        self._entry_index: Optional[int] = None

    def _ensure(self, ctx: StrategyContext) -> None:
        if not hasattr(self, "_events"):
            self.prepare(ctx.series, ctx.states)

    def signal(self, ctx: StrategyContext) -> float:
        self._ensure(ctx)
        i = ctx.index

        if i in self._events:
            self._entry_index = i
            return LONG

        if self._entry_index is None:
            return FLAT

        # 离场条件 1：超过最大持有期
        max_hold = int(self.params.get("max_hold_bars", 72))
        if i - self._entry_index >= max_hold:
            self._entry_index = None
            return FLAT

        # 离场条件 2：相位回到混乱期
        if bool(self.params.get("exit_on_phase_a", True)):
            st = ctx.state()
            if st is not None and st.market_phase == "A":
                self._entry_index = None
                return FLAT

        return LONG


# ---------------------------------------------------------------- 注册


STRATEGY_REGISTRY: Dict[str, type] = {
    BuyAndHold.name: BuyAndHold,
    SMABaseline.name: SMABaseline,
    BollingerSqueezeBreakout.name: BollingerSqueezeBreakout,
    NEMTCriticalState.name: NEMTCriticalState,
}

ALL_STRATEGIES = ["buy_and_hold", "sma_baseline",
                  "bollinger_squeeze_breakout", "nemt_critical_state"]


def build_strategy(name: str, **params) -> Strategy:
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"未知策略 {name!r}; 可用: {sorted(STRATEGY_REGISTRY)}")
    return STRATEGY_REGISTRY[name](**params)


def run_strategy(
    strategy: Strategy,
    series: CandleSeries,
    states: List[NEMTState],
) -> List[float]:
    """为每根 K 线生成目标信号。

    返回长度与 series 相同的信号序列：
        0.0 = 空仓, 1.0 = 做多
    信号在**第 i 根收盘后**产生，由回测引擎在 i+1 的 open 成交。
    """
    strategy.prepare(series, states)
    out: List[float] = []
    for i in range(len(series)):
        ctx = StrategyContext(series=series, states=states, index=i)
        v = strategy.signal(ctx)
        out.append(float(v))
    return out
