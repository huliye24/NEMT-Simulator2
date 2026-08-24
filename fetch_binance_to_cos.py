# Copyright 2026 NEMT Lab
"""
Binance K线数据采集与 COS 存储 (优化版)

功能:
- 从 Binance 公开 API 获取 K线数据
- 数据校验: 连续性检查 + 价格合理性验证
- 原子上传: 直接上传到 COS
- 索引文件: _index.json 记录各交易对更新时间

使用:
    python fetch_binance_to_cos.py           # 单次采集
    python fetch_binance_to_cos.py --daemon  # 持续运行
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 第三方库
try:
    from dotenv import load_dotenv
except ImportError:
    print("请安装 dotenv: pip install python-dotenv")
    sys.exit(1)

# 导入 COS 工具
from cos_sync import get_client, COS_CONFIG

# 可选依赖
try:
    from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
    HAS_TENACITY = True
except ImportError:
    HAS_TENACITY = False
    print("[WARN] tenacity 未安装，重试功能受限: pip install tenacity")

# 配置
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"]
DATA_DIR = Path("data/market/binance")
COS_PREFIX = "market_data/binance"
MAX_RETRIES = 3

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

# 添加文件日志处理器
try:
    log_file = LOG_DIR / f"fetch_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
except Exception as e:
    logger.warning(f"无法创建日志文件: {e}")


# ==================== Binance API ====================

BINANCE_BASE_URL = "https://api.binance.com"


def fetch_from_binance(symbol: str, interval: str, days: int = 2) -> List[Dict]:
    """从 Binance 获取 K线数据"""
    interval_map = {
        "1m": "1m", "5m": "5m", "15m": "15m",
        "30m": "30m", "1h": "1h", "4h": "4h",
        "1d": "1d", "1w": "1w",
    }
    binance_interval = interval_map.get(interval, "1h")

    # 计算时间范围
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {
        "symbol": symbol.upper(),
        "interval": binance_interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    klines = response.json()

    data = []
    for kline in klines:
        data.append({
            "timestamp": datetime.fromtimestamp(kline[0] / 1000).isoformat(),
            "symbol": symbol,
            "open": float(kline[1]),
            "high": float(kline[2]),
            "low": float(kline[3]),
            "close": float(kline[4]),
            "volume": float(kline[5]),
            "quote_volume": float(kline[7]) if len(kline) > 7 else 0,
            "trades": int(kline[8]) if len(kline) > 8 else 0,
            "timeframe": interval,
            "source": "binance"
        })

    return data


# ==================== 工具函数 ====================

def parse_timestamp(ts) -> float:
    """解析时间戳为 Unix 时间戳"""
    if isinstance(ts, (int, float)):
        return float(ts)
    if isinstance(ts, datetime):
        return ts.timestamp()
    try:
        return datetime.fromisoformat(str(ts).replace('Z', '+00:00')).timestamp()
    except:
        return float(ts)


# ==================== 数据校验 ====================

def validate_klines(data: List[Dict], interval: str) -> tuple[bool, str]:
    """验证 K线数据连续性"""
    if not data or len(data) < 2:
        return False, "数据为空或记录不足"

    interval_seconds = {
        "1m": 60, "5m": 300, "15m": 900,
        "1h": 3600, "4h": 14400, "1d": 86400,
        "1M": 2592000
    }
    expected_gap = interval_seconds.get(interval, 3600)

    prev_ts = parse_timestamp(data[0]['timestamp'])
    gaps = []
    for i in range(1, len(data)):
        curr_ts = parse_timestamp(data[i]['timestamp'])
        gap = curr_ts - prev_ts
        gaps.append(gap)
        if gap > expected_gap * 2:
            return False, f"数据不连续: index={i}, gap={gap}s, expected={expected_gap}s"
        prev_ts = curr_ts

    return True, ""


def validate_price(data: List[Dict]) -> tuple[bool, str]:
    """验证价格合理性"""
    for i, kline in enumerate(data):
        try:
            o, h, l, c = kline['open'], kline['high'], kline['low'], kline['close']
            # 高 >= 开/收/低
            if not (h >= max(o, c) and l <= min(o, c)):
                return False, f"价格关系错误 @ index={i}: O={o}, H={h}, L={l}, C={c}"
            # 所有价格为正
            if not all(p > 0 for p in [o, h, l, c]):
                return False, f"非正价格 @ index={i}"
            # 涨跌幅合理 (单根 K线不超过 100%)
            if o > 0:
                change = abs(c - o) / o
                if change > 1.0:
                    return False, f"异常涨跌 @ index={i}: {change:.1%}"
        except (KeyError, TypeError, ValueError) as e:
            return False, f"数据解析错误 @ index={i}: {e}"
    return True, ""


# ==================== COS 操作 ====================

def upload_atomic(client, local_path: Path, cos_key: str) -> bool:
    """
    原子上传: 直接上传到正式路径
    SDK 的 upload_file 内部会处理分片上传的原子性
    """
    bucket = COS_CONFIG['Bucket']

    try:
        # 直接上传到正式文件 (SDK 内部保证原子性)
        client.upload_file(
            Bucket=bucket,
            Key=cos_key,
            LocalFilePath=str(local_path)
        )
        logger.debug(f"上传文件: {cos_key}")
        return True

    except Exception as e:
        raise


def save_local(data: List[Dict], symbol: str, interval: str) -> Path:
    """保存到本地文件"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{symbol}_{interval}_{timestamp}.json"
    filepath = DATA_DIR / filename

    payload = {
        "meta": {
            "symbol": symbol,
            "interval": interval,
            "fetched_at": datetime.now().isoformat(),
            "count": len(data),
            "version": "1.0"
        },
        "data": data
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return filepath


def update_index(symbol: str, interval: str, count: int, timestamp: str = None):
    """更新索引文件"""
    index_key = f"{COS_PREFIX}/_index.json"
    timestamp = timestamp or datetime.now().isoformat()

    try:
        client = get_client()
        resp = client.get_object(Bucket=COS_CONFIG['Bucket'], Key=index_key)
        index = json.loads(resp['Body'].read())
    except:
        index = {"version": "1.0", "updated_at": None, "symbols": {}}

    if symbol not in index["symbols"]:
        index["symbols"][symbol] = {}

    index["symbols"][symbol][interval] = {
        "count": count,
        "updated_at": timestamp,
        "status": "ok"
    }
    index["updated_at"] = timestamp

    # 写入临时文件再上传
    temp_path = DATA_DIR / "temp_index.json"
    with open(temp_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    upload_atomic(client, temp_path, index_key)


# ==================== 采集逻辑 ====================

@dataclass
class FetchResult:
    """采集结果"""
    symbol: str
    interval: str
    success: bool
    records: int = 0
    cos_key: str = ""
    error: str = ""
    duration_ms: float = 0


@dataclass
class FetchStats:
    """采集统计"""
    total: int = 0
    success: int = 0
    failed: int = 0
    total_records: int = 0
    start_time: datetime = None

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.now()

    @property
    def success_rate(self) -> float:
        return self.success / self.total if self.total > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "total_records": self.total_records,
            "success_rate": f"{self.success_rate:.1%}",
            "elapsed_seconds": elapsed
        }


def fetch_single(symbol: str, interval: str) -> FetchResult:
    """采集单个交易对的 K线数据"""
    start_time = time.time()
    result = FetchResult(symbol=symbol, interval=interval, success=False)

    try:
        logger.info(f"Fetching {symbol}/{interval}...")

        # 1. 获取数据
        data = fetch_from_binance(symbol, interval, days=2)

        if not data:
            result.error = "无数据返回"
            return result

        # 2. 数据校验
        valid, msg = validate_klines(data, interval)
        if not valid:
            result.error = f"连续性校验失败: {msg}"
            return result

        valid, msg = validate_price(data)
        if not valid:
            result.error = f"价格校验失败: {msg}"
            return result

        # 3. 保存本地
        local_path = save_local(data, symbol, interval)
        logger.debug(f"本地保存: {local_path}")

        # 4. 上传 COS
        cos_key = f"{COS_PREFIX}/{symbol}/{interval}/latest.json"
        client = get_client()
        upload_atomic(client, local_path, cos_key)

        # 5. 更新索引
        update_index(symbol, interval, len(data))

        # 6. 清理本地文件
        try:
            local_path.unlink()
        except:
            pass

        result.success = True
        result.records = len(data)
        result.cos_key = cos_key
        result.duration_ms = (time.time() - start_time) * 1000

        logger.info(f"OK {symbol}/{interval}: {len(data)} records ({result.duration_ms:.0f}ms)")

    except Exception as e:
        result.error = str(e)
        logger.error(f"FAIL {symbol}/{interval}: {e}")

    return result


def fetch_all(symbols: List[str] = None, intervals: List[str] = None) -> FetchStats:
    """采集所有配置的交易对和时间周期"""
    symbols = symbols or SYMBOLS
    intervals = intervals or INTERVALS

    stats = FetchStats()
    results = []

    for symbol in symbols:
        for interval in intervals:
            stats.total += 1
            result = fetch_single(symbol, interval)
            results.append(result)

            if result.success:
                stats.success += 1
                stats.total_records += result.records
            else:
                stats.failed += 1

            # 避免请求过快
            time.sleep(1)

    # 报告
    logger.info(f"=== 采集完成 ===")
    logger.info(f"总计: {stats.total}, 成功: {stats.success}, 失败: {stats.failed}")
    logger.info(f"总记录数: {stats.total_records}, 成功率: {stats.success_rate:.1%}")

    return stats


# ==================== 告警 ====================

def check_health(stats: FetchStats):
    """健康检查 - 采集成功率"""
    if stats.total > 0 and stats.success_rate < 0.8:
        send_alert(
            title="Binance 数据采集失败",
            message=f"成功率仅 {stats.success_rate:.0%}，请检查网络或API"
        )


def send_alert(title: str, message: str):
    """发送告警"""
    alert_log = DATA_DIR / "alerts.log"
    with open(alert_log, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now()}] {title}: {message}\n")

    # Webhook 告警 (可选)
    webhook_url = os.getenv("ALERT_WEBHOOK_URL")
    if webhook_url:
        try:
            import requests
            requests.post(webhook_url, json={"text": f"{title}\n{message}"}, timeout=5)
        except Exception as e:
            logger.warning(f"Webhook 发送失败: {e}")


