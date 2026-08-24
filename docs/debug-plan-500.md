# NEMT Simulator 500步调试计划

> 创建日期: 2026-05-03
> 更新日期: 2026-05-03
> 状态: 进行中

## 概述

本计划包含 **500 个调试任务**，覆盖以下模块：

- **Python 后端 (nemt_os)**: 任务 1-200
- **Go 后端 (nemt-go)**: 任务 201-350
- **前端 (React/Electron)**: 任务 351-450
- **集成测试**: 任务 451-500

---

## 第一部分：Python 后端 (任务 1-200)

### 1.1 环境与基础 (任务 1-30)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 1 | config | requirements.txt | pip install | - | 依赖安装成功 | [ ] |
| 2 | config | requirements.txt | 版本验证 | - | numpy>=1.21 pandas>=1.3 | [ ] |
| 3 | config | requirements-dev.txt | pytest | - | pytest>=6.2.0 已安装 | [ ] |
| 4 | config | setup.py/pyproject.toml | 项目配置 | - | 包配置正确 | [ ] |
| 5 | config | .env.example | 环境变量 | - | 示例文件存在 | [ ] |
| 6 | core | nemt/__init__.py | 模块导入 | line 1-20 | 核心模块可导入 | [ ] |
| 7 | core | nemt/__init__.py | __all__ | line 15-30 | 导出列表完整 | [ ] |
| 8 | core | nemt/core/__init__.py | 导入链 | line 1-10 | core 子模块可用 | [ ] |
| 9 | core | nemt/core/__init__.py | 子模块导入 | line 10-20 | capsule/event_bus 等 | [ ] |
| 10 | core | nemt/core/__init__.py | 导出检查 | line 20-30 | 导出无循环依赖 | [ ] |
| 11 | core | config_center.py | ConfigCenter.__init__ | line 30-50 | 配置中心初始化 | [ ] |
| 12 | core | config_center.py | load() | line 80-100 | YAML 配置加载 | [ ] |
| 13 | core | config_center.py | get() | line 110-130 | 配置读取正常 | [ ] |
| 14 | core | config_center.py | set() | line 140-160 | 配置写入正常 | [ ] |
| 15 | core | config_center.py | save() | line 170-190 | 配置保存成功 | [ ] |
| 16 | core | event_bus.py | EventBus.__init__ | line 20-40 | 事件总线创建 | [ ] |
| 17 | core | event_bus.py | subscribe() | line 60-80 | 事件订阅成功 | [ ] |
| 18 | core | event_bus.py | publish() | line 90-110 | 事件发布正常 | [ ] |
| 19 | core | event_bus.py | unsubscribe() | line 120-140 | 取消订阅成功 | [ ] |
| 20 | core | event_bus.py | emit() | line 150-170 | 同步事件触发 | [ ] |
| 21 | core | event_bus.py | once() | line 180-200 | 单次事件监听 | [ ] |
| 22 | core | event_bus.py | clear() | line 210-220 | 清除所有监听 | [ ] |
| 23 | core | capsule_manager.py | CapsuleManager.__init__ | line 30-50 | 胶囊管理器初始化 | [ ] |
| 24 | core | capsule_manager.py | register() | line 60-80 | 胶囊注册成功 | [ ] |
| 25 | core | capsule_manager.py | start_all() | line 90-110 | 所有胶囊启动 | [ ] |
| 26 | core | capsule_manager.py | stop_all() | line 120-140 | 所有胶囊停止 | [ ] |
| 27 | core | capsule_manager.py | get_capsule() | line 150-160 | 胶囊获取正常 | [ ] |
| 28 | core | capsule_manager.py | list_capsules() | line 170-180 | 胶囊列表返回 | [ ] |
| 29 | core | capsule_manager.py | 依赖注入 | line 80-100 | DI 容器工作 | [ ] |
| 30 | core | capsule_manager.py | 生命周期 | line 100-120 | setup/execute/cleanup | [ ] |

### 1.2 MarketCapsule (任务 31-45)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 31 | market | market_capsule.py | MarketCapsule.__init__ | line 30-50 | 市场胶囊初始化 | [ ] |
| 32 | market | market_capsule.py | setup() | line 60-70 | 胶囊 setup | [ ] |
| 33 | market | market_capsule.py | load_data() | line 80-100 | K线数据加载 | [ ] |
| 34 | market | market_capsule.py | get_bar() | line 110-130 | 获取当前K线 | [ ] |
| 35 | market | market_capsule.py | next_bar() | line 140-160 | K线迭代 | [ ] |
| 36 | market | market_capsule.py | has_next() | line 170-180 | 迭代状态检查 | [ ] |
| 37 | market | market_capsule.py | reset() | line 190-200 | 迭代器重置 | [ ] |
| 38 | market | market_capsule.py | start_backtest() | line 210-230 | 回测启动 | [ ] |
| 39 | market | market_capsule.py | stop_backtest() | line 240-250 | 回测停止 | [ ] |
| 40 | market | market_capsule.py | get_symbol() | line 260-270 | 获取交易品种 | [ ] |
| 41 | market | market_capsule.py | get_current_price() | line 280-300 | 当前价格获取 | [ ] |
| 42 | market | market_capsule.py | get_ohlcv() | line 310-330 | OHLCV 数据 | [ ] |
| 43 | market | market_capsule.py | calculate_returns() | line 340-360 | 收益率计算 | [ ] |
| 44 | market | market_capsule.py | execute() | line 370-390 | 执行方法 | [ ] |
| 45 | market | market_capsule.py | cleanup() | line 400-410 | 资源清理 | [ ] |

### 1.3 SignalCapsule (任务 46-60)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 46 | signal | signal_capsule.py | SignalCapsule.__init__ | line 30-50 | 信号胶囊初始化 | [ ] |
| 47 | signal | signal_capsule.py | setup() | line 60-70 | 胶囊 setup | [ ] |
| 48 | signal | signal_capsule.py | generate_signal() | line 80-120 | 信号生成逻辑 | [ ] |
| 49 | signal | signal_capsule.py | calculate_confidence() | line 130-150 | 置信度计算 | [ ] |
| 50 | signal | signal_capsule.py | validate_signal() | line 160-180 | 信号验证 | [ ] |
| 51 | signal | signal_capsule.py | on_bar() | line 190-210 | K线事件处理 | [ ] |
| 52 | signal | signal_capsule.py | get_signal_strength() | line 220-240 | 信号强度 | [ ] |
| 53 | signal | signal_capsule.py | filter_signals() | line 250-270 | 信号过滤 | [ ] |
| 54 | signal | signal_capsule.py | get_latest_signal() | line 280-300 | 最新信号获取 | [ ] |
| 55 | signal | signal_capsule.py | execute() | line 310-330 | 执行方法 | [ ] |
| 56 | signal | signal_capsule.py | cleanup() | line 340-350 | 资源清理 | [ ] |
| 57 | signal | signal_layer.py | SignalLayer.__init__ | line 20-40 | 信号层初始化 | [ ] |
| 58 | signal | signal_layer.py | process() | line 50-70 | 信号处理 | [ ] |
| 59 | signal | signal_layer.py | aggregate() | line 80-100 | 信号聚合 | [ ] |
| 60 | signal | signal_layer.py | validate() | line 110-130 | 信号验证 | [ ] |

