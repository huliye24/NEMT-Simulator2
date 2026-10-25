from nemt_os.services.research.expectancy_optimizer import optimize_expectancy


def test_low_win_rate_high_payoff_can_receive_allocation() -> None:
    returns = [-1.0] * 90 + [100.0] * 10
    result = optimize_expectancy(returns)
    assert result.conservative_win_probability < 0.20
    assert result.robust_expectancy_r > 0
    assert result.optimal_allocation_fraction > 0


def test_high_win_rate_negative_payoff_is_rejected() -> None:
    returns = [0.05] * 18 + [-3.0, -3.0]
    result = optimize_expectancy(returns)
    assert result.posterior_win_probability > 0.80
    assert result.eligible is False
    assert result.reason == "non_positive_robust_expectancy"


def test_single_huge_winner_is_shrunk_and_insufficient() -> None:
    result = optimize_expectancy([-1.0] * 8 + [100.0])
    assert result.shrunk_average_win_r < 100.0
    assert result.eligible is False
    assert result.reason == "insufficient_observations"


def test_tail_loss_reduces_or_eliminates_allocation() -> None:
    ordinary = optimize_expectancy([-1.0] * 10 + [4.0] * 10)
    tailed = optimize_expectancy([-1.0] * 9 + [-10.0] + [4.0] * 10)
    assert tailed.loss_cvar_r > ordinary.loss_cvar_r
    assert tailed.optimal_allocation_fraction <= ordinary.optimal_allocation_fraction


def test_drawdown_throttles_allocation_to_zero() -> None:
    returns = [-1.0] * 10 + [4.0] * 10
    normal = optimize_expectancy(returns, current_drawdown=0.0)
    stopped = optimize_expectancy(returns, current_drawdown=0.20)
    assert normal.optimal_allocation_fraction > 0
    assert stopped.optimal_allocation_fraction == 0
    assert stopped.reason == "drawdown_shutdown"
