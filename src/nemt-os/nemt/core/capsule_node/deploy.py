"""
CapsuleNode 部署脚本

启动和管理 CapsuleNode 系统的运行
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from capsules import BrainNode, ExecutionNode, MarketNode, RiskNode, SignalNode
from tools.node_manager import PipelineNodeManager
from tools.state_exporter import StateExporter


def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_config(config_path: str = None):
    """加载配置"""
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")

    if os.path.exists(config_path):
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def create_pipeline_manager(config: dict = None) -> PipelineNodeManager:
    """创建 Pipeline 管理器"""
    manager = PipelineNodeManager()

    # 注册节点
    manager.register(MarketNode, "market")
    manager.register(SignalNode, "signal")
    manager.register(RiskNode, "risk")
    manager.register(BrainNode, "brain")
    manager.register(ExecutionNode, "execution")

    # 定义流程
    manager.define_pipeline(
        [
            ("market", "signal"),
            ("signal", "risk"),
            ("risk", "brain"),
            ("brain", "execution"),
        ]
    )

    return manager


def run_single_tick(manager: PipelineNodeManager, tick_data: dict) -> dict:
    """运行单次 tick"""
    return manager.execute_pipeline(tick_data)


def run_simulation(manager: PipelineNodeManager, ticks: int = 100, interval: float = 1.0):
    """运行模拟"""
    import time

    logger = logging.getLogger("CapsuleNode.Simulation")

    logger.info(f"Starting simulation: {ticks} ticks, {interval}s interval")

    results = []

    for i in range(ticks):
        # 生成 tick 数据
        tick_data = {
            "raw_feed": {
                "symbol": "BTCUSDT",
                "price": 50000 + (i % 100) * 10,
                "volume": 100 + i,
                "timestamp": int(datetime.now().timestamp()),
            }
        }

        # 执行
        result = run_single_tick(manager, tick_data)
        results.append(result)

        # 打印状态
        if "execution" in result:
            portfolio = result["execution"].get("portfolio", {})
            logger.info(f"Tick {i+1}: Portfolio={portfolio.get('total_value', 0):.2f}")

        # 等待
        if i < ticks - 1:
            time.sleep(interval)

    # 最终状态
    status = manager.get_status()
    logger.info(f"Simulation complete. Final status: {status}")

    return results


def export_all_states(manager: PipelineNodeManager, output_dir: str = "exports"):
    """导出所有节点状态"""
    os.makedirs(output_dir, exist_ok=True)

    exporter = StateExporter()

    for node_id in manager.list_nodes():
        node = manager.get(node_id)
        if node:
            filepath = os.path.join(output_dir, f"{node_id}_state.md")
            exporter.save(node, filepath, format="md")
            print(f"Exported: {filepath}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="CapsuleNode Deployment")

    parser.add_argument(
        "--mode", choices=["init", "run", "simulate", "status", "export"], default="status", help="运行模式"
    )

    parser.add_argument("--config", type=str, help="配置文件路径")

    parser.add_argument("--ticks", type=int, default=100, help="模拟 tick 数量")

    parser.add_argument("--interval", type=float, default=1.0, help="tick 间隔（秒）")

    parser.add_argument("--output", type=str, default="exports", help="导出目录")

    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="日志级别")

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger("CapsuleNode")

    # 加载配置
    config = load_config(args.config)

    # 创建管理器
    manager = create_pipeline_manager(config)

    if args.mode == "init":
        # 初始化
        logger.info("Initializing nodes...")
        manager.init_all()
        logger.info("Nodes initialized")
        print(json.dumps(manager.get_status(), indent=2, default=str))

    elif args.mode == "run":
        # 运行
        logger.info("Initializing and running...")
        manager.init_all()
        manager.start_all()

        try:
            # 运行一次
            result = manager.execute_pipeline(
                {
                    "raw_feed": {
                        "symbol": "BTCUSDT",
                        "price": 50000,
                        "volume": 100,
                        "timestamp": int(datetime.now().timestamp()),
                    }
                }
            )
            print(json.dumps(result, indent=2, default=str))
        finally:
            manager.shutdown_all()

    elif args.mode == "simulate":
        # 模拟
        logger.info(f"Starting simulation: {args.ticks} ticks")
        manager.init_all()
        manager.start_all()

        try:
            results = run_simulation(manager, args.ticks, args.interval)
            print(f"\nSimulation complete. Processed {len(results)} ticks.")
        finally:
            manager.shutdown_all()

    elif args.mode == "status":
        # 状态
        logger.info("Getting status...")
        manager.init_all()
        status = manager.get_status()
        print(json.dumps(status, indent=2, default=str))
        manager.shutdown_all()

    elif args.mode == "export":
        # 导出
        logger.info(f"Exporting states to {args.output}...")
        manager.init_all()
        export_all_states(manager, args.output)
        manager.shutdown_all()
        print(f"Exported to: {args.output}")


if __name__ == "__main__":
    main()
