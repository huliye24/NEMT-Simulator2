"""
CapsuleNode 集成测试 - 完整数据流验证

测试 MarketNode -> SignalNode -> RiskNode -> BrainNode -> ExecutionNode 完整流程
"""

import sys

sys.path.insert(0, "e:/NEMT Simulator/nemt_os/nemt/core/capsule_node")

from capsules import BrainNode, ExecutionNode, MarketNode, RiskNode, SignalNode


def test_full_pipeline():
    """测试完整数据流"""
    print("=" * 70)
    print("CapsuleNode Integration Test - Full Pipeline")
    print("MarketNode -> SignalNode -> RiskNode -> BrainNode -> ExecutionNode")
    print("=" * 70)

    # 1. 创建所有节点
    print("\n=== Step 1: Create Nodes ===")
    market = MarketNode()
    signal = SignalNode()
    risk = RiskNode()
    brain = BrainNode()
    execution = ExecutionNode()

    print("Created: market_node, signal_node, risk_node, brain_node, execution_node")

    # 2. 初始化所有节点
    print("\n=== Step 2: Initialize Nodes ===")
    market.init()
    signal.init()
    risk.init()
    brain.init()
    execution.init()

    print("All nodes initialized")

    # 3. 模拟市场数据
    print("\n=== Step 3: Market Data ===")
    market_outputs = market.run(
        {"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}}
    )
    print(f"Market output: phase={market_outputs['phase']}")
    print(f"OHLCV: close={market_outputs['ohlcv']['close']}")

    # 4. 生成信号
    print("\n=== Step 4: Signal Generation ===")
    signal_outputs = signal.run({"ohlcv": market_outputs["ohlcv"], "market_phase": market_outputs["phase"]})
    sig = signal_outputs["signal"]
    print(f"Signal: {sig['direction']}, confidence={sig['confidence']:.2f}")
    print(f"Stop loss: {sig.get('stop_loss')}")
    print(f"Take profit: {sig.get('take_profit')}")

    # 5. 风险评估
    print("\n=== Step 5: Risk Evaluation ===")
    risk_outputs = risk.run({"signal": sig, "portfolio": execution.get_portfolio()})

    if risk_outputs["risk_rejection"]:
        print(f"Risk REJECTED: {risk_outputs['risk_rejection']['reason']}")
        risk_approved = None
    else:
        approved = risk_outputs["risk_approved_signal"]
        print(f"Risk APPROVED: size={approved['approved_size']:.2f}, risk_score={approved['risk_score']:.4f}")
        risk_approved = {**sig, "approved_size": approved["approved_size"], "risk_score": approved["risk_score"]}

    # 6. 决策
    print("\n=== Step 6: Brain Decision ===")
    brain_outputs = brain.run(
        {
            "signal": sig,
            "risk_evaluation": {
                "approved": risk_approved is not None,
                "approved_size": risk_approved["approved_size"] if risk_approved else 0,
                "risk_score": risk_approved["risk_score"] if risk_approved else 1,
                "risk_rejection": risk_outputs.get("risk_rejection"),
            },
            "market_phase": market_outputs["phase"],
        }
    )

    decision = brain_outputs["decision"]
    print(f"Decision: {decision['action']}")
    if decision.get("reason"):
        print(f"Reason: {decision['reason'][:50]}...")

    # 7. 执行
    print("\n=== Step 7: Execution ===")
    exec_outputs = execution.run({"decision": decision})

    if exec_outputs["order"]:
        order = exec_outputs["order"]
        print(f"Order created: {order['order_id']}")
        print(f"Status: {order['status']}")

    if exec_outputs["fill"]:
        fill = exec_outputs["fill"]
        print(f"Fill: {fill['fill_id']}, price={fill['fill_price']}, fees={fill['fees']:.2f}")

    portfolio = exec_outputs["portfolio"]
    print(f"Portfolio: total={portfolio['total_value']:.2f}, available={portfolio['available_balance']:.2f}")

    # 8. AI 可读状态
    print("\n=== Step 8: AI-Readable State ===")
    print("\nMarketNode state:")
    print(f"  Phase: {market.state.phase.value}")
    print(f"  Constraints: {[c.name for c in market.CONSTRAINTS]}")

    print("\nSignalNode state:")
    print(f"  Phase: {signal.state.phase.value}")
    print(f"  Signals generated: {len(signal.get_all_signals())}")

    print("\nRiskNode state:")
    print(f"  Phase: {risk.state.phase.value}")
    print(f"  Portfolio risk: {risk.get_risk_metrics()['portfolio_risk']:.4f}")

    print("\nBrainNode state:")
    print(f"  Phase: {brain.state.phase.value}")
    state = brain.get_strategy_state()
    print(f"  Total decisions: {state['total_decisions']}")
    print(f"  Executions: {state['executions']}, Skips: {state['skips']}")

    print("\nExecutionNode state:")
    print(f"  Phase: {execution.state.phase.value}")
    print(f"  Orders: {len(execution.get_orders())}")
    print(f"  Fills: {len(execution.get_fills())}")

    return True


def test_schema_validation_at_each_step():
    """测试每一步的 Schema 验证"""
    print("\n" + "=" * 70)
    print("Schema Validation at Each Step")
    print("=" * 70)

    market = MarketNode()
    market.init()

    # 有效输入
    print("\n=== Valid Input ===")
    try:
        outputs = market.run({"raw_feed": {"symbol": "ETHUSDT", "price": 3000, "volume": 50, "timestamp": 1714281600}})
        print("Valid: SUCCESS")
    except Exception as e:
        print(f"Valid: FAILED - {e}")

    # 无效输入 (缺少必需字段)
    print("\n=== Invalid Input (missing required fields) ===")
    try:
        outputs = market.run(
            {
                "raw_feed": {
                    "symbol": "ETHUSDT",
                    "price": 3000,
                    # 缺少 timestamp
                }
            }
        )
        print("Invalid: SHOULD HAVE FAILED")
    except ValueError:
        print("Invalid: BLOCKED")
        print("  Reason: Validation failed")


def test_multi_symbol():
    """测试多符号"""
    print("\n" + "=" * 70)
    print("Multi-Symbol Test")
    print("=" * 70)

    market = MarketNode()
    signal = SignalNode()
    risk = RiskNode()
    brain = BrainNode()
    execution = ExecutionNode()

    for node in [market, signal, risk, brain, execution]:
        node.init()

    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]

    print(f"\nProcessing {len(symbols)} symbols...")

    results = []
    for symbol in symbols:
        # 市场数据
        market_out = market.run(
            {
                "raw_feed": {
                    "symbol": symbol,
                    "price": 100 + hash(symbol) % 1000,
                    "volume": 10 + len(symbol),
                    "timestamp": 1714281600,
                }
            }
        )

        # 信号
        signal_out = signal.run({"ohlcv": market_out["ohlcv"], "market_phase": market_out["phase"]})

        # 风险
        risk_out = risk.run({"signal": signal_out["signal"], "portfolio": execution.get_portfolio()})

        # 决策
        brain_out = brain.run(
            {
                "signal": signal_out["signal"],
                "risk_evaluation": {
                    "approved": risk_out["risk_approved_signal"] is not None,
                    "approved_size": (
                        risk_out["risk_approved_signal"]["approved_size"] if risk_out["risk_approved_signal"] else 0
                    ),
                    "risk_score": (
                        risk_out["risk_approved_signal"]["risk_score"] if risk_out["risk_approved_signal"] else 1
                    ),
                },
                "market_phase": market_out["phase"],
            }
        )

        # 执行
        exec_out = execution.run({"decision": brain_out["decision"]})

        results.append(
            {
                "symbol": symbol,
                "signal": signal_out["signal"]["direction"],
                "decision": brain_out["decision"]["action"],
                "executed": exec_out["order"] is not None,
            }
        )

        print(f"  {symbol}: signal={signal_out['signal']['direction']}, decision={brain_out['decision']['action']}")

    # 汇总
    executed = sum(1 for r in results if r["executed"])
    print(f"\nSummary: {executed}/{len(symbols)} executed")

    # 投资组合
    portfolio = execution.get_portfolio()
    print(f"Portfolio: total={portfolio['total_value']:.2f}")


