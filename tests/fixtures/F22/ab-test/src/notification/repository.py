from abc import ABC, abstractmethod
from .models import Notification


class NotificationRepository(ABC):
    """Repository 接口 — Service 层通过此接口访问数据。

    设计意图（CON-NOT-001 / ADR-002）：
    - Service 层不得直接访问数据库
    - 所有数据访问必须通过 Repository 接口
    - 具体实现（如 SQLAlchemyRepository）在基础设施层
    """

    @abstractmethod
    def save(self, notification: Notification) -> None:
        """持久化通知记录（CON-NOT-002：发送前必须先持久化）"""

    @abstractmethod
    def find_by_id(self, notification_id: str) -> Notification | None:
        """按 ID 查询通知"""

    @abstractmethod
    def update_status(self, notification_id: str, status: str) -> None:
        """更新通知发送状态"""
