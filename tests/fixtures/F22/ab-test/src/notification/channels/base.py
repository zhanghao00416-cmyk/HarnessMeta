from abc import ABC, abstractmethod
from ..models import Notification, NotificationStatus


class ChannelAdapter(ABC):
    """渠道适配器接口 — 所有渠道发送器必须实现此接口。

    设计意图（ADR-002）：
    - 核心 NotificationService 不关心具体渠道实现
    - 新增渠道只需实现此接口（满足 REQ-NOT-003）
    """

    @abstractmethod
    def send(self, notification: Notification) -> NotificationStatus:
        """发送通知，返回最终发送状态。
        
        Args:
            notification: 待发送的通知对象
            
        Returns:
            SENT 如果发送成功，FAILED 如果无法发送
        """

    @abstractmethod
    def retry(self, notification: Notification, max_attempts: int = 3) -> NotificationStatus:
        """重试发送通知。失败时自动重试，每次间隔 30 秒。
        
        Args:
            notification: 待发送的通知对象
            max_attempts: 最大重试次数（包含首次发送），默认 3
            
        Returns:
            SENT 如果重试成功，FAILED 如果全部尝试失败
        """

    @abstractmethod
    def get_status(self, notification_id: str) -> NotificationStatus:
        """查询通知的发送状态。
        
        Args:
            notification_id: 通知唯一标识
            
        Returns:
            当前状态（PENDING / SENT / FAILED）
        """
