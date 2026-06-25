from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime


class NotificationStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


@dataclass
class Notification:
    id: str
    title: str
    body: str
    recipient: str
    status: NotificationStatus = NotificationStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
