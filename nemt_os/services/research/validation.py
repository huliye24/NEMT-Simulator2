"""时间序列切分与防过拟合 (canonical)。

纪律:
    - **禁止随机打乱时间序列**
    - 参数只允许在**训练集**上选择
    - 验证集用于模型和参数决策
    - 测试集只允许在最终评估时运行一次
    - 若测试集表现显著衰减，必须明确判定为「疑似过拟合」，不得粉饰
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass
class SplitConfig:
    train_ratio: float = 0.60
    val_ratio: float = 0.20
    # test_ratio = 1 - train - val
    n_walk_forward_folds: int = 4
    # 判定「显著衰减」的阈值：测试集指标相对验证集下降超过此比例
    degradation_threshold: float = 0.40

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Split:
    """按时间顺序切分的三段索引区间（左闭右开）。"""

    n: int
    train: Tuple[int, int]
    val: Tuple[int, int]
    test: Tuple[int, int]

    def as_dict(self) -> dict:
        return {
            "n": self.n,
            "train": list(self.train),
            "val": list(self.val),
            "test": list(self.test),
        }

    def names(self) -> List[str]:
        return ["train", "val", "test"]

    def range_for(self, name: str) -> Tuple[int, int]:
        return getattr(self, name)


def split_by_time(n: int, cfg: Optional[SplitConfig] = None) -> Split:
    """按时间顺序切分。返回索引区间，不返回打乱后的索引。"""
    cfg = cfg or SplitConfig()
    if n <= 0:
        raise ValueError("n 必须为正")
    if cfg.train_ratio + cfg.val_ratio >= 1.0:
        raise ValueError("train_ratio + val_ratio 必须 < 1.0")

    train_end = int(n * cfg.train_ratio)
    val_end = int(n * (cfg.train_ratio + cfg.val_ratio))
    # 保证每段至少 1 根
    train_end = max(1, min(train_end, n - 2))
    val_end = max(train_end + 1, min(val_end, n - 1))

    return Split(n=n, train=(0, train_end), val=(train_end, val_end), test=(val_end, n))


@dataclass
class Fold:
    """Walk-forward 的一折。"""

    fold_id: int
    train: Tuple[int, int]
    test: Tuple[int, int]

    def as_dict(self) -> dict:
        return {"fold_id": self.fold_id, "train": list(self.train), "test": list(self.test)}


def walk_forward_folds(n: int, cfg: Optional[SplitConfig] = None) -> List[Fold]:
    """生成 walk-forward 折叠。

    采用**滚动原点**（anchored expanding window）：
    第 k 折的训练集从 0 开始，测试集紧随其后并不断向前推进。
    训练集始终只包含测试集之前的数据 —— 这是防止未来数据泄漏的关键。
    """
    cfg = cfg or SplitConfig()
    n_folds = max(1, int(cfg.n_walk_forward_folds))
    folds: List[Fold] = []

    min_train = int(n * cfg.train_ratio)
    if min_train < 2:
        min_train = max(2, n // (n_folds + 1))

    span = n - min_train
    if span <= n_folds:
        return [Fold(fold_id=0, train=(0, min_train), test=(min_train, n))]

    step = span // n_folds
    for k in range(n_folds):
        test_start = min_train + k * step
        test_end = min_train + (k + 1) * step
        if k == n_folds - 1:
            test_end = n
        if test_end - test_start < 2:
            continue
        folds.append(Fold(fold_id=k, train=(0, test_start), test=(test_start, test_end)))
    return folds


# ---------------------------------------------------------------- 过拟合判定


@dataclass
class DegradationVerdict:
    metric: str
    train_value: float
    val_value: float
    test_value: float
    drop_vs_val: Optional[float]
    drop_vs_train: Optional[float]
    threshold: float
    verdict: str
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _rel_drop(base: float, cur: float) -> Optional[float]:
    """相对下降比例。base <= 0 时无法定义相对变化，返回 None。"""
    if base <= 0:
        return None
    return (base - cur) / base


def judge_degradation(
    metric: str,
    train_value: float,
    val_value: float,
    test_value: float,
    threshold: float = 0.40,
    higher_is_better: bool = True,
) -> DegradationVerdict:
    """判断测试集是否相对验证集显著衰减。"""
    if not higher_is_better:
        train_value, val_value, test_value = -train_value, -val_value, -test_value

    d_val = _rel_drop(val_value, test_value)
    d_train = _rel_drop(train_value, test_value)

    if d_val is None:
        return DegradationVerdict(
            metric, train_value, val_value, test_value, None, None, threshold,
            "无法判定", "验证集指标 <= 0，相对衰减无定义"
        )

    if d_val > threshold:
        verdict = "疑似过拟合"
        note = f"测试集相对验证集下降 {d_val*100:.1f}%，超过阈值 {threshold*100:.0f}%"
    elif d_val > threshold / 2:
        verdict = "轻度衰减"
        note = f"测试集相对验证集下降 {d_val*100:.1f}%，未超过阈值但需警惕"
    elif d_val < 0:
        verdict = "无衰减"
        note = f"测试集相对验证集变化 {-d_val*100:.1f}%（未下降）"
    else:
        verdict = "无显著衰减"
        note = f"测试集相对验证集下降 {d_val*100:.1f}%"

    return DegradationVerdict(
        metric=metric,
        train_value=train_value,
        val_value=val_value,
        test_value=test_value,
        drop_vs_val=d_val,
        drop_vs_train=d_train,
        threshold=threshold,
        verdict=verdict,
        note=note,
    )


# ---------------------------------------------------------------- 参数搜索记录


@dataclass
class ParamSearchRecord:
    """参数搜索结果记录。必须全部保存，不得只保留最优解。"""

    split_name: str
    metric: str
    best_params: Dict
    best_score: float
    all_results: List[Dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "split_name": self.split_name,
            "metric": self.metric,
            "best_params": self.best_params,
            "best_score": self.best_score,
            "n_candidates": len(self.all_results),
            "all_results": self.all_results,
        }


def grid_search(
    candidates: Sequence[Dict],
    evaluate_fn,
    metric: str = "sharpe_ratio",
    split_name: str = "train",
    higher_is_better: bool = True,
) -> ParamSearchRecord:
    """网格搜索。evaluate_fn(params) -> metrics dict。

    只在传入的 split_name 区间上评估（由调用方保证是训练集）。
    """
    results: List[Dict] = []
    for params in candidates:
        try:
            metrics = evaluate_fn(params)
        except Exception as e:  # 单个候选失败不应中断整个搜索
            results.append({"params": params, "error": f"{type(e).__name__}: {e}"})
            continue
        score = metrics.get(metric, float("nan"))
        if score != score:  # NaN
            score = float("-inf") if higher_is_better else float("inf")
        results.append({"params": params, "metrics": dict(metrics), "score": score})

    valid = [r for r in results if "score" in r]
    if not valid:
        return ParamSearchRecord(split_name, metric, {}, float("nan"), results)

    best = max(valid, key=lambda r: r["score"]) if higher_is_better \
        else min(valid, key=lambda r: r["score"])

    return ParamSearchRecord(
        split_name=split_name,
        metric=metric,
        best_params=dict(best["params"]),
        best_score=best["score"],
        all_results=results,
    )
