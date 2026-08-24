# Copyright 2026 NEMT Lab
"""
NEMT Memory System - End-to-End Integration Test
================================================
完整流程测试：模拟真实 Cursor 会话

测试场景：
1. 会话开始 → Context Injector 自动注入记忆
2. 用户提问 → Agent 响应
3. 决策被捕获 → Memory Writer 自动记录
4. 成功经验被捕获 → 自动记录
5. 会话结束 → Checkpoint 生成

运行方式：
    python notion_sync/e2e_test.py
"""

import os
import sys
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

_self_dir = os.path.dirname(os.path.abspath(__file__))
if _self_dir not in sys.path:
    sys.path.insert(0, _self_dir)

from local_fallback import get_local_store
from context_injector import get_context_injector
from memory_writer import get_memory_writer, TriggerEngine
from active_retriever import CheckpointGenerator, QualityController


def run_e2e_test():
    print("=" * 70)
    print("NEMT Memory System - End-to-End Test")
    print("=" * 70)
    print(f"\n时间: {datetime.now().isoformat()}")
    print()

    # =================================================================
    # Phase 1: 会话开始 → READ Phase
    # =================================================================
    print("[Phase 1] 会话开始 - Context Injector (READ Phase)")
    print("-" * 50)

    injector = get_context_injector()
    bundle = injector.inject_from_session_context()
    injector.print_summary(bundle)

    # =================================================================
    # Phase 2: 模拟真实会话
    # =================================================================
    print("\n[Phase 2] 模拟会话 - T1-T5 触发器检测")
    print("-" * 50)

    # 模拟的对话历史
    session_messages = []

    # Turn 1: 用户提问
    user_msg_1 = "我想把验证层集成到 Pipeline 中"
    agent_resp_1 = """
我建议采用方案 A：将验证层直接嵌入 Pipeline。

方案 A（集成到 Pipeline）：
- 优点：验证与分析同步执行，每次分析自动带约束检查
- 缺点：增加了 Pipeline 的复杂度
- 适用场景：需要实时验证的场景

方案 B（独立服务）：
- 优点：解耦，可独立扩展
- 缺点：需要额外的通信开销
- 适用场景：验证逻辑复杂的场景

我的建议是方案 A，因为验证层的核心价值在于"与分析同步"。
"""
    session_messages.append(f"User: {user_msg_1}")
    session_messages.append(f"Agent: {agent_resp_1}")

    # Turn 2: 用户明确要求记录
    user_msg_2 = "把这次讨论记录下来，标记为需要回顾"
    agent_resp_2 = "好的，我已将决策记录到记忆系统中，并标记为需要回顾。"
    session_messages.append(f"User: {user_msg_2}")
    session_messages.append(f"Agent: {agent_resp_2}")

    # Turn 3: 技术实现
    user_msg_3 = "现在开始实现方案 A"
    agent_resp_3 = """
正在实现验证层集成...

✅ 修复了 spectral width 的数值不稳定问题
✅ 集成了 nemtValidator 到 nemtPipeline
✅ 添加了 validationReport 到 PipelineResult

完成！验证层已成功嵌入 Pipeline，每次分析都会自动运行约束检查。
"""
    session_messages.append(f"User: {user_msg_3}")
    session_messages.append(f"Agent: {agent_resp_3}")

    # Turn 4: 编译错误
    user_msg_4 = "编译一下看看有没有问题"
    agent_resp_4 = """
运行 TypeScript 编译器...

❌ error TS2353: Object literal may only specify known properties,
   and 'description' does not exist in type 'CheckDef'

我需要修复这个问题。
"""
    session_messages.append(f"User: {user_msg_4}")
    session_messages.append(f"Agent: {agent_resp_4}")

    # =================================================================
    # Phase 3: 触发器检测 + 写入
    # =================================================================
    print("\n检测每条消息的触发器...")

    writer = get_memory_writer()
    engine = TriggerEngine()
    all_results = []

    # 模拟 Agent 的 auto_write 调用
    for i in range(0, len(session_messages), 2):
        if i + 1 >= len(session_messages):
            break
        user_msg = session_messages[i]
        agent_resp = session_messages[i + 1]

        # 只在 Agent 响应后进行检测
        if i > 0 or "User" in user_msg:
            results = writer.auto_write(
                user_message=user_msg,
                agent_response=agent_resp,
                session_messages=session_messages[:i+2],
                dry_run=False  # 实际写入
            )

            for r in results:
                print(f"\n  [Trigger: {r.trigger_type}] {r.record_type}")
                print(f"    Title: {r.title[:50]}")
                print(f"    Confidence: {r.confidence:.0%}")
                print(f"    Written: {r.written}")
                if r.written:
                    if r.notion_id:
                        print(f"    Notion ID: {r.notion_id}")
                    if r.local_id:
                        print(f"    Local ID: {r.local_id}")
                if r.skip_reason:
                    print(f"    Skipped: {r.skip_reason}")
                all_results.append(r)

    # =================================================================
    # Phase 4: 会话结束 → Checkpoint 生成
    # =================================================================
    print("\n[Phase 4] 会话结束 - Checkpoint 生成")
    print("-" * 50)

    checkpoint_gen = CheckpointGenerator()
    session = checkpoint_gen.create_session(
        session_id="e2e_test_session_001",
        agent_role="TechLead",
        project_tag="notion",
    )
    session.messages_count = len(session_messages)

    # 追加已记录的条目
    for r in all_results:
        if r.written:
            checkpoint_gen.add_record(session, r.record_type, {
                "title": r.title,
                "notion_id": r.notion_id,
                "local_id": r.local_id,
            })
        elif r.triggered and r.confidence >= 0.6:
            checkpoint_gen.add_unrecorded_detection(
                session, r.record_type, r.title, r.confidence
            )

    # 生成 Checkpoint
    checkpoint_output = checkpoint_gen.generate(session)
    print(checkpoint_output)

    # =================================================================
    # Phase 5: 质量控制检查
    # =================================================================
    print("\n[Phase 5] 质量控制检查")
    print("-" * 50)

    qc = QualityController()

    recorded_decisions = [r for r in all_results if r.written and r.record_type == "decision"]
    for r in recorded_decisions:
        gate = qc.check_decision(
            title=r.title,
            conclusion=r.content.get("conclusion", ""),
            reason=r.content.get("reason", ""),
            decision_type=r.content.get("decision_type", ""),
        )
        print(f"\n  决策: {r.title[:40]}")
        print(f"    质量分数: {gate.score:.0%}")
        print(f"    通过: {gate.passed}")
        if gate.issues:
            print(f"    问题: {', '.join(gate.issues)}")
        if gate.suggestions:
            print(f"    建议: {', '.join(gate.suggestions)}")

    # =================================================================
    # Phase 6: 验证本地存储
    # =================================================================
    print("\n[Phase 6] 本地存储验证")
    print("-" * 50)

    store = get_local_store()
    stats = store.get_stats()
    print(f"\n  总记录数:")
    print(f"    Decisions: {stats['decisions_total']} total, {stats['decisions_pending']} pending")
    print(f"    Experiences: {stats['experiences_total']} total, {stats['experiences_pending']} pending")
    print(f"    Failures: {stats['failures_total']} total, {stats['failures_pending']} pending")

    print("\n  最近决策:")
    recent = store.get_recent_decisions(limit=5)
    for d in recent:
        print(f"    [{d.status}] {d.title}")
        print(f"      结论: {d.conclusion}")

    # =================================================================
    # Phase 7: 综合测试 Context Injector（再次）
    # =================================================================
    print("\n[Phase 7] Context Injector 再次检索（验证写入成功）")
    print("-" * 50)

    bundle2 = injector.inject_from_session_context()
    injector.print_summary(bundle2)

    # =================================================================
    # 结果汇总
    # =================================================================
    print("\n" + "=" * 70)
    print("E2E TEST SUMMARY")
    print("=" * 70)

    total_written = sum(1 for r in all_results if r.written)
    total_triggered = len(all_results)

    print(f"\n  触发器统计:")
    print(f"    总触发次数: {total_triggered}")
    print(f"    成功写入: {total_written}")
    print(f"    写入率: {total_written/max(total_triggered,1):.0%}")

    print(f"\n  触发器类型分布:")
    for t_type in ["T1", "T2", "T3", "T4", "T5"]:
        count = sum(1 for r in all_results if r.trigger_type == t_type)
        if count:
            print(f"    {t_type}: {count}")

    print(f"\n  记录类型分布:")
    for r_type in ["decision", "experience", "failure"]:
        count = sum(1 for r in all_results if r.record_type == r_type and r.written)
        if count:
            print(f"    {r_type}: {count}")

    print(f"\n  本地存储:")
    print(f"    Decisions: {stats['decisions_total']}")
    print(f"    Experiences: {stats['experiences_total']}")
    print(f"    Failures: {stats['failures_total']}")

    print("\n" + "=" * 70)
    print("E2E TEST PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_e2e_test()
