"""
Notion 适配器 (Notion Adapter)
提供与 Notion API 的标准化接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class NotionPage:
    """Notion 页面数据"""
    page_id: str
    title: str
    content: str
    properties: Dict[str, Any] = field(default_factory=dict)
    created_time: Optional[datetime] = None
    last_edited_time: Optional[datetime] = None
    url: str = ""
    parent_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'page_id': self.page_id,
            'title': self.title,
            'content': self.content,
            'properties': self.properties,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'last_edited_time': self.last_edited_time.isoformat() if self.last_edited_time else None,
            'url': self.url,
            'parent_id': self.parent_id
        }


@dataclass
class NotionDatabase:
    """Notion 数据库"""
    database_id: str
    title: str
    properties: Dict[str, Any] = field(default_factory=dict)
    url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'database_id': self.database_id,
            'title': self.title,
            'properties': self.properties,
            'url': self.url
        }


class BaseNotionAdapter(ABC):
    """
    Notion 适配器抽象基类
    
    定义与 Notion API 交互的标准接口
    """

    def __init__(self, api_token: str = None):
        self.api_token = api_token
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @abstractmethod
    def connect(self) -> bool:
        """连接到 Notion API"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    def get_database(self, database_id: str) -> Optional[NotionDatabase]:
        """获取数据库信息"""
        pass

    @abstractmethod
    def query_database(
        self,
        database_id: str,
        filter_query: Dict[str, Any] = None,
        sorts: List[Dict[str, Any]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """查询数据库"""
        pass

    @abstractmethod
    def get_page(self, page_id: str) -> Optional[NotionPage]:
        """获取页面内容"""
        pass

    @abstractmethod
    def create_page(
        self,
        parent_id: str,
        properties: Dict[str, Any],
        content: str = None
    ) -> Optional[NotionPage]:
        """创建页面"""
        pass

    @abstractmethod
    def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any] = None,
        content: str = None
    ) -> bool:
        """更新页面"""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        filter_type: str = "page",
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索 Notion 内容"""
        pass


class MockNotionAdapter(BaseNotionAdapter):
    """
    Mock Notion 适配器
    
    用于开发测试，返回模拟数据
    """

    def __init__(self, api_token: str = None):
        super().__init__(api_token)
        self._mock_databases: Dict[str, NotionDatabase] = {}
        self._mock_pages: Dict[str, NotionPage] = {}
        self._init_mock_data()

    def _init_mock_data(self) -> None:
        """初始化模拟数据"""
        # 策略数据库
        self._mock_databases['strategy-db'] = NotionDatabase(
            database_id='strategy-db',
            title='策略库',
            properties={
                'Name': {'type': 'title'},
                'Status': {'type': 'select'},
                'Type': {'type': 'select'},
                'Sharpe': {'type': 'number'},
                'WinRate': {'type': 'number'},
                'Created': {'type': 'date'}
            },
            url='https://notion.so/mock-strategy-db'
        )

        # 回测数据库
        self._mock_databases['backtest-db'] = NotionDatabase(
            database_id='backtest-db',
            title='回测记录',
            properties={
                'Strategy': {'type': 'relation'},
                'Status': {'type': 'select'},
                'Return': {'type': 'number'},
                'Sharpe': {'type': 'number'},
                'MaxDD': {'type': 'number'}
            },
            url='https://notion.so/mock-backtest-db'
        )

        # 模拟页面
        self._mock_pages['page-001'] = NotionPage(
            page_id='page-001',
            title='NEMT-DCI 策略 A',
            content='基于NEMT理论的DCI策略，表现良好。',
            properties={
                'Status': 'alive',
                'Type': 'nemt-dci',
                'Sharpe': 1.8,
                'WinRate': 0.62
            },
            created_time=datetime.now(),
            last_edited_time=datetime.now(),
            url='https://notion.so/mock-page-001'
        )

    def connect(self) -> bool:
        logger.info("[MockNotion] Connecting to mock Notion...")
        self._is_connected = True
        logger.info("[MockNotion] Connected successfully")
        return True

    def disconnect(self) -> None:
        self._is_connected = False
        logger.info("[MockNotion] Disconnected")

    def get_database(self, database_id: str) -> Optional[NotionDatabase]:
        return self._mock_databases.get(database_id)

    def query_database(
        self,
        database_id: str,
        filter_query: Dict[str, Any] = None,
        sorts: List[Dict[str, Any]] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        # 返回所有页面作为模拟结果
        return [page.to_dict() for page in self._mock_pages.values()]

    def get_page(self, page_id: str) -> Optional[NotionPage]:
        return self._mock_pages.get(page_id)

    def create_page(
        self,
        parent_id: str,
        properties: Dict[str, Any],
        content: str = None
    ) -> Optional[NotionPage]:
        import uuid
        page_id = f"page-{uuid.uuid4().hex[:8]}"
        page = NotionPage(
            page_id=page_id,
            title=properties.get('Name', 'New Page'),
            content=content or '',
            properties=properties,
            created_time=datetime.now(),
            last_edited_time=datetime.now()
        )
        self._mock_pages[page_id] = page
        return page

    def update_page(
        self,
        page_id: str,
        properties: Dict[str, Any] = None,
        content: str = None
    ) -> bool:
        if page_id not in self._mock_pages:
            return False
        
        page = self._mock_pages[page_id]
        if properties:
            page.properties.update(properties)
        if content is not None:
            page.content = content
        page.last_edited_time = datetime.now()
        return True

    def search(
        self,
        query: str,
        filter_type: str = "page",
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        # 简单模拟搜索
        results = []
        for page in self._mock_pages.values():
            if query.lower() in page.title.lower() or query.lower() in page.content.lower():
                results.append(page.to_dict())
        return results

    def get_status(self) -> Dict[str, Any]:
        return {
            'connected': self._is_connected,
            'databases': len(self._mock_databases),
            'pages': len(self._mock_pages)
        }


class NotionSyncAdapter:
    """
    Notion 同步适配器
    
    专门用于 NEMT 系统与 Notion 之间的数据同步
    """

    def __init__(self, adapter: BaseNotionAdapter = None):
        self.adapter = adapter or MockNotionAdapter()

    def sync_strategy_to_notion(self, strategy: Dict[str, Any]) -> bool:
        """同步策略到 Notion"""
        try:
            # 查找策略数据库
            db = self.adapter.get_database('strategy-db')
            if not db:
                logger.error("[NotionSync] Strategy database not found")
                return False

            # 创建或更新策略页面
            properties = {
                'Name': strategy.get('name', 'Unnamed Strategy'),
                'Status': strategy.get('status', 'testing'),
                'Type': strategy.get('type', 'unknown'),
                'Sharpe': strategy.get('sharpe_ratio', 0),
                'WinRate': strategy.get('win_rate', 0)
            }

            page = self.adapter.create_page('strategy-db', properties)
            logger.info(f"[NotionSync] Strategy synced: {page.page_id}")
            return True

        except Exception as e:
            logger.error(f"[NotionSync] Failed to sync strategy: {e}")
            return False

    def sync_backtest_to_notion(self, backtest: Dict[str, Any]) -> bool:
        """同步回测结果到 Notion"""
        try:
            db = self.adapter.get_database('backtest-db')
            if not db:
                logger.error("[NotionSync] Backtest database not found")
                return False

            properties = {
                'Strategy': backtest.get('strategy_id', ''),
                'Status': backtest.get('status', 'completed'),
                'Return': backtest.get('return_pct', 0),
                'Sharpe': backtest.get('sharpe_ratio', 0),
                'MaxDD': backtest.get('max_drawdown', 0)
            }

            page = self.adapter.create_page('backtest-db', properties)
            logger.info(f"[NotionSync] Backtest synced: {page.page_id}")
            return True

        except Exception as e:
            logger.error(f"[NotionSync] Failed to sync backtest: {e}")
            return False

    def get_strategies_from_notion(self) -> List[Dict[str, Any]]:
        """从 Notion 获取策略列表"""
        try:
            results = self.adapter.query_database('strategy-db')
            return results
        except Exception as e:
            logger.error(f"[NotionSync] Failed to get strategies: {e}")
            return []

    def get_backtests_from_notion(self) -> List[Dict[str, Any]]:
        """从 Notion 获取回测列表"""
        try:
            results = self.adapter.query_database('backtest-db')
            return results
        except Exception as e:
            logger.error(f"[NotionSync] Failed to get backtests: {e}")
            return []
