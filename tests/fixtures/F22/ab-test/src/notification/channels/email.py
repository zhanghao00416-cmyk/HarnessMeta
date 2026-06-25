import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

from .base import ChannelAdapter
from ..models import Notification, NotificationStatus


class EmailChannelSender(ChannelAdapter):
    """邮件渠道发送器。

    实现 REQ-NOT-001（邮件发送）和 REQ-NOT-002（状态追踪）。
    遵循 ADR-001：使用标准 SMTP 协议，不依赖第三方 API。

    约束感知（来自 Context Bundle）：
    - CON-NOT-001 [block]：Service 层不得直接访问数据库。
      → EmailChannelSender 位于 infrastructure 层，无需数据库操作。
    - CON-NOT-002 [block]：消息持久化由 NotificationService 负责。
      → Channel 层只负责发送，不涉及持久化。
    """

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 25):
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._status: dict[str, NotificationStatus] = {}

    def send(self, notification: Notification) -> NotificationStatus:
        """发送邮件通知（满足 REQ-NOT-001）。"""
        try:
            msg = self._build_message(notification)
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as smtp:
                smtp.send_message(msg)
            self._status[notification.id] = NotificationStatus.SENT
            return NotificationStatus.SENT
        except Exception:
            self._status[notification.id] = NotificationStatus.FAILED
            return NotificationStatus.FAILED

    def retry(self, notification: Notification, max_attempts: int = 3) -> NotificationStatus:
        """重试发送（满足 AC-NOT-002：最多 3 次，间隔 30 秒）。"""
        for attempt in range(max_attempts):
            try:
                msg = self._build_message(notification)
                with smtplib.SMTP(self._smtp_host, self._smtp_port) as smtp:
                    smtp.send_message(msg)
                self._status[notification.id] = NotificationStatus.SENT
                return NotificationStatus.SENT
            except Exception:
                notification.retry_count += 1
                if attempt < max_attempts - 1:
                    time.sleep(30)

        self._status[notification.id] = NotificationStatus.FAILED
        return NotificationStatus.FAILED

    def get_status(self, notification_id: str) -> NotificationStatus:
        """查询发送状态（满足 REQ-NOT-002：状态追踪 pending/sent/failed）。"""
        return self._status.get(notification_id, NotificationStatus.PENDING)

    def _build_message(self, notification: Notification) -> MIMEMultipart:
        """构建 MIME 邮件消息。"""
        msg = MIMEMultipart()
        msg["From"] = "notification@system.local"
        msg["To"] = notification.recipient
        msg["Subject"] = notification.title
        msg["Date"] = formatdate(localtime=True)
        msg.attach(MIMEText(notification.body, "plain", "utf-8"))
        return msg