### 1.4 RiskCapsule (任务 61-75)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 61 | risk | risk_capsule.py | RiskCapsule.__init__ | line 30-50 | 风控胶囊初始化 | [ ] |
| 62 | risk | risk_capsule.py | setup() | line 60-70 | 胶囊 setup | [ ] |
| 63 | risk | risk_capsule.py | check_risk() | line 80-120 | 风控检查逻辑 | [ ] |
| 64 | risk | risk_capsule.py | check_stop_loss() | line 130-150 | 止损检查 | [ ] |
| 65 | risk | risk_capsule.py | check_take_profit() | line 160-180 | 止盈检查 | [ ] |
| 66 | risk | risk_capsule.py | calculate_position_size() | line 190-220 | 仓位计算 | [ ] |
| 67 | risk | risk_capsule.py | get_risk_level() | line 230-250 | 风险等级 | [ ] |
| 68 | risk | risk_capsule.py | is_defensive() | line 260-280 | 防御模式 | [ ] |
| 69 | risk | risk_capsule.py | on_event() | line 290-310 | 事件处理 | [ ] |
| 70 | risk | risk_capsule.py | execute() | line 320-340 | 执行方法 | [ ] |
| 71 | risk | risk_capsule.py | cleanup() | line 350-360 | 资源清理 | [ ] |
| 72 | risk | trading/risk.py | RiskManager | line 20-50 | 风控管理器 | [ ] |
| 73 | risk | trading/risk.py | validate_order() | line 60-80 | 订单验证 | [ ] |
| 74 | risk | trading/risk.py | check_limits() | line 90-110 | 限额检查 | [ ] |
| 75 | risk | trading/risk.py | emergency_exit() | line 120-140 | 紧急退出 | [ ] |

### 1.5 ExecutionCapsule (任务 76-90)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 76 | execution | execution_capsule.py | ExecutionCapsule.__init__ | line 30-50 | 执行胶囊初始化 | [ ] |
| 77 | execution | execution_capsule.py | setup() | line 60-70 | 胶囊 setup | [ ] |
| 78 | execution | execution_capsule.py | place_order() | line 80-120 | 下单逻辑 | [ ] |
| 79 | execution | execution_capsule.py | cancel_order() | line 130-150 | 撤单逻辑 | [ ] |
| 80 | execution | execution_capsule.py | modify_order() | line 160-180 | 改单逻辑 | [ ] |
| 81 | execution | execution_capsule.py | get_order_status() | line 190-210 | 订单状态 | [ ] |
| 82 | execution | execution_capsule.py | on_fill() | line 220-240 | 成交回报处理 | [ ] |
| 83 | execution | execution_capsule.py | calculate_commission() | line 250-270 | 佣金计算 | [ ] |
| 84 | execution | execution_capsule.py | get_statistics() | line 280-300 | 执行统计 | [ ] |
| 85 | execution | execution_capsule.py | execute() | line 310-330 | 执行方法 | [ ] |
| 86 | execution | execution_capsule.py | cleanup() | line 340-350 | 资源清理 | [ ] |
| 87 | execution | execution.py | OrderManager | line 20-50 | 订单管理器 | [ ] |
| 88 | execution | execution.py | submit() | line 60-80 | 订单提交 | [ ] |
| 89 | execution | execution.py | process_response() | line 90-110 | 响应处理 | [ ] |
| 90 | execution | execution.py | sync_orders() | line 120-140 | 订单同步 | [ ] |

### 1.6 DashboardCapsule (任务 91-100)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 91 | dashboard | dashboard_capsule.py | DashboardCapsule.__init__ | line 30-50 | 仪表板初始化 | [ ] |
| 92 | dashboard | dashboard_capsule.py | setup() | line 60-70 | 胶囊 setup | [ ] |
| 93 | dashboard | dashboard_capsule.py | update() | line 80-100 | 状态更新 | [ ] |
| 94 | dashboard | dashboard_capsule.py | on_trade() | line 110-130 | 交易事件 | [ ] |
| 95 | dashboard | dashboard_capsule.py | calculate_equity() | line 140-160 | 权益计算 | [ ] |
| 96 | dashboard | dashboard_capsule.py | calculate_drawdown() | line 170-190 | 回撤计算 | [ ] |
| 97 | dashboard | dashboard_capsule.py | get_win_rate() | line 200-220 | 胜率计算 | [ ] |
| 98 | dashboard | dashboard_capsule.py | execute() | line 230-250 | 执行方法 | [ ] |
| 99 | dashboard | dashboard_capsule.py | cleanup() | line 260-270 | 资源清理 | [ ] |
| 100 | dashboard | ops/dashboard.py | DashboardService | line 20-40 | Dashboard 服务 | [ ] |

### 1.7 核心引擎 (任务 101-140)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 101 | engine | nemt_engine.py | NEMTEngine.__init__ | line 43-60 | 引擎初始化 | [ ] |
| 102 | engine | nemt_engine.py | setup() | line 68-77 | 引擎 setup | [ ] |
| 103 | engine | nemt_engine.py | _register_all_capsules() | line 79-115 | 胶囊注册 | [ ] |
| 104 | engine | nemt_engine.py | register_capsule() | line 117-129 | 单个胶囊注册 | [ ] |
| 105 | engine | nemt_engine.py | get_capsule() | line 131-141 | 胶囊获取 | [ ] |
| 106 | engine | nemt_engine.py | load_data() | line 143-157 | 数据加载 | [ ] |
| 107 | engine | nemt_engine.py | run() | line 159-201 | 主回测循环 | [ ] |
| 108 | engine | nemt_engine.py | pause() | line 203-205 | 回测暂停 | [ ] |
| 109 | engine | nemt_engine.py | resume() | line 207-209 | 回测继续 | [ ] |
| 110 | engine | nemt_engine.py | stop() | line 211-213 | 回测停止 | [ ] |
| 111 | engine | nemt_engine.py | _shutdown() | line 215-225 | 引擎关闭 | [ ] |
| 112 | engine | nemt_engine.py | _collect_results() | line 227-241 | 结果收集 | [ ] |
| 113 | engine | nemt_engine.py | generate_report() | line 243-286 | 报告生成 | [ ] |
| 114 | engine | nemt_engine.py | create_engine() | line 298-308 | 工厂函数 | [ ] |
| 115 | engine | backtest.py | BacktestEngine | line 20-50 | 回测引擎类 | [ ] |
| 116 | engine | backtest.py | initialize() | line 60-80 | 初始化 | [ ] |
| 117 | engine | backtest.py | feed_data() | line 90-110 | 数据喂入 | [ ] |
| 118 | engine | backtest.py | process_bar() | line 120-140 | K线处理 | [ ] |
| 119 | engine | backtest.py | calculate_results() | line 150-170 | 结果计算 | [ ] |
| 120 | engine | backtest.py | generate_metrics() | line 180-200 | 指标生成 | [ ] |
| 121 | engine | position_capsule.py | PositionCapsule.__init__ | line 30-50 | 仓位胶囊 | [ ] |
| 122 | engine | position_capsule.py | calculate_position() | line 60-80 | 仓位计算 | [ ] |
| 123 | engine | position_capsule.py | update_position() | line 90-110 | 仓位更新 | [ ] |
| 124 | engine | position_capsule.py | get_position_value() | line 120-140 | 仓位价值 | [ ] |
| 125 | engine | position_capsule.py | close_position() | line 150-170 | 平仓逻辑 | [ ] |
| 126 | engine | position_calculator.py | calculate() | line 30-50 | 核心计算 | [ ] |
| 127 | engine | position_calculator.py | validate() | line 60-80 | 仓位验证 | [ ] |
| 128 | engine | brain_capsule.py | BrainCapsule.__init__ | line 30-50 | 大脑胶囊 | [ ] |
| 129 | engine | brain_capsule.py | make_decision() | line 60-90 | 决策逻辑 | [ ] |
| 130 | engine | brain_capsule.py | analyze_context() | line 100-130 | 上下文分析 | [ ] |
| 131 | engine | brain_capsule.py | execute() | line 140-160 | 执行方法 | [ ] |
| 132 | engine | monitor_capsule.py | MonitorCapsule.__init__ | line 30-50 | 监控胶囊 | [ ] |
| 133 | engine | monitor_capsule.py | monitor() | line 60-80 | 监控逻辑 | [ ] |
| 134 | engine | monitor_capsule.py | alert() | line 90-110 | 告警逻辑 | [ ] |
| 135 | engine | phase_capsule.py | PhaseStateMachineCapsule | line 30-50 | 阶段状态机 | [ ] |
| 136 | engine | phase_capsule.py | transition() | line 60-80 | 状态转换 | [ ] |
| 137 | engine | brain.py | Brain | line 20-50 | Brain 类 | [ ] |
| 138 | engine | brain.py | think() | line 60-80 | 思考逻辑 | [ ] |
| 139 | engine | strategy.py | Strategy | line 20-50 | 策略基类 | [ ] |
| 140 | engine | strategy.py | on_tick() | line 60-80 | Tick 处理 | [ ] |

