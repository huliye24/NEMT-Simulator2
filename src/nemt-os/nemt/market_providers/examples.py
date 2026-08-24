"""
市场数据使用示例
展示如何使用不同的数据源加载和处理市场数据
"""

from datetime import datetime, timedelta

# =============================================================================
# 示例 1: 使用 Binance API 获取真实数据
# =============================================================================


def example_binance_api():
    """
    展示如何使用 Binance API 获取真实市场数据
    """
    print("=" * 60)
    print("示例 1: Binance API 获取真实数据")
    print("=" * 60)

    from nemt.market_providers import BinanceMarketProvider, fetch_binance_data

    # 方式 1: 直接使用便捷函数
    print("\n--- 方式 1: fetch_binance_data 便捷函数 ---")
    klines = fetch_binance_data(symbol="BTCUSDT", interval="1h", days=7, save_csv="btc_binance_data.csv")
    print(f"获取到 {len(klines)} 条K线")
    if klines:
        print(f"最新价格: {klines[-1].close}")

    # 方式 2: 使用 Provider 类 (更多控制)
    print("\n--- 方式 2: BinanceMarketProvider 类 ---")
    provider = BinanceMarketProvider(symbols=["BTCUSDT", "ETHUSDT"], default_interval="1h")

    if provider.connect():
        # 获取历史数据
        btc_klines = provider.get_history("BTCUSDT", "1h", limit=100)
        print(f"BTC 历史数据: {len(btc_klines)} 条")

        # 获取最新K线
        latest = provider.get_latest("BTCUSDT")
        if latest:
            print(f"最新K线: {latest.close}")

        # 获取实时行情
        ticker = provider.get_ticker("BTCUSDT")
        if ticker:
            print(f"24h涨跌: {ticker.change_pct_24h:.2f}%")

        # 启动 WebSocket 实时流 (非阻塞)
        # provider.subscribe_websocket(["BTCUSDT"], ["1h"])
        # print("WebSocket 已启动，实时接收数据中...")

        provider.disconnect()
    else:
        print("连接失败，请检查网络")


# =============================================================================
# 示例 2: 使用 CSV 文件加载本地数据
# =============================================================================


def example_csv_file():
    """
    展示如何使用 CSV 文件加载本地数据
    """
    print("\n" + "=" * 60)
    print("示例 2: CSV 文件加载")
    print("=" * 60)

    from nemt.market_providers import CSVFileProvider, CSVConfig, load_csv_data

    # 方式 1: 使用便捷函数
    print("\n--- 方式 1: load_csv_data 便捷函数 ---")
    klines = load_csv_data(filepath="matlab_data/BTC.csv", symbol="BTC")
    print(f"加载了 {len(klines)} 条K线")
    if klines:
        print(f"时间范围: {klines[0].timestamp} ~ {klines[-1].timestamp}")

    # 方式 2: 使用 Provider 类 (支持文件监视)
    print("\n--- 方式 2: CSVFileProvider 类 (带文件监视) ---")
    config = CSVConfig(
        filepath="matlab_data/BTC.csv",
        default_symbol="BTC",
        timestamp_col="timestamp",
        open_col="open",
        high_col="high",
        low_col="low",
        close_col="close",
        volume_col="volume",
    )

    provider = CSVFileProvider(config=config, auto_watch=True)

    if provider.connect():
        print(f"已连接，等待文件更新...")

        # 获取历史数据
        history = provider.get_history(limit=100)
        print(f"历史数据: {len(history)} 条")

        # 设置新数据回调
        def on_new_bar(kline):
            print(f"新数据: {kline.timestamp} close={kline.close}")

        provider.set_on_new_bar(on_new_bar)

        # 注意: 文件监视在后台运行
        # 当CSV文件追加新行时，会自动触发回调
        # time.sleep(60)  # 等待一分钟

        provider.disconnect()


# =============================================================================
# 示例 3: 使用 Mock 数据进行测试
# =============================================================================


def example_mock_data():
    """
    展示如何使用 Mock 数据进行测试
    """
    print("\n" + "=" * 60)
    print("示例 3: Mock 数据测试")
    print("=" * 60)

    from nemt.market_providers import MockMarketProvider

    provider = MockMarketProvider(base_prices={"BTCUSDT": 67000.0, "ETHUSDT": 3400.0}, volatility=0.001)

    provider.connect()

    # 获取模拟历史数据
    klines = provider.get_history("BTCUSDT", "1h", limit=50)
    print(f"生成模拟数据: {len(klines)} 条")
    print(f"示例数据: open={klines[0].open:.2f} close={klines[0].close:.2f}")

    # 获取实时行情
    ticker = provider.get_ticker("BTCUSDT")
    print(f"实时价格: {ticker.price:.2f}")

    provider.disconnect()


# =============================================================================
# 示例 4: 使用 MarketLayer 整合数据
# =============================================================================


