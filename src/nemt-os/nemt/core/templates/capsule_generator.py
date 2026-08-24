"""
Capsule Template Generator - 胶囊代码生成器

自动生成符合分形迭代标准的 Capsule 骨架代码。

版本: v1.0.0
更新: 2026-04-27
"""

import os

CAPSULE_TEMPLATE = '''"""
{module_name} - {description}

{description_extended}

版本: {version}
更新时间: {update_date}
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from nemt.core.capsule import FractalCapsule


# =============================================================================
# Domain Models
# =============================================================================

{domain_models}

# =============================================================================
# Capsule
# =============================================================================

class {capsule_name}Capsule(FractalCapsule):
    """
    {capsule_description}

    负责：
{responsibilities}

    五阶段方法已实现。

    示例:
    ```python
    capsule = {capsule_name}Capsule("{capsule_name_lower}")
    capsule.init()
    result = capsule.run_fractal_iteration()
    ```
    """

    def __init__(self, capsule_id: str = "{capsule_name_lower}"):
        super().__init__(capsule_id, version="{version}")
        self._layer = "L1"

        # 内部状态
{internal_state}

        # 配置
        self._config_loaded = False

    # ========================================
    # 【看】观察阶段
    # ========================================

    def observe_phase(self) -> Dict[str, Any]:
        """
        【看】观察阶段 - {observe_description}
        """
        return {{
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "observe",
            "timestamp": datetime.now().isoformat(),
            "inputs": {{
{observe_inputs}
            }},
            "outputs": {{
{observe_outputs}
            }},
            "constraints": {{
{observe_constraints}
            }},
            "dependencies": {observe_dependencies},
            "risks": [
{observe_risks}
            ],
            "subscribes_to": {subscribe_events},
            "publishes": {publish_events},
        }}

    # ========================================
    # 【画】设计阶段
    # ========================================

    def design_phase(self) -> Dict[str, Any]:
        """
        【画】设计阶段 - 定义接口契约和骨架
        """
        return {{
            "capsule_id": self._capsule_id,
            "layer": "L1",
            "phase": "design",
            "timestamp": datetime.now().isoformat(),
            "public_api": {{
{public_api}
            }},
            "input_schema": {{
                "type": "object",
                "properties": {{
                    "symbol": {{"type": "string"}},
                }},
                "required": ["symbol"],
            }},
            "output_schema": {{
                "type": "object",
                "properties": {{
                    "status": {{"type": "string"}},
                    "data": {{"type": "object"}},
                }},
            }},
            "event_contracts": {{
                "publishes": {publish_events},
                "subscribes": {subscribe_events},
            }},
        }}

    # ========================================
    # 【填】实现阶段
    # ========================================

    def implement_phase(self) -> None:
        """
        【填】实现阶段 - 填充核心逻辑
        """
        # 加载配置
        self._load_config()

        # 初始化内部状态
{implement_init}

        self._logger.info(f"{{self._capsule_id}} 实现阶段完成")

    def _load_config(self) -> None:
        """加载配置"""
        if self._config is None:
            return

        # TODO: 添加配置加载逻辑
        self._config_loaded = True

    # ========================================
    # 【验】验证阶段
    # ========================================

    def verify_phase(self) -> Dict[str, Any]:
        """
        【验】验证阶段 - 确保实现正确
        """
        checks = {{
            "config_loaded": self._config_loaded,
            "dependencies_injected": self._event_bus is not None,
            "initialized": self._initialized,
        }}

        passed = all(checks.values())

        return {{
            "capsule_id": self._capsule_id,
            "phase": "verify",
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
            "passed": passed,
            "metrics": {{
                "total_checks": len(checks),
                "passed_checks": sum(1 for v in checks.values() if v),
            }},
        }}

    # ========================================
    # 【连】集成阶段
    # ========================================

    def integrate_phase(self) -> None:
        """
        【连】集成阶段 - 与上下游对接
        """
        self._logger.info(f"{{self._capsule_id}} 集成阶段完成")
        self._logger.info(f"  上游: {{self._get_upstream()}}")
        self._logger.info(f"  下游: {{self._get_downstream()}}")

    def _get_upstream(self) -> str:
        """获取上游模块"""
        return "TBD"

    def _get_downstream(self) -> str:
        """获取下游模块"""
        return "TBD"

    # ========================================
    # 标准生命周期
    # ========================================

    def init(self) -> None:
        """
        初始化胶囊 - 订阅事件
        """
        # TODO: 添加事件订阅
        self._initialized = True
        self._logger.info(f"{{self._capsule_id}} 初始化完成")

    def exec(self) -> Dict[str, Any]:
        """
        执行主要逻辑
        """
        return {{
            "capsule_id": self._capsule_id,
            "status": "running",
            "timestamp": datetime.now().isoformat(),
        }}

    def shutdown(self) -> None:
        """
        关闭胶囊 - 清理资源
        """
        self._running = False
        self._logger.info(f"{{self._capsule_id}} 已关闭")

    # ========================================
    # 公开 API
    # ========================================

{public_methods}

    # ========================================
    # 内部方法
    # ========================================

{internal_methods}


# =============================================================================
# Factory
# =============================================================================

def create_{capsule_name_lower}_capsule(capsule_id: str = "{capsule_name_lower}") -> {capsule_name}Capsule:
    """
    工厂方法：创建 {capsule_name}Capsule

    Args:
        capsule_id: 胶囊 ID

    Returns:
        {capsule_name}Capsule 实例
    """
    return {capsule_name}Capsule(capsule_id=capsule_id)
'''