### 1.8 测试文件 (任务 141-200)

| # | 模块 | 文件 | 函数/测试 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 141 | test | test_nemt.py | test_import | line 1-20 | 导入测试 | [ ] |
| 142 | test | test_nemt.py | test_config | line 30-50 | 配置测试 | [ ] |
| 143 | test | test_nemt.py | test_event_bus | line 60-80 | 事件总线测试 | [ ] |
| 144 | test | test_nemt.py | test_capsule | line 90-110 | 胶囊测试 | [ ] |
| 145 | test | test_nemt.py | test_engine | line 120-140 | 引擎测试 | [ ] |
| 146 | test | test_integration.py | test_full_flow | line 20-50 | 完整流程测试 | [ ] |
| 147 | test | test_integration.py | test_data_loading | line 60-80 | 数据加载测试 | [ ] |
| 148 | test | test_integration.py | test_signal_generation | line 90-110 | 信号生成测试 | [ ] |
| 149 | test | test_integration.py | test_execution | line 120-140 | 执行测试 | [ ] |
| 150 | test | test_integration.py | test_results | line 150-170 | 结果测试 | [ ] |
| 151 | test | test_acceptance.py | test_acceptance_criteria | line 20-50 | 验收标准 | [ ] |
| 152 | test | test_acceptance.py | test_performance | line 60-80 | 性能测试 | [ ] |
| 153 | test | test_acceptance.py | test_stability | line 90-110 | 稳定性测试 | [ ] |
| 154 | test | test_phase2.py | test_phase2_features | line 20-50 | Phase2 特性 | [ ] |
| 155 | test | test_phase2.py | test_integration_points | line 60-80 | 集成点 | [ ] |
| 156 | test | test_phase2.py | test_error_handling | line 90-110 | 错误处理 | [ ] |
| 157 | test | test_phase3.py | test_phase3_features | line 20-50 | Phase3 特性 | [ ] |
| 158 | test | test_phase3.py | test_advanced_signals | line 60-80 | 高级信号 | [ ] |
| 159 | test | test_phase3.py | test_risk_management | line 90-110 | 风险管理 | [ ] |
| 160 | test | test_phase4.py | test_phase4_features | line 20-50 | Phase4 特性 | [ ] |
| 161 | test | test_phase4.py | test_production_ready | line 60-80 | 生产就绪 | [ ] |
| 162 | test | test_phase4.py | test_monitoring | line 90-110 | 监控测试 | [ ] |
| 163 | test | test_services.py | ServiceTests | line 20-50 | 服务测试 | [ ] |
| 164 | test | test_services.py | MarketServiceTest | line 60-80 | 市场服务测试 | [ ] |
| 165 | test | test_services.py | SignalServiceTest | line 90-110 | 信号服务测试 | [ ] |
| 166 | test | test_examples.py | ExampleTests | line 20-50 | 示例测试 | [ ] |
| 167 | test | test_examples.py | test_demo | line 60-80 | 演示测试 | [ ] |
| 168 | test | conftest.py | pytest fixtures | line 20-50 | Pytest 配置 | [ ] |
| 169 | test | test_fractal_integration.py | FractalTests | line 20-50 | 分形测试 | [ ] |
| 170 | test | test_security_quick.py | SecurityQuickTests | line 20-50 | 快速安全测试 | [ ] |
| 171 | test | test_security_full_80steps.py | SecurityFullTests | line 20-50 | 完整安全测试 | [ ] |
| 172 | core | capsule.py | ModuleCapsule | line 30-100 | 基础胶囊类 | [ ] |
| 173 | core | capsule.py | setup/execute/cleanup | line 100-150 | 生命周期方法 | [ ] |
| 174 | core | capsule_manager.py | CapsuleManager | line 30-150 | 胶囊管理 | [ ] |
| 175 | core | event_bus_factory.py | EventBusFactory | line 20-50 | 工厂模式 | [ ] |
| 176 | core | node_schema.py | NodeSchema | line 20-50 | 节点模式 | [ ] |
| 177 | core | node.py | Node | line 20-50 | Node 类 | [ ] |
| 178 | core | registry.py | Registry | line 20-50 | 注册表 | [ ] |
| 179 | core | data_layer.py | DataLayer | line 20-50 | 数据层 | [ ] |
| 180 | core | platform.py | Platform | line 20-50 | 平台层 | [ ] |
| 181 | evolution | evolution_capsule.py | EvolutionCapsule | line 30-80 | 进化胶囊 | [ ] |
| 182 | evolution | evolution.py | Evolution | line 20-50 | Evolution 类 | [ ] |
| 183 | evolution | guider/guider.py | Guider | line 20-50 | 指导器 | [ ] |
| 184 | evolution | self_repair/self_repair.py | SelfRepair | line 20-50 | 自我修复 | [ ] |
| 185 | evolution | test_evolution.py | EvolutionTests | line 20-50 | 进化测试 | [ ] |
| 186 | evolution | test_business_constraints.py | ConstraintsTests | line 20-50 | 约束测试 | [ ] |
| 187 | storage | sqlite_storage.py | SQLiteStorage | line 30-80 | SQLite 存储 | [ ] |
| 188 | storage | sqlite_storage.py | save/load | line 80-120 | 保存/加载 | [ ] |
| 189 | storage | storage_factory.py | StorageFactory | line 20-50 | 存储工厂 | [ ] |
| 190 | storage | interfaces/storage.py | StorageInterface | line 20-50 | 存储接口 | [ ] |
| 191 | adapters | notion_adapter.py | NotionAdapter | line 30-80 | Notion 适配器 | [ ] |
| 192 | adapters | storage_adapter.py | StorageAdapter | line 30-80 | 存储适配器 | [ ] |
| 193 | adapters | config_center_adapter.py | ConfigCenterAdapter | line 30-80 | 配置适配器 | [ ] |
| 194 | resilience | rate_limiter.py | RateLimiter | line 20-50 | 限流器 | [ ] |
| 195 | resilience | circuit_breaker.py | CircuitBreaker | line 20-50 | 熔断器 | [ ] |
| 196 | resilience | timeout_handler.py | TimeoutHandler | line 20-50 | 超时处理 | [ ] |
| 197 | security | audit.py | Audit | line 20-50 | 审计日志 | [ ] |
| 198 | security | permission.py | Permission | line 20-50 | 权限管理 | [ ] |
| 199 | ops | workflow.py | Workflow | line 20-50 | 工作流 | [ ] |
| 200 | ops | profiler.py | Profiler | line 20-50 | 性能分析 | [ ] |

---

