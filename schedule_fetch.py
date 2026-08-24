# Copyright 2026 NEMT Lab
"""
数据采集调度脚本

功能:
- 每小时执行一次 Binance 数据采集
- 记录执行日志和统计
- 支持作为系统服务运行

使用:
    python schedule_fetch.py              # 前台运行
    python schedule_fetch.py --daemon     # 后台守护进程
    python schedule_fetch.py --once       # 单次执行
"""

import os
import sys
import json
import time
import logging
import argparse
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from threading import Thread, Event

# 路径配置
SCRIPT_DIR = Path(__file__).parent
FETCH_SCRIPT = SCRIPT_DIR / "fetch_binance_to_cos.py"
DATA_DIR = Path("data/market/binance")
LOG_DIR = DATA_DIR / "logs"
PID_FILE = DATA_DIR / "scheduler.pid"

# 日志配置
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class SchedulerService:
    """调度服务"""

    def __init__(self, interval_hours: float = 1.0):
        self.interval_hours = interval_hours
        self.interval_seconds = interval_hours * 3600
        self.stop_event = Event()
        self.is_running = False

    def run_fetch(self) -> dict:
        """执行采集任务"""
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info(f"[{start_time}] 开始采集任务...")

        try:
            # 导入并执行采集
            sys.path.insert(0, str(SCRIPT_DIR))
            from fetch_binance_to_cos import fetch_all, save_stats

            stats = fetch_all()
            save_stats(stats)

            elapsed = (datetime.now() - start_time).total_seconds()

            result = {
                "success": True,
                "elapsed_seconds": elapsed,
                "stats": stats.to_dict()
            }

            logger.info(f"采集完成，耗时 {elapsed:.1f}s")
            return result

        except Exception as e:
            logger.error(f"采集失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def save_run_history(self, result: dict):
        """保存执行历史"""
        history_file = LOG_DIR / "history.json"

        # 读取历史
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []

        # 添加新记录
        record = {
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", False),
            "elapsed_seconds": result.get("elapsed_seconds", 0),
            "error": result.get("error", "")
        }

        if "stats" in result:
            record["stats"] = result["stats"]

        history.append(record)

        # 只保留最近 100 条
        history = history[-100:]

        # 写入
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def run_loop(self):
        """主循环"""
        self.is_running = True
        next_run = datetime.now()

        logger.info(f"调度服务已启动，间隔: {self.interval_hours} 小时")
        logger.info(f"下次执行: {next_run + timedelta(seconds=self.interval_seconds)}")

        while not self.stop_event.is_set():
            now = datetime.now()

            if now >= next_run:
                result = self.run_fetch()
                self.save_run_history(result)
                next_run = now + timedelta(seconds=self.interval_seconds)

            # 每分钟检查一次
            time.sleep(60)

        self.is_running = False
        logger.info("调度服务已停止")

    def start(self):
        """启动服务"""
        # 检查是否已运行
        if self.is_running:
            logger.warning("服务已在运行中")
            return

        # 保存 PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        # 注册信号处理
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，停止服务...")
            self.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 启动线程
        thread = Thread(target=self.run_loop, daemon=True)
        thread.start()

        return thread

    def stop(self):
        """停止服务"""
        self.stop_event.set()


def check_status():
    """检查服务状态"""
    print("\n=== Binance 数据采集服务状态 ===\n")

    # 检查 PID
    if PID_FILE.exists():
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        try:
            os.kill(pid, 0)
            print(f"服务运行中: PID {pid}")
        except OSError:
            print("服务未运行 (PID 文件存在但进程不存在)")
            PID_FILE.unlink()
    else:
        print("服务未运行")

    # 检查历史
    history_file = LOG_DIR / "history.json"
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

        if history:
            last = history[-1]
            print(f"\n最近执行: {last['timestamp']}")
            print(f"状态: {'成功' if last['success'] else '失败'}")
            print(f"耗时: {last.get('elapsed_seconds', 0):.1f}s")

            if 'stats' in last:
                stats = last['stats']
                print(f"成功率: {stats.get('success_rate', 'N/A')}")
                print(f"总记录: {stats.get('total_records', 0)}")

    # 检查统计数据
    stats_file = DATA_DIR / "stats.json"
    if stats_file.exists():
        print("\n--- 统计信息 ---")
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        for k, v in stats.items():
            print(f"  {k}: {v}")

    print()


def run_once():
    """单次执行"""
    service = SchedulerService()
    result = service.run_fetch()
    service.save_run_history(result)
    return result["success"]


def main():
    parser = argparse.ArgumentParser(description="Binance 数据采集调度器")
    parser.add_argument('--daemon', action='store_true', help='后台守护进程模式')
    parser.add_argument('--once', action='store_true', help='单次执行')
    parser.add_argument('--status', action='store_true', help='查看状态')
    parser.add_argument('--interval', type=float, default=1.0, help='执行间隔(小时，默认1小时)')

    args = parser.parse_args()

    if args.status:
        check_status()
        return

    if args.once:
        success = run_once()
        sys.exit(0 if success else 1)

    if args.daemon:
        service = SchedulerService(interval_hours=args.interval)
        service.start()

        # 保持主线程
        try:
            while service.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            service.stop()
    else:
        # 前台运行模式
        service = SchedulerService(interval_hours=args.interval)
        try:
            service.run_loop()
        except KeyboardInterrupt:
            logger.info("收到中断信号，退出...")
            service.stop_event.set()


# 辅助函数
from datetime import timedelta


if __name__ == "__main__":
    main()
