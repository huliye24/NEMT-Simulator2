from nemt_os.services.research.trend_rollability_v43 import RollabilityObservation, assess_rollability


def test_similar_positive_history_permits_roll() -> None:
    history = [RollabilityObservation((0.8, 0.2), True, 2.0) for _ in range(30)]
    assert assess_rollability((0.8, 0.2), history).permitted is True


def test_negative_marginal_history_blocks_roll() -> None:
    history = [RollabilityObservation((0.8, 0.2), False, -1.0) for _ in range(30)]
    decision = assess_rollability((0.8, 0.2), history)
    assert decision.permitted is False


def test_dissimilar_history_does_not_count_as_effective_sample() -> None:
    history = [RollabilityObservation((0.0, 1.0), True, 2.0) for _ in range(100)]
    decision = assess_rollability((1.0, 0.0), history)
    assert decision.permitted is False
    assert decision.reason == "insufficient_similar_history"