## 第二部分：Go 后端 (任务 201-350)

### 2.1 Gateway 服务 (任务 201-250)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 201 | gateway | cmd/gateway/main.go | main() | line 1-50 | 服务启动 | [ ] |
| 202 | gateway | cmd/gateway/main.go | initServer() | line 50-100 | 服务初始化 | [ ] |
| 203 | gateway | cmd/gateway/main.go | loadConfig() | line 100-150 | 配置加载 | [ ] |
| 204 | gateway | cmd/gateway/main.go | setupGRPC() | line 150-200 | gRPC 设置 | [ ] |
| 205 | gateway | cmd/gateway/main.go | startServer() | line 200-250 | 服务启动 | [ ] |
| 206 | gateway | cmd/gateway/main.go | shutdown() | line 250-300 | 优雅关闭 | [ ] |
| 207 | gateway | pkg/gateway/handler.go | NewHandler() | line 20-50 | 处理器创建 | [ ] |
| 208 | gateway | pkg/gateway/handler.go | HandleRequest() | line 50-100 | 请求处理 | [ ] |
| 209 | gateway | pkg/gateway/handler.go | RouteRequest() | line 100-150 | 路由分发 | [ ] |
| 210 | gateway | pkg/gateway/handler.go | HandleError() | line 150-200 | 错误处理 | [ ] |
| 211 | gateway | pkg/gateway/strategy.go | HandleStrategy() | line 20-50 | 策略处理 | [ ] |
| 212 | gateway | pkg/gateway/strategy.go | CreateStrategy() | line 50-100 | 策略创建 | [ ] |
| 213 | gateway | pkg/gateway/strategy.go | UpdateStrategy() | line 100-150 | 策略更新 | [ ] |
| 214 | gateway | pkg/gateway/strategy.go | DeleteStrategy() | line 150-200 | 策略删除 | [ ] |
| 215 | gateway | pkg/gateway/strategy.go | GetStrategy() | line 200-250 | 策略获取 | [ ] |
| 216 | gateway | pkg/gateway/strategy.go | ListStrategies() | line 250-300 | 策略列表 | [ ] |
| 217 | gateway | pkg/gateway/marketdata.go | HandleMarketData() | line 20-50 | 市场数据处理 | [ ] |
| 218 | gateway | pkg/gateway/marketdata.go | Subscribe() | line 50-100 | 订阅数据 | [ ] |
| 219 | gateway | pkg/gateway/marketdata.go | Unsubscribe() | line 100-150 | 取消订阅 | [ ] |
| 220 | gateway | pkg/gateway/marketdata.go | GetQuote() | line 150-200 | 获取报价 | [ ] |
| 221 | gateway | pkg/gateway/marketdata.go | GetKline() | line 200-250 | 获取K线 | [ ] |
| 222 | gateway | pkg/gateway/backtest.go | HandleBacktest() | line 20-50 | 回测处理 | [ ] |
| 223 | gateway | pkg/gateway/backtest.go | StartBacktest() | line 50-100 | 启动回测 | [ ] |
| 224 | gateway | pkg/gateway/backtest.go | StopBacktest() | line 100-150 | 停止回测 | [ ] |
| 225 | gateway | pkg/gateway/backtest.go | GetBacktestResult() | line 150-200 | 获取结果 | [ ] |
| 226 | gateway | pkg/gateway/websocket.go | HandleWebSocket() | line 20-50 | WebSocket处理 | [ ] |
| 227 | gateway | pkg/gateway/websocket.go | Connect() | line 50-100 | 建立连接 | [ ] |
| 228 | gateway | pkg/gateway/websocket.go | Disconnect() | line 100-150 | 断开连接 | [ ] |
| 229 | gateway | pkg/gateway/websocket.go | SendMessage() | line 150-200 | 发送消息 | [ ] |
| 230 | gateway | pkg/gateway/websocket.go | ReceiveMessage() | line 200-250 | 接收消息 | [ ] |
| 231 | gateway | pkg/gateway/capsule.go | HandleCapsule() | line 20-50 | 胶囊处理 | [ ] |
| 232 | gateway | pkg/gateway/capsule.go | DeployCapsule() | line 50-100 | 部署胶囊 | [ ] |
| 233 | gateway | pkg/gateway/capsule.go | RemoveCapsule() | line 100-150 | 移除胶囊 | [ ] |
| 234 | gateway | pkg/gateway/marketplace.go | HandleMarketplace() | line 20-50 | 市场处理 | [ ] |
| 235 | gateway | pkg/gateway/marketplace.go | ListProducts() | line 50-100 | 产品列表 | [ ] |
| 236 | gateway | pkg/gateway/marketplace.go | GetProduct() | line 100-150 | 获取产品 | [ ] |
| 237 | gateway | pkg/grpcserver/server.go | NewServer() | line 20-50 | 服务创建 | [ ] |
| 238 | gateway | pkg/grpcserver/server.go | Serve() | line 50-100 | 服务运行 | [ ] |
| 239 | gateway | pkg/grpcserver/server.go | RegisterServices() | line 100-150 | 注册服务 | [ ] |
| 240 | gateway | pkg/grpcserver/server.go | Stop() | line 150-200 | 停止服务 | [ ] |
| 241 | gateway | pkg/middleware/middleware.go | LoggingMiddleware() | line 20-50 | 日志中间件 | [ ] |
| 242 | gateway | pkg/middleware/middleware.go | AuthMiddleware() | line 50-100 | 认证中间件 | [ ] |
| 243 | gateway | pkg/middleware/middleware.go | RecoveryMiddleware() | line 100-150 | 恢复中间件 | [ ] |
| 244 | gateway | pkg/middleware/middleware.go | CORSMiddleware() | line 150-200 | CORS 中间件 | [ ] |
| 245 | gateway | pkg/middleware/middleware.go | RateLimitMiddleware() | line 200-250 | 限流中间件 | [ ] |
| 246 | gateway | pkg/models/models.go | Strategy | line 20-50 | 策略模型 | [ ] |
| 247 | gateway | pkg/models/models.go | Order | line 50-100 | 订单模型 | [ ] |
| 248 | gateway | pkg/models/models.go | Position | line 100-150 | 仓位模型 | [ ] |
| 249 | gateway | pkg/models/models.go | MarketData | line 150-200 | 市场数据模型 | [ ] |
| 250 | gateway | pkg/models/models.go | BacktestResult | line 200-250 | 回测结果模型 | [ ] |

### 2.2 Collector 服务 (任务 251-280)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 251 | collector | cmd/collector/main.go | main() | line 1-50 | 采集器启动 | [ ] |
| 252 | collector | cmd/collector/main.go | init() | line 50-100 | 初始化 | [ ] |
| 253 | collector | cmd/collector/main.go | run() | line 100-150 | 运行采集 | [ ] |
| 254 | collector | pkg/collector/collector.go | Collector | line 20-50 | 采集器结构 | [ ] |
| 255 | collector | pkg/collector/collector.go | Start() | line 50-100 | 开始采集 | [ ] |
| 256 | collector | pkg/collector/collector.go | Stop() | line 100-150 | 停止采集 | [ ] |
| 257 | collector | pkg/collector/collector.go | FetchData() | line 150-200 | 获取数据 | [ ] |
| 258 | collector | pkg/collector/collector.go | ProcessData() | line 200-250 | 处理数据 | [ ] |
| 259 | collector | pkg/collector/collector.go | SaveData() | line 250-300 | 保存数据 | [ ] |
| 260 | collector | pkg/collector/collector.go | Schedule() | line 300-350 | 调度任务 | [ ] |
| 261 | collector | pkg/market/marketplace.go | Marketplace | line 20-50 | 市场结构 | [ ] |
| 262 | collector | pkg/market/marketplace.go | Store() | line 50-100 | 存储数据 | [ ] |
| 263 | collector | pkg/market/marketplace.go | Query() | line 100-150 | 查询数据 | [ ] |
| 264 | collector | pkg/market/marketplace.go | GetLatest() | line 150-200 | 获取最新 | [ ] |
| 265 | collector | pkg/market/marketplace.go | GetRange() | line 200-250 | 范围查询 | [ ] |
| 266 | collector | pkg/cache/cache.go | Cache | line 20-50 | 缓存结构 | [ ] |
| 267 | collector | pkg/cache/cache.go | Get() | line 50-100 | 获取缓存 | [ ] |
| 268 | collector | pkg/cache/cache.go | Set() | line 100-150 | 设置缓存 | [ ] |
| 269 | collector | pkg/cache/cache.go | Delete() | line 150-200 | 删除缓存 | [ ] |
| 270 | collector | pkg/cache/cache.go | Clear() | line 200-250 | 清空缓存 | [ ] |