def generate_capsule(
    capsule_name: str,
    description: str,
    responsibilities: list[str],
    version: str = "1.0.0",
    module_name: str | None = None,
    domain_models: str = "",
    observe_inputs: str = "",
    observe_outputs: str = "",
    observe_constraints: str = "",
    observe_dependencies: str = "[]",
    observe_risks: str = "",
    subscribe_events: str = "[]",
    publish_events: str = "[]",
    public_api: str = "",
    internal_state: str = "",
    implement_init: str = "",
    public_methods: str = "",
    internal_methods: str = "",
) -> str:
    """
    生成 Capsule 代码

    Args:
        capsule_name: 胶囊名称
        description: 描述
        responsibilities: 职责列表
        version: 版本号
        module_name: 模块名
        domain_models: 领域模型代码
        observe_inputs: 观察阶段输入
        observe_outputs: 观察阶段输出
        observe_constraints: 观察阶段约束
        observe_dependencies: 观察阶段依赖
        observe_risks: 观察阶段风险
        subscribe_events: 订阅事件
        publish_events: 发布事件
        public_api: 公开 API
        internal_state: 内部状态
        implement_init: 实现阶段初始化
        public_methods: 公开方法
        internal_methods: 内部方法

    Returns:
        生成的代码字符串
    """
    module_name = module_name or f"{capsule_name.lower()}_capsule"

    responsibility_lines = "\n".join(f"    - {r}" for r in responsibilities)

    return CAPSULE_TEMPLATE.format(
        module_name=module_name,
        description=description,
        description_extended=description,
        version=version,
        update_date=datetime.now().strftime("%Y-%m-%d"),
        capsule_name=capsule_name,
        capsule_description=description,
        responsibilities=responsibility_lines,
        capsule_name_lower=capsule_name.lower(),
        domain_models=domain_models or "# TODO: 添加领域模型",
        observe_inputs=observe_inputs
        or '                "symbol": {"type": "string", "source": "config", "required": True},',
        observe_outputs=observe_outputs or '                "result": {"type": "object", "description": "操作结果"},',
        observe_constraints=observe_constraints or '                "timeout": {"type": "number", "default": 30},',
        observe_dependencies=observe_dependencies,
        observe_risks=observe_risks or '                {{"type": "数据缺失", "mitigation": "默认值处理"}}',
        subscribe_events=subscribe_events,
        publish_events=publish_events,
        public_api=public_api or '                "process(symbol)": "处理数据",',
        internal_state=internal_state or "        self._state = {}",
        implement_init=implement_init or "        pass",
        public_methods=public_methods or "    pass",
        internal_methods=internal_methods or "    pass",
    )


def save_capsule(capsule_name: str, output_dir: str, **kwargs) -> str:
    """
    生成并保存 Capsule 代码

    Args:
        capsule_name: 胶囊名称
        output_dir: 输出目录
        **kwargs: generate_capsule 的其他参数

    Returns:
        保存的文件路径
    """
    os.makedirs(output_dir, exist_ok=True)

    module_name = f"{capsule_name.lower()}_capsule"
    file_path = os.path.join(output_dir, f"{module_name}.py")

    code = generate_capsule(capsule_name=capsule_name, module_name=module_name, **kwargs)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(code)

    return file_path


# =============================================================================
# Predefined Capsule Templates
# =============================================================================

