from nemt_os.services.research.nemt_momentum_v2 import (
    MomentumState,
    MomentumV2Config,
    generate_targets,
    next_intent,
)


def test_repeated_direction_is_hold_not_new_entry() -> None:
    state = MomentumState(0.8, 0.8, "critical_up", 90)
    assert next_intent(state, 0, "bear").action == "OPEN"
    held = next_intent(state, 1, "bear")
    assert held.action == "HOLD"
    assert held.target == 1


def test_annual_regime_sizes_but_never_blocks_reversal() -> None:
    state = MomentumState(0.8, 0.8, "critical_up", 90)
    counter = next_intent(state, 0, "bear")
    aligned = next_intent(state, 0, "bull")
    assert counter.action == "OPEN"
    assert counter.risk_scale == 0.5
    assert aligned.risk_scale == 1.0


def test_decay_closes_and_critical_wait_holds() -> None:
    waiting = MomentumState(0.1, 0.8, "critical", 50)
    decay = MomentumState(0.1, 0.1, "decay", 20)
    assert next_intent(waiting, -1).target == -1
    assert next_intent(decay, -1).action == "CLOSE"


def test_prefix_results_do_not_change_with_future_prices() -> None:
    cfg = MomentumV2Config(window=12)
    prefix = [100.0 + (i % 5) * 2.0 for i in range(40)]
    full = prefix + [1.0, 9999.0, 2.0]
    a = generate_targets(prefix, config=cfg)
    b = generate_targets(full, config=cfg)[: len(prefix)]
    assert a == b