### 2.3 Decision 引擎 (任务 271-310)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 271 | decision | pkg/decision/engine.go | DecisionEngine | line 20-50 | 决策引擎 | [ ] |
| 272 | decision | pkg/decision/engine.go | ProcessSignals() | line 50-100 | 处理信号 | [ ] |
| 273 | decision | pkg/decision/engine.go | EvaluateRisk() | line 100-150 | 评估风险 | [ ] |
| 274 | decision | pkg/decision/engine.go | MakeDecision() | line 150-200 | 做出决策 | [ ] |
| 275 | decision | pkg/decision/engine.go | ExecuteDecision() | line 200-250 | 执行决策 | [ ] |
| 276 | strategy | pkg/strategy/engine.go | StrategyEngine | line 20-50 | 策略引擎 | [ ] |
| 277 | strategy | pkg/strategy/engine.go | GenerateOrders() | line 50-100 | 生成订单 | [ ] |
| 278 | strategy | pkg/strategy/engine.go | ApplyConstraints() | line 100-150 | 应用约束 | [ ] |
| 279 | strategy | pkg/strategy/engine.go | ValidateOrders() | line 150-200 | 验证订单 | [ ] |
| 280 | strategy | pkg/strategy/engine.go | OptimizeParameters() | line 200-250 | 参数优化 | [ ] |
| 281 | evolution | pkg/evolution/engine.go | EvolutionEngine | line 20-50 | 进化引擎 | [ ] |
| 282 | evolution | pkg/evolution/engine.go | Evolve() | line 50-100 | 进化逻辑 | [ ] |
| 283 | evolution | pkg/evolution/engine.go | Mutate() | line 100-150 | 突变 | [ ] |
| 284 | evolution | pkg/evolution/engine.go | Crossover() | line 150-200 | 交叉 | [ ] |
| 285 | evolution | pkg/evolution/engine.go | Select() | line 200-250 | 选择 | [ ] |
| 286 | evolution | pkg/evolution/engine.go | Fitness() | line 250-300 | 适应度 | [ ] |
| 287 | selfrepair | pkg/selfrepair/engine.go | SelfRepairEngine | line 20-50 | 自修复引擎 | [ ] |
| 288 | selfrepair | pkg/selfrepair/engine.go | Detect() | line 50-100 | 检测问题 | [ ] |
| 289 | selfrepair | pkg/selfrepair/engine.go | Diagnose() | line 100-150 | 诊断问题 | [ ] |
| 290 | selfrepair | pkg/selfrepair/engine.go | Repair() | line 150-200 | 修复问题 | [ ] |
| 291 | selfrepair | pkg/selfrepair/engine.go | Verify() | line 200-250 | 验证修复 | [ ] |
| 292 | simulator | pkg/simulator/simulator.go | Simulator | line 20-50 | 模拟器 | [ ] |
| 293 | simulator | pkg/simulator/simulator.go | Simulate() | line 50-100 | 模拟逻辑 | [ ] |
| 294 | simulator | pkg/simulator/simulator.go | NextStep() | line 100-150 | 下一步 | [ ] |
| 295 | simulator | pkg/simulator/simulator.go | GetState() | line 150-200 | 获取状态 | [ ] |
| 296 | simulator | pkg/simulator/simulator.go | Reset() | line 200-250 | 重置 | [ ] |

### 2.4 基础设施 (任务 297-350)