# ==================== 定时调度 ====================

def run_scheduler(interval_minutes: int = 60):
    """持续运行的调度器"""
    import schedule

    def job():
        logger.info(f"\n{'='*50}")
        logger.info(f"[{datetime.now()}] 开始定时采集...")
        stats = fetch_all()
        save_stats(stats)
        if stats.failed > 0:
            check_health(stats)

    # 定时任务
    schedule.every(interval_minutes).minutes.do(job)

    # 立即执行一次
    job()

    # 持续运行
    logger.info(f"调度器已启动，每 {interval_minutes} 分钟执行一次")
    while True:
        schedule.run_pending()
        time.sleep(60)


def save_stats(stats: FetchStats):
    """保存统计到文件"""
    stats_file = DATA_DIR / "stats.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats.to_dict(), f, indent=2, ensure_ascii=False)


# ==================== 主入口 ====================

def main():
    parser = argparse.ArgumentParser(description="Binance K线数据采集与 COS 存储")
    parser.add_argument('--daemon', action='store_true', help='持续运行模式')
    parser.add_argument('--interval', type=int, default=60, help='调度间隔(分钟)')
    parser.add_argument('--symbol', type=str, help='指定交易对')
    parser.add_argument('--tf', '--timeframe', dest='timeframe', type=str, help='指定时间周期')

    args = parser.parse_args()

    # 检查 COS 配置
    if not COS_CONFIG.get('SecretId'):
        logger.error("COS 配置不完整，请检查 cos_sync.env")
        sys.exit(1)

    if args.daemon:
        run_scheduler(interval_minutes=args.interval)
    else:
        symbols = [args.symbol] if args.symbol else None
        intervals = [args.timeframe] if args.timeframe else None
        fetch_all(symbols=symbols, intervals=intervals)


if __name__ == "__main__":
    main()
