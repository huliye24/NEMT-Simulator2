"""
StrategyMarket - 策略市场

提供策略发布、发现、订阅、评价等市场功能。
"""

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

__all__ = [
    "StrategyListing",
    "StrategyCategory",
    "StrategyReview",
    "StrategyMarket",
]


class StrategyCategory(Enum):
    """策略分类"""

    TREND = "trend"  # 趋势策略
    MEAN_REVERSION = "mean_reversion"  # 均值回归
    ARBITRAGE = "arbitrage"  # 套利策略
    SCALPING = "scalping"  # 刷单策略
    NEWS = "news"  # 新闻驱动
    ML = "ml"  # 机器学习
    CUSTOM = "custom"  # 自定义


@dataclass
class StrategyListing:
    """策略列表"""

    listing_id: str
    strategy_id: str
    author_id: str
    author_name: str
    name: str
    description: str
    category: StrategyCategory
    version: str
    price: float  # 0 表示免费
    subscription_count: int = 0
    rating: float = 0.0
    review_count: int = 0
    tags: list[str] = field(default_factory=list)
    preview_image: str = ""
    documentation_url: str = ""
    status: str = "draft"  # draft, published, suspended
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    published_at: float = 0


@dataclass
class StrategyReview:
    """策略评价"""

    review_id: str
    listing_id: str
    user_id: str
    user_name: str
    rating: float  # 1-5
    title: str
    content: str
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    is_verified_purchase: bool = False
    helpful_count: int = 0
    created_at: float = field(default_factory=time.time)


@dataclass
class Subscription:
    """订阅"""

    subscription_id: str
    listing_id: str
    user_id: str
    start_date: float
    end_date: float
    auto_renew: bool = True
    status: str = "active"  # active, cancelled, expired