| # | 模块 | 文件 | 函数/方法 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 297 | config | pkg/config/config.go | Config | line 20-50 | 配置结构 | [ ] |
| 298 | config | pkg/config/config.go | Load() | line 50-100 | 加载配置 | [ ] |
| 299 | config | pkg/config/config.go | Save() | line 100-150 | 保存配置 | [ ] |
| 300 | config | pkg/config/config.go | Get() | line 150-200 | 获取值 | [ ] |
| 301 | config | pkg/config/config.go | Set() | line 200-250 | 设置值 | [ ] |
| 302 | config | pkg/config/config.go | Validate() | line 250-300 | 验证配置 | [ ] |
| 303 | grpcserver | pkg/grpcserver/server.go | GRPCServer | line 20-50 | gRPC 服务器 | [ ] |
| 304 | grpcserver | pkg/grpcserver/server.go | Register() | line 50-100 | 注册服务 | [ ] |
| 305 | grpcserver | pkg/grpcserver/server.go | Start() | line 100-150 | 启动服务 | [ ] |
| 306 | grpcserver | pkg/grpcserver/server.go | Stop() | line 150-200 | 停止服务 | [ ] |
| 307 | grpcclient | pkg/grpcclient/client.go | GRPCClient | line 20-50 | gRPC 客户端 | [ ] |
| 308 | grpcclient | pkg/grpcclient/client.go | Connect() | line 50-100 | 连接服务 | [ ] |
| 309 | grpcclient | pkg/grpcclient/client.go | Call() | line 100-150 | 调用方法 | [ ] |
| 310 | grpcclient | pkg/grpcclient/client.go | Close() | line 150-200 | 关闭连接 | [ ] |
| 311 | logger | pkg/logger/logger.go | Logger | line 20-50 | 日志器 | [ ] |
| 312 | logger | pkg/logger/logger.go | Info() | line 50-100 | Info 日志 | [ ] |
| 313 | logger | pkg/logger/logger.go | Error() | line 100-150 | Error 日志 | [ ] |
| 314 | logger | pkg/logger/logger.go | Debug() | line 150-200 | Debug 日志 | [ ] |
| 315 | logger | pkg/logger/logger.go | Warn() | line 200-250 | Warn 日志 | [ ] |
| 316 | monitoring | pkg/monitoring/metrics.go | Metrics | line 20-50 | 指标结构 | [ ] |
| 317 | monitoring | pkg/monitoring/metrics.go | IncCounter() | line 50-100 | 增加计数器 | [ ] |
| 318 | monitoring | pkg/monitoring/metrics.go | RecordGauge() | line 100-150 | 记录仪表 | [ ] |
| 319 | monitoring | pkg/monitoring/metrics.go | ObserveHistogram() | line 150-200 | 记录直方图 | [ ] |
| 320 | monitoring | pkg/monitoring/metrics.go | GetMetrics() | line 200-250 | 获取指标 | [ ] |
| 321 | ipc | pkg/ipc/ipc.go | IPC | line 20-50 | IPC 结构 | [ ] |
| 322 | ipc | pkg/ipc/ipc.go | Send() | line 50-100 | 发送消息 | [ ] |
| 323 | ipc | pkg/ipc/ipc.go | Receive() | line 100-150 | 接收消息 | [ ] |
| 324 | ipc | pkg/ipc/ipc.go | RegisterHandler() | line 150-200 | 注册处理器 | [ ] |
| 325 | plugin | pkg/plugin/plugin.go | Plugin | line 20-50 | 插件结构 | [ ] |
| 326 | plugin | pkg/plugin/plugin.go | Load() | line 50-100 | 加载插件 | [ ] |
| 327 | plugin | pkg/plugin/plugin.go | Unload() | line 100-150 | 卸载插件 | [ ] |
| 328 | plugin | pkg/plugin/plugin.go | Execute() | line 150-200 | 执行插件 | [ ] |
| 329 | notification | pkg/notification/service.go | NotificationService | line 20-50 | 通知服务 | [ ] |
| 330 | notification | pkg/notification/service.go | Send() | line 50-100 | 发送通知 | [ ] |
| 331 | notification | pkg/notification/service.go | Subscribe() | line 100-150 | 订阅通知 | [ ] |
| 332 | bootstrap | pkg/bootstrap/system.go | Bootstrap | line 20-50 | 引导程序 | [ ] |
| 333 | bootstrap | pkg/bootstrap/system.go | Init() | line 50-100 | 初始化 | [ ] |
| 334 | bootstrap | pkg/bootstrap/system.go | Start() | line 100-150 | 启动系统 | [ ] |
| 335 | bootstrap | pkg/bootstrap/system.go | Stop() | line 150-200 | 停止系统 | [ ] |
| 336 | common | pkg/common/common.go | CommonTypes | line 20-50 | 公共类型 | [ ] |
| 337 | common | pkg/common/common.go | UtilityFunctions | line 50-100 | 工具函数 | [ ] |
| 338 | guider | pkg/guider/interface.go | GuiderInterface | line 20-50 | 指导器接口 | [ ] |
| 339 | scheduler | cmd/scheduler/main.go | main() | line 1-50 | 调度器启动 | [ ] |
| 340 | scheduler | cmd/scheduler/main.go | Schedule() | line 50-100 | 调度逻辑 | [ ] |
| 341 | scheduler | cmd/scheduler/main.go | RunTasks() | line 100-150 | 运行任务 | [ ] |
| 342 | orthstar | cmd/orthstar/main.go | main() | line 1-50 | Orthstar 启动 | [ ] |
| 343 | orthstar | cmd/orthstar/main.go | Navigate() | line 50-100 | 导航逻辑 | [ ] |
| 344 | orthstar | pkg/orthstar/navigator.go | Navigator | line 20-50 | 导航器 | [ ] |
| 345 | orthstar | pkg/orthstar/navigator.go | PlanRoute() | line 50-100 | 规划路线 | [ ] |
| 346 | orthstar | pkg/orthstar/navigator.go | ExecuteRoute() | line 100-150 | 执行路线 | [ ] |
| 347 | orthstar | pkg/orthstar/navigator.go | AdjustRoute() | line 150-200 | 调整路线 | [ ] |
| 348 | orthstar | pkg/orthstar/navigator.go | GetStatus() | line 200-250 | 获取状态 | [ ] |
| 349 | orthstar | pkg/orthstar/navigator.go | EmergencyStop() | line 250-300 | 紧急停止 | [ ] |
| 350 | orthstar | pkg/orthstar/navigator.go | ResumeNavigation() | line 300-350 | 恢复导航 | [ ] |

---

## 第三部分：前端 (任务 351-450)

### 3.1 核心组件 (任务 351-380)

| # | 模块 | 文件 | 函数/组件 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 351 | app | App.tsx | App Component | line 1-50 | 应用加载 | [ ] |
| 352 | app | App.tsx | useEffect init | line 50-100 | 初始化逻辑 | [ ] |
| 353 | app | App.tsx | State Management | line 100-150 | 状态管理 | [ ] |
| 354 | app | App.tsx | Event Handling | line 150-200 | 事件处理 | [ ] |
| 355 | app | App.tsx | Render Logic | line 200-250 | 渲染逻辑 | [ ] |
| 356 | store | stores/strategyStore.ts | StrategyStore | line 20-50 | 策略状态 | [ ] |
| 357 | store | stores/strategyStore.ts | setStrategy() | line 50-100 | 设置策略 | [ ] |
| 358 | store | stores/strategyStore.ts | getStrategy() | line 100-150 | 获取策略 | [ ] |
| 359 | store | stores/strategyStore.ts | updateStrategy() | line 150-200 | 更新策略 | [ ] |
| 360 | store | stores/strategyStore.ts | deleteStrategy() | line 200-250 | 删除策略 | [ ] |
| 361 | store | stores/nemtExecutionStore.ts | NemtExecutionStore | line 20-50 | 执行状态 | [ ] |
| 362 | store | stores/nemtExecutionStore.ts | execute() | line 50-100 | 执行逻辑 | [ ] |
| 363 | store | stores/nemtExecutionStore.ts | getStatus() | line 100-150 | 获取状态 | [ ] |
| 364 | store | stores/nemtExecutionStore.ts | cancel() | line 150-200 | 取消执行 | [ ] |
| 365 | store | stores/capsuleStore.ts | CapsuleStore | line 20-50 | 胶囊状态 | [ ] |
| 366 | store | stores/uiStore.ts | UIStore | line 20-50 | UI 状态 | [ ] |
| 367 | store | stores/dualBufferStore.ts | DualBufferStore | line 20-50 | 双缓冲状态 | [ ] |
| 368 | store | stores/binanceStore.ts | BinanceStore | line 20-50 | 币安状态 | [ ] |
| 369 | service | services/nemtPipeline.ts | NEMTPipeline | line 20-100 | NEMT 流水线 | [ ] |
| 370 | service | services/nemtPipeline.ts | process() | line 100-150 | 处理数据 | [ ] |
| 371 | service | services/nemtPipeline.ts | execute() | line 150-200 | 执行流水线 | [ ] |
| 372 | service | services/executionService.ts | ExecutionService | line 20-50 | 执行服务 | [ ] |
| 373 | service | services/strategyService.ts | StrategyService | line 20-50 | 策略服务 | [ ] |
| 374 | service | services/marketService.ts | MarketService | line 20-50 | 市场服务 | [ ] |
| 375 | service | services/notionService.ts | NotionService | line 20-50 | Notion 服务 | [ ] |
| 376 | hook | hooks/useElectron.ts | useElectron | line 20-50 | Electron Hook | [ ] |
| 377 | hook | hooks/useElectron.ts | invoke() | line 50-100 | 调用主进程 | [ ] |
| 378 | hook | hooks/useElectron.ts | onEvent() | line 100-150 | 事件监听 | [ ] |
| 379 | event | events/eventBus.ts | EventBus | line 20-50 | 事件总线 | [ ] |
| 380 | event | events/eventBus.ts | emit() | line 50-100 | 发送事件 | [ ] |
| 381 | event | events/eventBus.ts | on() | line 100-150 | 监听事件 | [ ] |

### 3.2 策略模块 (任务 382-420)

