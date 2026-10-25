from nemt_os.services.research.strategy_acceptance import assess_strategy


def test_low_win_rate_can_pass_with_positive_asymmetric_expectancy() -> None:
    result = assess_strategy({
        "trade_count": 100, "total_return": 1.0, "expectancy_ratio": 0.1,
        "profit_factor": 1.5, "payoff_ratio": 100.0, "sharpe_ratio": 2.0,
        "max_drawdown": 0.15, "win_rate": 0.10,
    })
    assert result["passed"] is True
    assert result["diagnostics"]["win_rate"] == 0.10


def test_high_win_rate_cannot_rescue_negative_expectancy() -> None:
    result = assess_strategy({
        "trade_count": 100, "total_return": -0.1, "expectancy_ratio": -0.01,
        "profit_factor": 0.9, "payoff_ratio": 0.2, "sharpe_ratio": -0.2,
        "max_drawdown": 0.25, "win_rate": 0.90,
    })
    assert result["passed"] is False
    assert result["checks"]["positive_expectancy"] is False


def test_drawdown_remains_a_hard_survival_gate() -> None:
    result = assess_strategy({
        "trade_count": 100, "total_return": 2.0, "expectancy_ratio": 0.2,
        "profit_factor": 2.0, "payoff_ratio": 4.0, "sharpe_ratio": 2.5,
        "max_drawdown": 0.21, "win_rate": 0.20,
    })
    assert result["passed"] is False
    assert result["checks"]["drawdown"] is False
