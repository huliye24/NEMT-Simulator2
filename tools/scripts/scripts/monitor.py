"""
NEMT 系统监控脚本

监控 NEMT 系统的运行状态。
"""

import os
import sys
import time
import psutil
import argparse
from datetime import datetime
from pathlib import Path


def get_system_info():
    """获取系统信息"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        'cpu': {
            'percent': cpu_percent,
            'count': psutil.cpu_count(),
        },
        'memory': {
            'total': memory.total,
            'used': memory.used,
            'percent': memory.percent,
            'available': memory.available,
        },
        'disk': {
            'total': disk.total,
            'used': disk.used,
            'percent': disk.percent,
            'free': disk.free,
        }
    }


def format_bytes(bytes_value):
    """格式化字节"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.2f} PB"


def print_system_info(info):
    """打印系统信息"""
    print("\n" + "=" * 50)
    print(f"系统监控 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    print("\n[CPU]")
    print(f"  使用率: {info['cpu']['percent']:.1f}%")
    print(f"  核心数: {info['cpu']['count']}")

    print("\n[内存]")
    print(f"  总计:   {format_bytes(info['memory']['total'])}")
    print(f"  已使用: {format_bytes(info['memory']['used'])} ({info['memory']['percent']:.1f}%)")
    print(f"  可用:   {format_bytes(info['memory']['available'])}")

    print("\n[磁盘]")
    print(f"  总计:   {format_bytes(info['disk']['total'])}")
    print(f"  已使用: {format_bytes(info['disk']['used'])} ({info['disk']['percent']:.1f}%)")
    print(f"  可用:   {format_bytes(info['disk']['free'])}")


def monitor_nemt_process():
    """监控 NEMT 进程"""
    print("\n[NEMT 进程]")

    current_pid = os.getpid()
    process = psutil.Process(current_pid)

    print(f"  PID: {process.pid}")
    print(f"  名称: {process.name()}")
    print(f"  状态: {process.status()}")
    print(f"  CPU:  {process.cpu_percent(interval=0.1):.1f}%")
    print(f"  内存: {format_bytes(process.memory_info().rss)}")
    print(f"  线程: {process.num_threads()}")


def check_port(port):
    """检查端口占用"""
    print(f"\n[端口 {port}]")

    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            print(f"  监听中: {conn.laddr}")
            return True

    print("  未被占用")
    return False


def check_logs(log_dir, lines=20):
    """检查日志"""
    print(f"\n[最近日志 ({lines} 行)]")

    log_path = Path(log_dir)
    if not log_path.exists():
        print("  日志目录不存在")
        return

    log_files = list(log_path.glob("*.log"))
    if not log_files:
        print("  没有日志文件")
        return

    # 获取最新的日志文件
    latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
    print(f"  文件: {latest_log.name}")

    # 读取最后几行
    with open(latest_log, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

    for line in last_lines:
        print(f"  {line.rstrip()}")


def continuous_monitor(interval=5, duration=None):
    """持续监控"""
    print("开始持续监控...")
    print(f"间隔: {interval}秒")
    if duration:
        print(f"持续: {duration}秒")
    print("按 Ctrl+C 停止\n")

    start_time = time.time()

    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')

            info = get_system_info()
            print_system_info(info)
            monitor_nemt_process()

            if duration and (time.time() - start_time) >= duration:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n监控已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='NEMT 系统监控')
    parser.add_argument('--interval', '-i', type=int, default=5,
                       help='监控间隔 (秒)')
    parser.add_argument('--duration', '-d', type=int, default=None,
                       help='监控持续时间 (秒)')
    parser.add_argument('--once', '-o', action='store_true',
                       help='只显示一次')
    parser.add_argument('--logs', '-l', type=str, default='logs',
                       help='日志目录')
    parser.add_argument('--port', '-p', type=int, default=None,
                       help='检查端口')

    args = parser.parse_args()

    if args.once:
        # 单次监控
        info = get_system_info()
        print_system_info(info)
        monitor_nemt_process()

        if args.port:
            check_port(args.port)

        if args.logs:
            check_logs(args.logs)

    else:
        # 持续监控
        continuous_monitor(args.interval, args.duration)


if __name__ == '__main__':
    main()