| # | 模块 | 文件 | 函数/组件 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 382 | strategy | backtest/engineCore.ts | BacktestEngineCore | line 20-50 | 回测核心引擎 | [ ] |
| 383 | strategy | backtest/engineCore.ts | init() | line 50-100 | 初始化 | [ ] |
| 384 | strategy | backtest/engineCore.ts | run() | line 100-150 | 运行回测 | [ ] |
| 385 | strategy | backtest/backtestEngine.ts | BacktestEngine | line 20-50 | 回测引擎 | [ ] |
| 386 | strategy | backtest/backtestEngine.ts | start() | line 50-100 | 开始回测 | [ ] |
| 387 | strategy | backtest/backtestEngine.ts | pause() | line 100-150 | 暂停回测 | [ ] |
| 388 | strategy | backtest/backtestEngine.ts | stop() | line 150-200 | 停止回测 | [ ] |
| 389 | strategy | backtest/backtestEngine.ts | getResults() | line 200-250 | 获取结果 | [ ] |
| 390 | strategy | backtest/dataLoader.ts | DataLoader | line 20-50 | 数据加载器 | [ ] |
| 391 | strategy | backtest/dataLoader.ts | loadCSV() | line 50-100 | 加载 CSV | [ ] |
| 392 | strategy | backtest/dataLoader.ts | loadBinance() | line 100-150 | 加载 Binance | [ ] |
| 393 | strategy | backtest/dataLoader.ts | getData() | line 150-200 | 获取数据 | [ ] |
| 394 | strategy | backtest/store.ts | BacktestStore | line 20-50 | 回测状态 | [ ] |
| 395 | strategy | backtest/types.ts | BacktestTypes | line 20-50 | 回测类型 | [ ] |
| 396 | strategy | indicators/technicalIndicators.ts | TechnicalIndicators | line 20-50 | 技术指标 | [ ] |
| 397 | strategy | indicators/technicalIndicators.ts | calculateRSI() | line 50-100 | 计算 RSI | [ ] |
| 398 | strategy | indicators/technicalIndicators.ts | calculateMACD() | line 100-150 | 计算 MACD | [ ] |
| 399 | strategy | indicators/technicalIndicators.ts | calculateBollinger() | line 150-200 | 计算布林带 | [ ] |
| 400 | strategy | indicators/technicalIndicators.ts | calculateMA() | line 200-250 | 计算均线 | [ ] |
| 401 | strategy | nemt/nemtCalculator.ts | NEMTCalculator | line 20-50 | NEMT 计算器 | [ ] |
| 402 | strategy | nemt/nemtCalculator.ts | calculate() | line 50-100 | NEMT 计算 | [ ] |
| 403 | strategy | nemt/nemtCalculator.ts | getState() | line 100-150 | 获取状态 | [ ] |
| 404 | strategy | nemt/index.ts | NEMTIndex | line 20-50 | NEMT 索引 | [ ] |
| 405 | strategy | exchange/binanceAdapter.ts | BinanceAdapter | line 20-50 | 币安适配器 | [ ] |
| 406 | strategy | exchange/binanceAdapter.ts | getKlines() | line 50-100 | 获取K线 | [ ] |
| 407 | strategy | exchange/binanceAdapter.ts | placeOrder() | line 100-150 | 下单 | [ ] |
| 408 | strategy | exchange/binanceAdapter.ts | getBalance() | line 150-200 | 获取余额 | [ ] |
| 409 | strategy | optimizer/optimizer.ts | Optimizer | line 20-50 | 优化器 | [ ] |
| 410 | strategy | optimizer/optimizer.ts | optimize() | line 50-100 | 优化逻辑 | [ ] |
| 411 | strategy | optimizer/optimizer.ts | gridSearch() | line 100-150 | 网格搜索 | [ ] |
| 412 | strategy | optimizer/optimizer.ts | randomSearch() | line 150-200 | 随机搜索 | [ ] |
| 413 | strategy | config/strategyConfig.ts | StrategyConfig | line 20-50 | 策略配置 | [ ] |
| 414 | strategy | templates/strategyTemplates.ts | StrategyTemplates | line 20-50 | 策略模板 | [ ] |
| 415 | strategy | integration/storeIntegration.ts | StoreIntegration | line 20-50 | 状态集成 | [ ] |
| 416 | strategy | interfaces/IStrategy.ts | IStrategy | line 20-50 | 策略接口 | [ ] |
| 417 | strategy | examples.ts | StrategyExamples | line 20-50 | 策略示例 | [ ] |
| 418 | strategy | algorithm/algorithm.ts | Algorithm | line 20-50 | 算法 | [ ] |
| 419 | strategy | types/kline.ts | KLine Types | line 20-50 | K线类型 | [ ] |

### 3.3 AI 模块 (任务 421-440)

| # | 模块 | 文件 | 函数/组件 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 421 | ai | client/deepseekClient.ts | DeepSeekClient | line 20-50 | DeepSeek 客户端 | [ ] |
| 422 | ai | client/deepseekClient.ts | analyze() | line 50-100 | 分析逻辑 | [ ] |
| 423 | ai | client/deepseekClient.ts | generate() | line 100-150 | 生成逻辑 | [ ] |
| 424 | ai | strategy/aiStrategy.ts | AIStrategy | line 20-50 | AI 策略 | [ ] |
| 425 | ai | strategy/aiStrategy.ts | onTick() | line 50-100 | Tick 处理 | [ ] |
| 426 | ai | strategy/aiStrategy.ts | generateSignal() | line 100-150 | 生成信号 | [ ] |
| 427 | ai | risk/riskManager.ts | AIRiskManager | line 20-50 | AI 风控 | [ ] |
| 428 | ai | risk/riskManager.ts | assess() | line 50-100 | 风险评估 | [ ] |
| 429 | ai | risk/riskManager.ts | prevent() | line 100-150 | 风险预防 | [ ] |
| 430 | ai | sentiment/sentimentFetcher.ts | SentimentFetcher | line 20-50 | 情绪获取 | [ ] |
| 431 | ai | sentiment/sentimentFetcher.ts | fetch() | line 50-100 | 获取情绪 | [ ] |
| 432 | ai | strategy/strategyGenerator.ts | StrategyGenerator | line 20-50 | 策略生成器 | [ ] |
| 433 | ai | index.ts | AIIndex | line 20-50 | AI 索引 | [ ] |
| 434 | trader | alpha/strategy/strategy.ts | AlphaStrategy | line 20-50 | Alpha 策略 | [ ] |
| 435 | trader | alpha/model/model.ts | Model | line 20-50 | 模型 | [ ] |
| 436 | trader | alpha/dataset/dataset.ts | Dataset | line 20-50 | 数据集 | [ ] |
| 437 | trader | alpha/strategy/index.ts | AlphaStrategyIndex | line 20-50 | Alpha 索引 | [ ] |
| 438 | trader | engine/mainEngine.ts | MainEngine | line 20-50 | 主引擎 | [ ] |
| 439 | trader | engine/logger.ts | TraderLogger | line 20-50 | 交易日志 | [ ] |
| 440 | trader | gateway/baseGateway.ts | BaseGateway | line 20-50 | 基础网关 | [ ] |

### 3.4 Electron 容器 (任务 441-450)

| # | 模块 | 文件 | 函数/组件 | 断点位置 | 预期结果 | 状态 |
|---|------|------|-----------|----------|----------|------|
| 441 | electron | electron/src/main.ts | main() | line 1-50 | Electron 入口 | [ ] |
| 442 | electron | electron/src/main.ts | createWindow() | line 50-100 | 创建窗口 | [ ] |
| 443 | electron | electron/src/main.ts | setupIPC() | line 100-150 | 设置 IPC | [ ] |
| 444 | electron | electron/src/main.ts | startPython() | line 150-200 | 启动 Python | [ ] |
| 445 | electron | electron/src/main.ts | handlePythonOutput() | line 200-250 | 处理输出 | [ ] |
| 446 | electron | electron/src/main.ts | cleanup() | line 250-300 | 清理资源 | [ ] |
| 447 | electron | electron/src/preload.ts | preload() | line 1-50 | 预加载脚本 | [ ] |
| 448 | electron | electron/src/preload.ts | exposeAPI() | line 50-100 | 暴露 API | [ ] |
| 449 | electron | main.ts | main process | line 1-50 | 主进程 | [ ] |
| 450 | electron | preload.ts | context bridge | line 1-50 | 上下文桥接 | [ ] |