def test_ai_readable_export():
    """测试 AI 可读导出"""
    print("\n" + "=" * 70)
    print("AI-Readable State Export")
    print("=" * 70)

    market = MarketNode()
    market.init()
    market.run({"raw_feed": {"symbol": "BTCUSDT", "price": 50000, "volume": 100, "timestamp": 1714281600}})

    # 导出状态
    state = market.export_state()

    print("\nState export contains:")
    print(f"  node: {state['node']}")
    print(f"  state: {state['state']['capsule_state']} / {state['state']['phase']}")
    print("  schemas:")
    print(f"    inputs: {list(state['schemas']['inputs'].keys())}")
    print(f"    outputs: {list(state['schemas']['outputs'].keys())}")
    print(f"    constraints: {list(state['schemas']['constraints'].keys())}")
    print(f"  metrics: {state['metrics']}")


if __name__ == "__main__":
    tests = [
        ("Full Pipeline", test_full_pipeline),
        ("Schema Validation", test_schema_validation_at_each_step),
        ("Multi-Symbol", test_multi_symbol),
        ("AI-Readable Export", test_ai_readable_export),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed, None))
        except Exception as e:
            results.append((name, False, str(e)))

    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)

    for name, passed, error in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}: {name}")
        if error:
            print(f"       Error: {error}")

    all_passed = all(r[1] for r in results)
    print("\n" + ("All tests passed!" if all_passed else "Some tests failed"))
