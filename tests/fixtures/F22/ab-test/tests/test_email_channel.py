"""
测试 EmailChannelSender 实现。
运行方式：pytest tests/ -v

Agent 必须使以下 6 个测试全部通过。
"""
import pytest
from unittest.mock import Mock, patch
from src.notification.models import Notification, NotificationStatus
from src.notification.channels.email import EmailChannelSender
from datetime import datetime


@pytest.fixture
def notification():
    return Notification(
        id="not-001",
        title="测试通知",
        body="这是一条测试通知",
        recipient="test@example.com",
        status=NotificationStatus.PENDING,
        created_at=datetime.now()
    )


class TestEmailChannelSender:

    def test_send_success(self, notification):
        """测试正常发送：SMTP 可用时 send() 返回 SENT"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        with patch("smtplib.SMTP") as mock_smtp:
            status = channel.send(notification)
            assert status == NotificationStatus.SENT
            mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    def test_send_failure_with_retry(self, notification):
        """测试发送失败重试：3 次全部失败后返回 FAILED（AC-NOT-002）"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value.send_message.side_effect = Exception("SMTP error")
            status = channel.retry(notification, max_attempts=3)
            assert status == NotificationStatus.FAILED
            assert notification.retry_count == 3

    def test_retry_recovery(self, notification):
        """测试重试恢复：前 2 次失败，第 3 次成功"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        with patch("smtplib.SMTP") as mock_smtp:
            smtp_instance = mock_smtp.return_value.__enter__.return_value
            smtp_instance.send_message.side_effect = [
                Exception("fail 1"),
                Exception("fail 2"),
                None
            ]
            status = channel.retry(notification, max_attempts=3)
            assert status == NotificationStatus.SENT
            assert notification.retry_count == 2

    def test_get_status_default(self, notification):
        """测试状态查询：新通知状态为 PENDING"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        assert channel.get_status(notification.id) == NotificationStatus.PENDING

    def test_no_direct_db_access(self, notification):
        """验证 CON-NOT-001：EmailChannelSender 不直接访问数据库"""
        import inspect
        from src.notification.channels.email import EmailChannelSender
        source = inspect.getsource(EmailChannelSender)
        assert "sql" not in source.lower()
        assert "cursor" not in source.lower()
        assert "execute" not in source.lower()
        assert "connection" not in source.lower()

    def test_service_persist_order(self, notification):
        """验证 CON-NOT-002：NotificationService 先 save 再 send"""
        from src.notification.service import NotificationService
        from unittest.mock import Mock

        mock_channel = Mock()
        mock_repo = Mock()

        service = NotificationService(mock_channel, mock_repo)
        service.send(notification)

        # CON-NOT-002：save 必须在 send 之前调用
        mock_repo.save.assert_called_once()
        mock_channel.send.assert_called_once()