PREDEFINED_TEMPLATES = {
    "market": {
        "description": "市场数据胶囊",
        "responsibilities": [
            "订阅市场数据源",
            "数据预处理",
            "缓存管理",
            "发布市场事件",
        ],
        "observe_inputs": """
                "raw_klines": {"type": "list", "format": "{timestamp, open, high, low, close, volume}", "required": True},
                "symbols": {"type": "list", "default": ["BTCUSDT"]},""",
        "observe_outputs": """
                "processed_klines": {"type": "DataFrame"},
                "indicators": {"type": "dict"},
                "events": {"type": "list"},""",
        "observe_constraints": """
                "latency": "<100ms",
                "reconnect": "断线自动重连",
                "cache_ttl": "60s",""",
        "observe_dependencies": '["EventBus", "ConfigCenter"]',
        "observe_risks": """
                {"type": "API不稳定", "mitigation": "重试机制+熔断"},
                {"type": "数据延迟", "mitigation": "本地缓存+时间戳校验"},""",
        "subscribe_events": '["market.subscribe_request", "market.kline_update"]',
        "publish_events": '["market.kline", "market.price_update", "market.candle_closed"]',
        "public_api": """
                "get_klines(symbol, timeframe, limit)": "获取K线数据",
                "get_price(symbol)": "获取最新价格",
                "subscribe(symbol, callback)": "订阅实时数据",""",
        "internal_state": """
        self._symbols: List[str] = []
        self._data_caches: Dict[str, Any] = {}
        self._subscribers: Dict[str, List[Callable]] = {}""",
    },
    "signal": {
        "description": "信号生成胶囊",
        "responsibilities": [
            "接收市场数据",
            "计算技术指标",
            "生成交易信号",
            "信号过滤和融合",
        ],
        "observe_inputs": """
                "market_data": {"type": "dict", "source": "MarketCapsule", "required": True},
                "indicators_config": {"type": "dict", "default": {"rsi_period": 14}},""",
        "observe_outputs": """
                "signals": {"type": "list", "format": "[{type, entry, sl, tp, confidence}]"},
                "indicators": {"type": "dict"},""",
        "observe_constraints": """
                "max_signals_per_symbol": 1,
                "signal_validity_period": "1小时",
                "min_confidence": 0.6,""",
        "observe_dependencies": '["MarketCapsule", "EventBus", "ConfigCenter"]',
        "subscribe_events": '["market.price_update", "market.candle_closed"]',
        "publish_events": '["signal.generated", "signal.filtered"]',
        "public_api": """
                "generate_signal(symbol, market_data)": "生成交易信号",
                "calculate_indicators(prices)": "计算技术指标",
                "filter_signals(signals)": "过滤信号",
                "get_latest_signals(n)": "获取最新信号",""",
        "internal_state": """
        self._signals: List[Any] = []
        self._signal_count = 0
        self._indicators: Dict[str, Any] = {}""",
    },
    "risk": {
        "description": "风控胶囊",
        "responsibilities": [
            "仓位管理",
            "止损/止盈检查",
            "回撤控制",
            "风险评分",
        ],
        "observe_inputs": """
                "signals": {"type": "list", "source": "SignalCapsule", "required": True},
                "account_balance": {"type": "number", "source": "ExecutionCapsule", "required": True},""",
        "observe_outputs": """
                "approved_signals": {"type": "list"},
                "rejected_signals": {"type": "list"},
                "risk_metrics": {"type": "dict"},""",
        "observe_constraints": """
                "max_position_size": 1.0,
                "max_drawdown": 0.2,
                "max_daily_loss": 0.05,""",
        "observe_dependencies": '["SignalCapsule", "ExecutionCapsule", "ConfigCenter"]',
        "subscribe_events": '["signal.generated"]',
        "publish_events": '["risk.approved", "risk.rejected", "risk.alert"]',
        "public_api": """
                "check_signal(signal)": "检查信号是否通过风控",
                "check_position(position)": "检查仓位",
                "update_balance(balance)": "更新账户余额",
                "get_risk_metrics()": "获取风控指标",""",
        "internal_state": """
        self._max_position_size = 1.0
        self._max_drawdown = 0.2
        self._current_balance = 0.0
        self._positions: Dict[str, Any] = {}""",
    },
}


def generate_from_template(
    template_name: str,
    output_dir: str,
    capsule_name: str | None = None,
) -> str:
    """
    从预定义模板生成 Capsule

    Args:
        template_name: 模板名称
        output_dir: 输出目录
        capsule_name: 胶囊名称（可选）

    Returns:
        保存的文件路径
    """
    if template_name not in PREDEFINED_TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}")

    template = PREDEFINED_TEMPLATES[template_name]
    capsule_name = capsule_name or template_name.capitalize()

    return save_capsule(capsule_name=capsule_name, output_dir=output_dir, **template)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        template_name = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
        path = generate_from_template(template_name, output_dir)
        print(f"Generated: {path}")
    else:
        # 生成所有预定义模板
        for template_name in PREDEFINED_TEMPLATES:
            path = generate_from_template(template_name, ".")
            print(f"Generated: {path}")
