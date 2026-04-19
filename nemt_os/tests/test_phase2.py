"""
NEMT Phase 2 验收测试
测试数据层组件
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_market_provider():
    """测试市场数据提供者"""
    print("\n" + "=" * 60)
    print("测试: 市场数据提供者 (Market Provider)")
    print("=" * 60)
    
    from nemt.market_providers import MockMarketProvider
    
    # 创建Mock提供者
    provider = MockMarketProvider(name="TestProvider")
    
    # 测试连接
    assert provider.connect() == True
    print("[OK] Mock Provider 连接成功")
    
    # 测试获取ticker
    ticker = provider.get_ticker('BTCUSDT')
    assert ticker is not None
    assert ticker.symbol == 'BTCUSDT'
    assert ticker.price > 0
    print(f"[OK] BTCUSDT Ticker: ${ticker.price:,.2f}")
    
    # 测试获取历史K线
    klines = provider.get_history('BTCUSDT', limit=10)
    assert len(klines) == 10
    print(f"[OK] 获取 {len(klines)} 条历史K线")
    
    # 测试获取所有ticker
    tickers = provider.get_all_tickers()
    assert len(tickers) == 4  # 默认4个币种
    print(f"[OK] 获取 {len(tickers)} 个交易对行情")
    
    # 测试状态
    status = provider.get_status()
    assert status['connected'] == True
    print(f"[OK] Provider 状态: {status}")
    
    provider.disconnect()
    print("[OK] Mock Provider 断开连接")
    
    return True


def test_storage():
    """测试数据存储"""
    print("\n" + "=" * 60)
    print("测试: 数据存储层 (Storage)")
    print("=" * 60)
    
    from nemt.storage import init_database
    from nemt.market_providers.base import KLine
    from datetime import datetime
    
    # 初始化数据库
    storage = init_database(":memory:")  # 使用内存数据库
    print("[OK] 数据库初始化成功")
    
    # 测试保存K线
    from datetime import timedelta
    base_time = datetime.now()
    klines = []
    for i in range(10):
        kline = KLine(
            timestamp=base_time - timedelta(seconds=10 * (10 - i)),  # 每条间隔10秒
            open=67000 + i,
            high=67100 + i,
            low=66900 + i,
            close=67050 + i,
            volume=12345,
            symbol='BTCUSDT',
            interval='1h'
        )
        klines.append(kline)
    
    count = storage.save_klines(klines)
    print(f"[DEBUG] Saved {count} klines, expected 10")
    print(f"[DEBUG] KLines count: {len(klines)}")
    assert count == 10, f"Expected 10, got {count}"
    print(f"[OK] 保存 {count} 条K线数据")
    
    # 测试获取K线
    stored_klines = storage.get_klines('BTCUSDT', limit=5)
    print(f"[DEBUG] Retrieved {len(stored_klines)} klines, expected 5")
    assert len(stored_klines) == 5, f"Expected 5, got {len(stored_klines)}"
    print(f"[OK] 获取 {len(stored_klines)} 条K线数据")
    
    # 测试保存策略
    success = storage.save_strategy(
        strategy_id='test-strategy-001',
        name='测试策略',
        strategy_type='nemt-dci',
        params={'alpha': 0.5, 'beta': 0.3},
        status='alive'
    )
    assert success == True
    print("[OK] 保存策略配置")
    
    # 测试获取策略
    strategy = storage.get_strategy('test-strategy-001')
    assert strategy is not None
    assert strategy['name'] == '测试策略'
    print(f"[OK] 获取策略: {strategy['name']}")
    
    # 测试列出策略
    strategies = storage.list_strategies()
    assert len(strategies) >= 1
    print(f"[OK] 列出 {len(strategies)} 个策略")
    
    # 测试保存信号
    success = storage.save_signal(
        signal_id='sig-001',
        signal_type='vortex_breakout',
        direction='bullish',
        symbol='BTCUSDT',
        confidence=0.75,
        reason='测试信号',
        price=67000
    )
    assert success == True
    print("[OK] 保存信号")
    
    # 测试获取信号
    signals = storage.get_signals(limit=10)
    assert len(signals) >= 1
    print(f"[OK] 获取 {len(signals)} 个信号")
    
    # 测试系统配置
    storage.set_config('last_sync', {'time': '2026-04-19'})
    last_sync = storage.get_config('last_sync')
    assert last_sync is not None
    print(f"[OK] 系统配置: {last_sync}")
    
    return True


def test_event_bus():
    """测试事件总线"""
    print("\n" + "=" * 60)
    print("测试: 事件总线 (Event Bus)")
    print("=" * 60)
    
    from nemt.event_bus import EventBus, EventType, publish_event
    
    # 创建事件总线
    bus = EventBus()  # 不使用Redis，使用本地模式
    bus.start()
    print("[OK] 事件总线启动")
    
    # 测试发布事件
    received_events = []
    
    def test_callback(event):
        received_events.append(event)
        print(f"[RECV] 事件: {event.event_type.value}")
    
    # 订阅事件
    bus.subscribe(EventType.SIGNAL_GENERATED, test_callback)
    print("[OK] 订阅 SIGNAL_GENERATED 事件")
    
    # 发布事件
    bus.emit(EventType.SIGNAL_GENERATED, 'test', {'signal_id': 'test-001'})
    bus.emit(EventType.SIGNAL_GENERATED, 'test', {'signal_id': 'test-002'})
    
    # 等待事件处理
    import time
    time.sleep(0.2)
    
    assert len(received_events) >= 1
    print(f"[OK] 收到 {len(received_events)} 个事件")
    
    # 测试获取历史
    history = bus.get_history(EventType.SIGNAL_GENERATED, limit=10)
    print(f"[OK] 事件历史: {len(history)} 条")
    
    # 测试状态
    status = bus.get_status()
    print(f"[OK] 事件总线状态: {status}")
    
    bus.stop()
    print("[OK] 事件总线停止")
    
    return True


def test_notion_adapter():
    """测试Notion适配器"""
    print("\n" + "=" * 60)
    print("测试: Notion 适配器 (Notion Adapter)")
    print("=" * 60)
    
    from nemt.adapters.notion import MockNotionAdapter, NotionSyncAdapter
    
    # 创建Mock适配器
    adapter = MockNotionAdapter()
    assert adapter.connect() == True
    print("[OK] Mock Notion 连接成功")
    
    # 测试获取数据库
    db = adapter.get_database('strategy-db')
    assert db is not None
    assert db.title == '策略库'
    print(f"[OK] 获取数据库: {db.title}")
    
    # 测试查询数据库
    results = adapter.query_database('strategy-db')
    print(f"[OK] 查询结果: {len(results)} 条")
    
    # 测试创建页面
    page = adapter.create_page(
        parent_id='strategy-db',
        properties={'Name': '新策略', 'Status': 'testing'},
        content='测试策略内容'
    )
    assert page is not None
    print(f"[OK] 创建页面: {page.title}")
    
    # 测试同步适配器
    sync = NotionSyncAdapter(adapter)
    
    success = sync.sync_strategy_to_notion({
        'name': 'NEMT-DCI 测试策略',
        'status': 'alive',
        'type': 'nemt-dci',
        'sharpe_ratio': 1.5,
        'win_rate': 0.6
    })
    assert success == True
    print("[OK] 策略同步到Notion")
    
    # 测试从Notion获取策略
    strategies = sync.get_strategies_from_notion()
    print(f"[OK] 从Notion获取 {len(strategies)} 个策略")
    
    adapter.disconnect()
    print("[OK] Mock Notion 断开连接")
    
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("NEMT Phase 2 验收测试")
    print("厨房阶段 - 数据层")
    print("=" * 60)
    
    tests = [
        ("市场数据提供者", test_market_provider),
        ("数据存储层", test_storage),
        ("事件总线", test_event_bus),
        ("Notion适配器", test_notion_adapter),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success, None))
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"[FAIL] {name}: {e}")
    
    # 打印结果汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, success, error in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {name}")
        if error:
            print(f"       错误: {error}")
        if not success:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("Phase 2 验收测试: 全部通过")
    else:
        print("Phase 2 验收测试: 有失败项")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