def example_market_layer():
    """
    展示如何使用 MarketLayer 整合数据
    """
    print("\n" + "=" * 60)
    print("示例 4: MarketLayer 整合")
    print("=" * 60)

    from nemt.market import MarketLayer, MarketConfig
    from nemt.market_providers import BinanceMarketProvider

    # 创建配置
    config = MarketConfig(name="BTC/USDT", default_interval="1h")

    market = MarketLayer(config=config)

    # 方式 1: 从 CSV 加载
    print("\n--- 从 CSV 加载 ---")
    try:
        market.load_from_csv("matlab_data/BTC.csv")
        print(f"加载数据: {len(market.data)} 条")
    except FileNotFoundError:
        print("CSV文件不存在，跳过")

    # 方式 2: 从 Binance 加载
    print("\n--- 从 Binance 加载 ---")
    provider = BinanceMarketProvider(symbols=["BTCUSDT"])

    try:
        market.load_from_provider(provider, symbol="BTCUSDT", interval="1h", days=7)
        print(f"加载数据: {len(market.data)} 条")
    except Exception as e:
        print(f"加载失败: {e}")

    # 分析市场状态
    if market.data is not None:
        state = market.detect_regime()
        indicators = market.get_market_indicators()
        print(f"\n市场状态: {state.value}")
        print(f"波动率: {indicators.get('volatility', 0):.4f}")
        print(f"趋势强度: {indicators.get('trend_strength', 0):.4f}")


# =============================================================================
# 示例 5: 使用 MarketCapsule 进行回测
# =============================================================================


def example_market_capsule():
    """
    展示如何使用 MarketCapsule 进行回测
    """
    print("\n" + "=" * 60)
    print("示例 5: MarketCapsule 回测")
    print("=" * 60)

    from nemt.core.market_capsule import MarketCapsule

    capsule = MarketCapsule()

    # 方式 1: 加载本地CSV数据
    print("\n--- 加载本地数据回测 ---")
    try:
        capsule.load_data_from_csv("matlab_data/BTC.csv", "BTC")
        print(f"加载了 {len(capsule._bars.get('BTC', []))} 条数据")
    except Exception as e:
        print(f"加载失败: {e}")

    # 方式 2: 从 Binance 加载数据
    print("\n--- 从 Binance 加载数据回测 ---")
    success = capsule.connect_provider(type="binance", symbols=["BTCUSDT"], interval="1h")

    if success:
        count = capsule.load_history_from_provider(symbol="BTCUSDT", interval="1h", days=7)
        print(f"从Binance加载了 {count} 条数据")

        # 开始回测
        capsule.start_backtest()

        step = 0
        while capsule.next_bar():
            step += 1
            if step % 100 == 0:
                print(f"回测进度: {step} bars")

        capsule.stop_backtest()
        print(f"回测完成: 共处理 {step} 条K线")

        capsule.shutdown()


# =============================================================================
# 示例 6: 实时数据流处理
# =============================================================================


def example_realtime_stream():
    """
    展示如何处理实时数据流
    """
    print("\n" + "=" * 60)
    print("示例 6: 实时数据流")
    print("=" * 60)

    from nemt.market_providers import BinanceMarketProvider

    def on_kline(kline):
        """处理每个新的K线"""
        print(f"[{kline.timestamp}] {kline.symbol}: {kline.close:.2f}")

    # 创建 Provider
    provider = BinanceMarketProvider(symbols=["BTCUSDT"])

    if provider.connect():
        # 订阅实时数据
        provider.subscribe("BTCUSDT", on_kline)

        # 启动 WebSocket
        provider.subscribe_websocket(["BTCUSDT"], ["1m"])

        print("实时数据流已启动，按 Ctrl+C 停止")

        # 注意: 这里会阻塞，实际使用需要异步处理
        # import time
        # while True:
        #     time.sleep(1)

        provider.disconnect()


# =============================================================================
# 示例 7: 使用工厂模式创建数据源
# =============================================================================


def example_factory():
    """
    展示如何使用工厂模式创建数据源
    """
    print("\n" + "=" * 60)
    print("示例 7: 工厂模式")
    print("=" * 60)

    from nemt.market_providers import MarketProviderFactory, ProviderType, create_data_source

    # 方式 1: 使用枚举类型
    print("\n--- 使用 ProviderType ---")
    mock = MarketProviderFactory.create(ProviderType.MOCK, symbols=["BTCUSDT"])
    mock.connect()
    print(f"Mock 提供者: {mock.get_status()}")
    mock.disconnect()

    # 方式 2: 使用字符串
    print("\n--- 使用字符串 ---")
    binance = MarketProviderFactory.create("binance", symbols=["BTCUSDT"])
    binance.connect()
    print(f"Binance 提供者: {binance.get_status()}")
    binance.disconnect()

    # 方式 3: 使用便捷函数
    print("\n--- 使用 create_data_source ---")
    csv_source = create_data_source("csv", filepath="matlab_data/BTC.csv", symbol="BTC")
    csv_source.connect()
    history = csv_source.get_history(limit=10)
    print(f"CSV 数据: {len(history)} 条")
    csv_source.disconnect()


# =============================================================================
# 主函数
# =============================================================================


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("NEMT 市场数据提供者使用示例")
    print("=" * 60)

    # 按顺序运行示例 (可以注释掉不需要的)
    try:
        example_mock_data()
    except Exception as e:
        print(f"示例 3 失败: {e}")

    try:
        example_binance_api()
    except Exception as e:
        print(f"示例 1 失败: {e}")

    try:
        example_csv_file()
    except Exception as e:
        print(f"示例 2 失败: {e}")

    try:
        example_market_layer()
    except Exception as e:
        print(f"示例 4 失败: {e}")

    try:
        example_factory()
    except Exception as e:
        print(f"示例 7 失败: {e}")

    # 以下示例需要更长时间运行
    # example_market_capsule()
    # example_realtime_stream()

    print("\n" + "=" * 60)
    print("所有示例运行完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