---

## 第四部分：集成测试 (任务 451-500)

### 4.1 端到端测试 (任务 451-470)

| # | 模块 | 测试场景 | 测试目标 | 预期结果 | 状态 |
|---|------|----------|----------|----------|------|
| 451 | e2e | Python + Gateway gRPC | 通信协议 | protobuf 序列化正常 | [ ] |
| 452 | e2e | Python + Gateway gRPC | 服务调用 | gRPC 方法调用成功 | [ ] |
| 453 | e2e | Python + Gateway gRPC | 错误处理 | 错误正确传播 | [ ] |
| 454 | e2e | Python + Gateway gRPC | 超时处理 | 超时正确响应 | [ ] |
| 455 | e2e | Python + Gateway gRPC | 重连机制 | 连接断开后重连 | [ ] |
| 456 | e2e | Frontend + Backend API | REST 调用 | HTTP 请求正常 | [ ] |
| 457 | e2e | Frontend + Backend API | 认证流程 | JWT 认证工作 | [ ] |
| 458 | e2e | Frontend + Backend API | 数据格式 | JSON 序列化正常 | [ ] |
| 459 | e2e | Frontend + Backend API | 错误响应 | API 错误正确处理 | [ ] |
| 460 | e2e | Frontend + Backend API | CORS | 跨域请求正常 | [ ] |
| 461 | e2e | Electron + Python IPC | 进程通信 | stdin/stdout 通信 | [ ] |
| 462 | e2e | Electron + Python IPC | JSON-RPC | JSON-RPC 协议 | [ ] |
| 463 | e2e | Electron + Python IPC | 命令执行 | 命令正确执行 | [ ] |
| 464 | e2e | Electron + Python IPC | 输出解析 | 输出正确解析 | [ ] |
| 465 | e2e | Electron + Python IPC | 错误传播 | Python 错误正确传播 | [ ] |
| 466 | e2e | Notion 集成 | 页面创建 | Notion API 调用 | [ ] |
| 467 | e2e | Notion 集成 | 数据同步 | 数据同步正常 | [ ] |
| 468 | e2e | Notion 集成 | 错误处理 | Notion 错误处理 | [ ] |
| 469 | e2e | Binance 集成 | 数据拉取 | Binance API 调用 | [ ] |
| 470 | e2e | Binance 集成 | 订单执行 | 订单正确执行 | [ ] |

### 4.2 性能测试 (任务 471-485)

| # | 模块 | 测试目标 | 测试方法 | 预期结果 | 状态 |
|---|------|----------|----------|----------|------|
| 471 | perf | 回测性能 | 500条K线处理时间 | < 1秒 | [ ] |
| 472 | perf | 回测性能 | 1000条K线处理时间 | < 2秒 | [ ] |
| 473 | perf | 回测性能 | 5000条K线处理时间 | < 10秒 | [ ] |
| 474 | perf | 回测性能 | 并发回测 | 多策略同时回测 | [ ] |
| 475 | perf | 回测性能 | 内存占用 | < 500MB | [ ] |
| 476 | perf | 前端渲染 | 首屏加载时间 | < 2秒 | [ ] |
| 477 | perf | 前端渲染 | 1000条数据渲染 | 无卡顿 | [ ] |
| 478 | perf | 前端渲染 | 图表更新 | 实时更新流畅 | [ ] |
| 479 | perf | 前端渲染 | 状态更新 | React 重渲染优化 | [ ] |
| 480 | perf | 前端渲染 | 大数据集虚拟化 | 虚拟列表工作 | [ ] |
| 481 | perf | 内存泄漏 | 长时间运行 | 内存稳定 | [ ] |
| 482 | perf | 内存泄漏 | 事件监听清理 | 无内存泄漏 | [ ] |
| 483 | perf | 内存泄漏 | 定时器清理 | 定时器正确清理 | [ ] |
| 484 | perf | 内存泄漏 | 组件卸载 | 组件正确卸载 | [ ] |
| 485 | perf | 数据库 | 查询性能 | < 100ms | [ ] |

### 4.3 错误处理 (任务 486-500)

| # | 模块 | 测试场景 | 测试方法 | 预期结果 | 状态 |
|---|------|----------|----------|----------|------|
| 486 | error | 网络中断 | 重连机制 | 自动重连成功 | [ ] |
| 487 | error | 网络中断 | 离线模式 | 离线数据缓存 | [ ] |
| 488 | error | 网络中断 | 恢复同步 | 恢复后数据同步 | [ ] |
| 489 | error | 数据异常 | 空数据 | 空数据处理 | [ ] |
| 490 | error | 数据异常 | 格式错误 | 格式验证 | [ ] |
| 491 | error | 数据异常 | 缺失字段 | 默认值处理 | [ ] |
| 492 | error | 数据异常 | 异常值 | 异常值检测 | [ ] |
| 493 | error | 并发冲突 | 竞态条件 | 锁机制工作 | [ ] |
| 494 | error | 并发冲突 | 死锁 | 无死锁 | [ ] |
| 495 | error | 并发冲突 | 资源竞争 | 资源正确分配 | [ ] |
| 496 | error | 并发冲突 | 状态一致性 | 最终一致性 | [ ] |
| 497 | error | 服务异常 | 服务崩溃 | 优雅降级 | [ ] |
| 498 | error | 服务异常 | 超时处理 | 超时正确处理 | [ ] |
| 499 | error | 服务异常 | 熔断器 | 熔断触发/恢复 | [ ] |
| 500 | error | 服务异常 | 限流 | 请求正确限流 | [ ] |

---

## 执行指南

### 推荐执行顺序

```
第1阶段: Python 基础 (1-50)     → 理解核心架构
第2阶段: Python 胶囊 (51-140)  → 调试各模块
第3阶段: Python 测试 (141-200) → 验证功能
第4阶段: Go Gateway (201-250) → API 服务
第5阶段: Go 引擎 (251-310)    → 核心逻辑
第6阶段: Go 基础设施 (311-350) → 支撑模块
第7阶段: 前端核心 (351-381)   → 状态管理
第8阶段: 前端业务 (382-450)   → 功能模块
第9阶段: 集成测试 (451-500)   → 端到端验证
```

### 状态符号说明

| 符号 | 含义 | 说明 |
|------|------|------|
| `[ ]` | 未开始 | 尚未调试 |
| `[x]` | 已完成 | 调试通过 |
| `[!]` | 发现问题 | 需要修复 |
| `[~]` | 部分完成 | 需继续 |
| `[?]` | 需要信息 | 需更多上下文 |

### 调试技巧

#### PyCharm 调试
1. 设置条件断点: `右键断点 → Conditions`
2. 监视变量: Debug 面板 → Watches
3. Evaluate 表达式: Debug 控制台输入

#### GoLand 调试
1. 设置条件断点: `右键断点 → Condition`
2. 日志点: 输出变量值
3. 调试子进程: `GODEBUG=追其者=1`

---

## 文件路径参考

### Python 后端
- `nemt_os/nemt/core/` - 核心模块
- `nemt_os/nemt/evolution/` - 进化模块
- `nemt_os/tests/` - 测试文件

### Go 后端
- `src/nemt-go/cmd/` - 入口程序
- `src/nemt-go/pkg/` - 包模块

### 前端
- `web/src/` - React 源码
- `web/src/stores/` - Zustand 状态
- `electron/src/` - Electron 源码

---

*最后更新: 2026-05-03*
