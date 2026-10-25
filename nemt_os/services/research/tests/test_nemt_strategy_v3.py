from nemt_os.services.research.nemt_momentum_v2 import MomentumState
from nemt_os.services.research.nemt_strategy_v3 import PositionControllerV3, StrategyV3Config, risk_sized_notional


def state(phase: str, score: int = 90) -> MomentumState:
    return MomentumState(0.8, 0.8, phase, score)  # type: ignore[arg-type]


def test_reversal_requires_two_consecutive_opposite_states() -> None:
    controller = PositionControllerV3()
    first = controller.decide(state("critical_down"), 1)
    second = controller.decide(state("critical_down"), 1)
    assert first.action == "WAIT_REVERSAL" and first.target == 1
    assert second.action == "REVERSE" and second.target == -1


def test_reversal_count_resets_when_signal_disappears() -> None:
    controller = PositionControllerV3()
    controller.decide(state("critical_down"), 1)
    controller.decide(state("critical"), 1)
    again = controller.decide(state("critical_down"), 1)
    assert again.action == "WAIT_REVERSAL" and again.reversal_count == 1


def test_stop_cooldown_blocks_two_bars() -> None:
    controller = PositionControllerV3()
    controller.on_stop()
    assert controller.decide(state("critical_up"), 0).action == "COOLDOWN"
    assert controller.decide(state("critical_up"), 0).action == "COOLDOWN"
    assert controller.decide(state("critical_up"), 0).action == "OPEN"


def test_risk_sizing_caps_loss_and_carrying_capacity() -> None:
    cfg = StrategyV3Config(risk_per_trade=0.02)
    assert risk_sized_notional(100.0, 0.02, 5, cfg) == 100.0
    assert risk_sized_notional(100.0, 0.001, 5, cfg) == 475.0


def test_leverage_never_exceeds_five() -> None:
    assert PositionControllerV3().decide(state("critical_up", 100), 0).leverage == 5
