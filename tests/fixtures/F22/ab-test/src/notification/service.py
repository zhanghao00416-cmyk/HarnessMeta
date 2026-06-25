from .models import Notification, NotificationStatus
from .repository import NotificationRepository
from .channels.base import ChannelAdapter


class NotificationService:
    """通知发送服务。

    遵循 CON-NOT-001：通过 Repository 接口访问数据，不直接操作数据库。
    遵循 CON-NOT-002：先持久化通知，再通过 Channel 发送，最后更新状态。
    """

    def __init__(self, channel: ChannelAdapter, repository: NotificationRepository):
        self.channel = channel
        self.repository = repository

    def send(self, notification: Notification) -> NotificationStatus:
        """发送通知（满足 REQ-NOT-001 邮件发送 + REQ-NOT-002 状态追踪）。

        执行顺序（CON-NOT-002）：
        1. 先持久化通知记录
        2. 通过 Channel 发送
        3. 更新最终状态
        """
        # 步骤 1：持久化（CON-NOT-002 要求）
        self.repository.save(notification)

        # 步骤 2：发送
        status = self.channel.send(notification)

        # 步骤 3：更新状态
        self.repository.update_status(notification.id, status.value)

        return status