class StrategyMarket:
    """
    策略市场

    示例:
    ```python
    market = StrategyMarket()

    # 发布策略
    listing = market.publish_strategy(
        strategy_id="strategy-123",
        author_id="user-1",
        author_name="Author",
        name="Trend Follower",
        description="A simple trend following strategy",
        category=StrategyCategory.TREND,
        price=99.0,
    )

    # 搜索策略
    results = market.search(
        query="trend",
        category=StrategyCategory.TREND,
        min_rating=4.0,
    )

    # 订阅策略
    subscription = market.subscribe("listing-123", "user-456")

    # 评价策略
    market.add_review("listing-123", user_id="user-789", rating=5.0, ...)
    ```
    """

    def __init__(self):
        self._listings: dict[str, StrategyListing] = {}
        self._reviews: dict[str, list[StrategyReview]] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._lock = threading.RLock()
        self._logger = logging.getLogger("StrategyMarket")

    def publish_strategy(
        self,
        strategy_id: str,
        author_id: str,
        author_name: str,
        name: str,
        description: str,
        category: StrategyCategory,
        price: float = 0,
        tags: list[str] = None,
        documentation_url: str = "",
        **kwargs,
    ) -> StrategyListing:
        """发布策略"""
        listing_id = str(uuid.uuid4())

        with self._lock:
            listing = StrategyListing(
                listing_id=listing_id,
                strategy_id=strategy_id,
                author_id=author_id,
                author_name=author_name,
                name=name,
                description=description,
                category=category,
                version=kwargs.get("version", "1.0.0"),
                price=price,
                tags=tags or [],
                documentation_url=documentation_url,
                status="published",
                published_at=time.time(),
            )

            self._listings[listing_id] = listing
            self._reviews[listing_id] = []

            self._logger.info(f"策略已发布: {name} ({listing_id})")
            return listing

    def update_listing(self, listing_id: str, **kwargs) -> bool:
        """更新列表"""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing:
                return False

            for key, value in kwargs.items():
                if hasattr(listing, key):
                    setattr(listing, key, value)
            listing.updated_at = time.time()
            return True

    def suspend_listing(self, listing_id: str) -> bool:
        """暂停策略"""
        return self.update_listing(listing_id, status="suspended")

    def delete_listing(self, listing_id: str) -> bool:
        """删除策略"""
        with self._lock:
            if listing_id in self._listings:
                del self._listings[listing_id]
                return True
            return False

    def get_listing(self, listing_id: str) -> StrategyListing | None:
        """获取列表"""
        return self._listings.get(listing_id)

    def search(
        self,
        query: str = None,
        category: StrategyCategory = None,
        min_rating: float = None,
        max_price: float = None,
        free_only: bool = False,
        sort_by: str = "rating",
        limit: int = 20,
        offset: int = 0,
    ) -> list[StrategyListing]:
        """搜索策略"""
        with self._lock:
            results = list(self._listings.values())

        # 过滤
        if query:
            query_lower = query.lower()
            results = [r for r in results if query_lower in r.name.lower() or query_lower in r.description.lower()]

        if category:
            results = [r for r in results if r.category == category]

        if min_rating is not None:
            results = [r for r in results if r.rating >= min_rating]

        if max_price is not None:
            results = [r for r in results if r.price <= max_price]

        if free_only:
            results = [r for r in results if r.price == 0]

        # 只显示已发布的
        results = [r for r in results if r.status == "published"]

        # 排序
        if sort_by == "rating":
            results.sort(key=lambda r: r.rating, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda r: r.published_at, reverse=True)
        elif sort_by == "popular":
            results.sort(key=lambda r: r.subscription_count, reverse=True)
        elif sort_by == "price_low":
            results.sort(key=lambda r: r.price)
        elif sort_by == "price_high":
            results.sort(key=lambda r: r.price, reverse=True)

        # 分页
        return results[offset : offset + limit]

    def get_trending(self, limit: int = 10) -> list[StrategyListing]:
        """获取热门策略"""
        return self.search(sort_by="popular", limit=limit)

    def get_new_releases(self, limit: int = 10) -> list[StrategyListing]:
        """获取新上架"""
        return self.search(sort_by="newest", limit=limit)

    def subscribe(
        self,
        listing_id: str,
        user_id: str,
        duration_days: int = 30,
    ) -> Subscription | None:
        """订阅策略"""
        listing = self._listings.get(listing_id)
        if not listing:
            return None

        # 检查是否已订阅
        with self._lock:
            for sub in self._subscriptions.values():
                if sub.listing_id == listing_id and sub.user_id == user_id:
                    if sub.status == "active":
                        return None  # 已订阅

        subscription_id = str(uuid.uuid4())
        now = time.time()

        subscription = Subscription(
            subscription_id=subscription_id,
            listing_id=listing_id,
            user_id=user_id,
            start_date=now,
            end_date=now + duration_days * 86400,
        )

        with self._lock:
            self._subscriptions[subscription_id] = subscription
            listing.subscription_count += 1

        self._logger.info(f"订阅策略: {listing.name} by {user_id}")
        return subscription

    def cancel_subscription(self, subscription_id: str) -> bool:
        """取消订阅"""
        with self._lock:
            sub = self._subscriptions.get(subscription_id)
            if not sub:
                return False

            sub.status = "cancelled"
            sub.auto_renew = False
            return True

    def get_subscription(self, subscription_id: str) -> Subscription | None:
        """获取订阅"""
        return self._subscriptions.get(subscription_id)

    def get_user_subscriptions(self, user_id: str) -> list[Subscription]:
        """获取用户订阅"""
        with self._lock:
            return [sub for sub in self._subscriptions.values() if sub.user_id == user_id and sub.status == "active"]

    def add_review(
        self,
        listing_id: str,
        user_id: str,
        user_name: str,
        rating: float,
        title: str,
        content: str,
        pros: list[str] = None,
        cons: list[str] = None,
        is_verified_purchase: bool = False,
    ) -> StrategyReview | None:
        """添加评价"""
        listing = self._listings.get(listing_id)
        if not listing:
            return None

        review_id = str(uuid.uuid4())

        review = StrategyReview(
            review_id=review_id,
            listing_id=listing_id,
            user_id=user_id,
            user_name=user_name,
            rating=rating,
            title=title,
            content=content,
            pros=pros or [],
            cons=cons or [],
            is_verified_purchase=is_verified_purchase,
        )

        with self._lock:
            self._reviews[listing_id].append(review)

            # 更新评分
            reviews = self._reviews[listing_id]
            total_rating = sum(r.rating for r in reviews)
            listing.rating = total_rating / len(reviews)
            listing.review_count = len(reviews)

        self._logger.info(f"策略评价: {listing.name} - {rating}星")
        return review

    def get_reviews(self, listing_id: str) -> list[StrategyReview]:
        """获取评价"""
        return self._reviews.get(listing_id, [])

    def helpful_review(self, review_id: str) -> bool:
        """标记评价有帮助"""
        with self._lock:
            for reviews in self._reviews.values():
                for review in reviews:
                    if review.review_id == review_id:
                        review.helpful_count += 1
                        return True
        return False

    def get_author_listings(self, author_id: str) -> list[StrategyListing]:
        """获取作者的所有策略"""
        with self._lock:
            return [listing for listing in self._listings.values() if listing.author_id == author_id]

    def get_stats(self) -> dict[str, Any]:
        """获取市场统计"""
        with self._lock:
            listings = list(self._listings.values())
            published = [l for l in listings if l.status == "published"]

            return {
                "total_listings": len(listings),
                "published_listings": len(published),
                "total_subscriptions": len(self._subscriptions),
                "total_reviews": sum(len(r) for r in self._reviews.values()),
                "avg_rating": sum(l.rating for l in published) / len(published) if published else 0,
                "free_strategies": len([l for l in published if l.price == 0]),
                "paid_strategies": len([l for l in published if l.price > 0]),
            }
