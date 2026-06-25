# Phase 3.1 Validation-2：Agent 成功率 AB Test

> **验证目标**：证明 Context Bundle 能提升 Agent 执行成功率
> **验证方式**：AB Test（A 组仅 Task / B 组 Task + Context Bundle）
> **上一阶段**：Validation-1（结构验证 ✅）

---

## 1. 核心问题

Validation-1 证明了 Resolver → Builder → Budget 的**解析正确性**（8/8 resolved，0 broken_ref）。

但这只是"语法验证"。真正的问题是：

> Context Bundle 是否让 Agent 更快、更准确地完成任务？

如果 B 组（有 Context Bundle）不比 A 组（仅有 Task）更好，说明：
- 要么 Context Bundle 包含的信息 Agent 不需要
- 要么 Agent 自己就能从代码库推导出等价的上下文
- 要么 Budget 裁减掉了关键信息

**必须用 AB Test 回答这个问题，而不是继续增加 Fixture**。

---

## 2. 实验设计

### 2.1 变量控制

| 变量 | A 组（对照组） | B 组（实验组） |
|------|-------------|-------------|
| **输入** | Task artifact | Task artifact + Context Bundle |
| **代码库** | 相同 | 相同 |
| **Agent** | 相同（新会话） | 相同（新会话） |
| **Task** | 相同 | 相同 |
| **Spec/Architecture** | Agent 需要自行搜索 | Context Bundle 已解析好 |

### 2.2 测试场景

使用 `tests/fixtures/F22/` 的 Spec + Task + Architecture，构建一个**真实的 Python 项目**：

```
tests/fixtures/F22/ab-test/
├── src/
│   └── notification/
│       ├── __init__.py
│       ├── models.py          # 已有骨架（Notification, NotificationStatus）
│       ├── service.py         # 已有骨架（send 方法为空）
│       ├── channels/
│       │   ├── __init__.py
│       │   ├── base.py        # ChannelAdapter 接口（已有）
│       │   └── email.py       # 待实现（Agent 任务）
│       └── repository.py      # Repository 接口（已有）
├── tests/
│   ├── __init__.py
│   ├── test_email_channel.py  # 测试用例（定义预期行为）
│   ├── test_service.py
│   └── test_retry.py
├── requirements.txt
└── README.md
```

### 2.3 Agent 任务

实现 `src/notification/channels/email.py` 中的 `EmailChannelSender` 类：

- 实现 `send()` — 发送邮件（mock SMTP）
- 实现 `retry()` — 失败重试 3 次，间隔 30 秒
- 实现 `get_status()` — 返回发送状态
- 遵循 CON-NOT-001："Service 层不得直接访问数据库"
- 遵循 CON-NOT-002："消息必须持久化后才能确认消费"
- 通过全部 6 个测试用例

### 2.4 输入差异

**A 组（仅 Task）**：

```
任务：实现 EmailChannelSender 类
文件：src/notification/channels/email.py

要求：
- 实现 send()、retry()、get_status()
- 参考 src/notification/channels/base.py 的接口
- 通过 tests/ 下的全部测试
```

**B 组（Task + Context Bundle）**：

A 组内容 + 以下：

```yaml
# Context Bundle（自动解析的上下文）
requirements:
  - REQ-NOT-001：邮件在 5 秒内送达
  - REQ-NOT-002：发送状态可追踪（pending/sent/failed）

acceptance_criteria:
  - AC-NOT-002：SMTP 失败时自动重试 3 次

constraints:
  - CON-NOT-001 [block]：Service 层不得直接访问数据库
  - CON-NOT-002 [block]：通知事件必须持久化后才能确认消费

architecture_decisions:
  - ADR-001：使用 SMTP 而非第三方 API
  - ADR-002：使用 Repository 模式

resolve_trace:
  - 以上信息来自 F22-specs 和 notification-architecture
```

---

## 3. 评估指标

### 3.1 一级指标（核心）

| 指标 | 含义 | 测量方式 | 预期 B > A |
|------|------|--------|-----------|
| **Verify Pass Rate** | 实现后 `harness-verify` 的 overall_status 是否为 passing | 运行 verify | ✅ |
| **Test Pass Rate** | 6 个测试通过数 / 6 | 运行 pytest | ✅ |
| **Constraint Compliance** | 实现的代码是否遵守 CON-NOT-001/002 | 人工审查 | ✅ |
| **Requirement Coverage** | 3 个 REQ 是否全部实现 | 人工审查 | ✅ |

### 3.2 二级指标（效率）

| 指标 | 含义 | 测量方式 | 预期 B < A |
|------|------|--------|-----------|
| **返工次数** | Agent 被要求修改的次数 | 计数 | ✅ |
| **Agent 调用次数** | 完成任务的对话轮数 | 计数 | ✅ |
| **Prompt Token 数** | 总输入 token 消耗 | 计数 | ❓（B 组初始 token 更多） |
| **Completion Token 数** | 总输出 token 消耗 | 计数 | ✅ |

### 3.3 成功标准

| 结果 | 判定 | 含义 |
|------|------|------|
| B 组一级指标 > A 组 | ✅ Context Engine 有效 | Phase 3 设计有价值 |
| B 组 = A 组 | ⚠️ Context Bundle 无增益 | 需要审视 Builder 是否过度设计 |
| B 组 < A 组 | ❌ Context Bundle 有害 | 需要审视 Budget 是否裁减了关键信息 |

---

## 4. 执行流程

### 4.1 运行 A 组

```
1. 新开 Agent 会话
2. 提供测试代码库（包含完整 test 文件 + 骨架代码）
3. Agent 只能看到 Task 内容（不含 Context Bundle）
4. Agent 自由探索代码库
5. Agent 实现 EmailChannelSender
6. 运行测试 → 记录 Test Pass Rate
7. 运行 harness-verify → 记录 Verify Pass Rate
8. 记录返工次数 / Agent 轮数 / Token 消耗
```

### 4.2 运行 B 组

```
1. 新开 Agent 会话（与 A 组相同的 Agent 实例）
2. 提供相同的测试代码库
3. Agent 看到 Task + Context Bundle（从 context_bundle.yaml）
4. Agent 自由探索代码库
5. Agent 实现 EmailChannelSender
6. 运行测试 → 记录 Test Pass Rate
7. 运行 harness-verify → 记录 Verify Pass Rate
8. 记录返工次数 / Agent 轮数 / Token 消耗
```

### 4.3 重要约束

- A 组和 B 组**必须在不同的 Agent 会话中运行**（避免记忆污染）
- **每个组只运行一次**（避免学习效应）
- 代码库**完全相同**（测试 git checkout 到相同 commit）
- Agent **不预装任何关于 F22 的知识**

---

## 5. 测试代码库设计

### 5.1 已有代码（骨架）

Agent 不需要从零开始。以下骨架已经存在：

**`src/notification/models.py`**（已有）：
```python
from enum import Enum
from dataclasses import dataclass
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
    status: NotificationStatus
    created_at: datetime
    retry_count: int = 0
```

**`src/notification/channels/base.py`**（已有）：
```python
from abc import ABC, abstractmethod
from ..models import Notification, NotificationStatus

class ChannelAdapter(ABC):
    """渠道适配器接口 — 所有渠道必须实现此接口"""

    @abstractmethod
    def send(self, notification: Notification) -> NotificationStatus:
        """发送通知，返回最终状态"""

    @abstractmethod
    def retry(self, notification: Notification, max_attempts: int = 3) -> NotificationStatus:
        """重试发送，返回最终状态"""

    @abstractmethod
    def get_status(self, notification_id: str) -> NotificationStatus:
        """查询发送状态"""
```

**`src/notification/repository.py`**（已有）：
```python
from abc import ABC, abstractmethod
from .models import Notification

class NotificationRepository(ABC):
    """Repository 接口 — Service 层通过此接口访问数据"""

    @abstractmethod
    def save(self, notification: Notification) -> None:
        """持久化通知记录"""

    @abstractmethod
    def find_by_id(self, notification_id: str) -> Notification | None:
        """按 ID 查询通知"""

    @abstractmethod
    def update_status(self, notification_id: str, status: str) -> None:
        """更新通知状态"""
```

**`src/notification/service.py`**（已有骨架）：
```python
from .models import Notification, NotificationStatus
from .repository import NotificationRepository
from .channels.base import ChannelAdapter


class NotificationService:
    """通知发送服务 — 遵循 CON-NOT-001：不直接访问数据库"""

    def __init__(self, channel: ChannelAdapter, repository: NotificationRepository):
        self.channel = channel
        self.repository = repository

    def send(self, notification: Notification) -> NotificationStatus:
        """
        发送通知并更新状态。
        遵循 CON-NOT-002：先持久化，再确认消费。
        """
        # 1. 先持久化（CON-NOT-002）
        self.repository.save(notification)

        # 2. 发送
        status = self.channel.send(notification)

        # 3. 更新状态
        self.repository.update_status(notification.id, status.value)

        return status
```

### 5.2 测试文件（定义预期行为）

6 个测试用例，Agent 必须全部通过：

**`tests/test_email_channel.py`**：
```python
import pytest
from unittest.mock import Mock, patch
from src.notification.models import Notification, NotificationStatus
from src.notification.channels.email import EmailChannelSender
from datetime import datetime


@pytest.fixture
def notification():
    return Notification(
        id="not-001",
        title="Test",
        body="Test body",
        recipient="test@example.com",
        status=NotificationStatus.PENDING,
        created_at=datetime.now()
    )


class TestEmailChannelSender:

    def test_send_success(self, notification):
        """测试正常发送"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        with patch("smtplib.SMTP") as mock_smtp:
            status = channel.send(notification)
            assert status == NotificationStatus.SENT
            mock_smtp.return_value.__enter__.return_value.send_message.assert_called_once()

    def test_send_failure_with_retry(self, notification):
        """测试发送失败 → 自动重试 → 最终 failed"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__.return_value.send_message.side_effect = Exception("SMTP error")
            status = channel.retry(notification, max_attempts=3)
            assert status == NotificationStatus.FAILED
            assert notification.retry_count == 3

    def test_retry_recovery(self, notification):
        """测试：前 2 次失败，第 3 次成功"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        with patch("smtplib.SMTP") as mock_smtp:
            smtp_instance = mock_smtp.return_value.__enter__.return_value
            smtp_instance.send_message.side_effect = [
                Exception("fail 1"),
                Exception("fail 2"),
                None  # 第 3 次成功
            ]
            status = channel.retry(notification, max_attempts=3)
            assert status == NotificationStatus.SENT
            assert notification.retry_count == 2  # 2 次失败后成功

    def test_get_status(self, notification):
        """测试状态查询"""
        channel = EmailChannelSender(smtp_host="localhost", smtp_port=1025)
        # 初始状态为 PENDING
        assert channel.get_status(notification.id) == NotificationStatus.PENDING

    def test_direct_db_access_forbidden(self, notification):
        """验证 CON-NOT-001：不得直接访问数据库（EmailChannelSender 不应导入 Repository）"""
        import inspect
        from src.notification.channels.email import EmailChannelSender
        source = inspect.getsource(EmailChannelSender)
        # 不应出现任何数据库访问代码
        assert "sql" not in source.lower()
        assert "cursor" not in source.lower()
        assert "execute" not in source.lower()

    def test_persist_before_confirm(self, notification):
        """验证 CON-NOT-002：Service 层先 save 再 send（通过 mock 顺序验证）"""
        from src.notification.service import NotificationService
        from unittest.mock import Mock

        mock_channel = Mock(spec=ChannelAdapter)
        mock_repo = Mock(spec=NotificationRepository)

        service = NotificationService(mock_channel, mock_repo)
        service.send(notification)

        # save 必须在 send 之前调用
        mock_repo.save.assert_called_once_with(notification)
        mock_channel.send.assert_called_once()
        # save 先于 send
        assert mock_repo.save.call_count == 1  # 先
        assert mock_channel.send.call_count == 1  # 后
```

### 5.3 Task（Agent 看到的指令）

```
## 任务：实现 EmailChannelSender

### 背景
通知系统需要支持邮件渠道发送。基础接口 `ChannelAdapter` 已定义在
`src/notification/channels/base.py`。

### 目标
实现 `src/notification/channels/email.py` 中的 `EmailChannelSender` 类。

### 要求
1. 实现 `send()` — 使用 smtplib.SMTP 发送邮件
2. 实现 `retry()` — 失败时重试 max_attempts 次，每次间隔 30 秒
3. 实现 `get_status()` — 返回通知当前状态
4. 继承 `ChannelAdapter` 接口

### 通过标准
运行 `pytest tests/ -v`，6 个测试全部通过。
```

---

## 6. 指标采集模板

### 6.1 执行记录

```yaml
test_run:
  group: "A"  # 或 "B"
  agent: "qwen-max / claude-sonnet / gpt-4o"
  date: "2026-06-25"
  task: "实现 EmailChannelSender"

results:
  # 一级指标
  test_pass_rate:
    total: 6
    passed: ??
    rate: ??

  verify_pass_rate:
    overall_status: "passing / failing"
    requirement_coverage: ??
    constraint_coverage: ??

  constraint_compliance:
    con_not_001: "pass / fail"  # 未直接访问数据库
    con_not_002: "pass / fail"  # 先持久化再确认

  requirement_coverage:
    req_not_001: "pass / fail"  # 邮件发送
    req_not_002: "pass / fail"  # 状态追踪

  # 二级指标
  efficiency:
    rework_count: ??
    agent_turns: ??
    prompt_tokens: ??
    completion_tokens: ??

  # 观察
  observations:
    - "Agent 是否自行搜索了 Spec 文件？"
    - "Agent 是否询问了约束条件？"
    - "Agent 是否产生了不必要的代码？"
```

### 6.2 对比表

| 指标 | A 组（仅 Task） | B 组（Task + Bundle） | Δ |
|------|:---:|:---:|:---:|
| Test Pass Rate | ?/6 | ?/6 | |
| Verify Pass Rate | ? | ? | |
| Constraint Compliance | ?/2 | ?/2 | |
| Requirement Coverage | ?/3 | ?/3 | |
| 返工次数 | ? | ? | |
| Agent 轮数 | ? | ? | |
| Prompt Tokens | ? | ? | |

---

## 7. 测试基础设施

### 7.1 就绪清单

- [ ] `ab-test/src/` — 骨架代码（已有的 models, base, service, repository）
- [ ] `ab-test/tests/` — 6 个测试用例
- [ ] `ab-test/requirements.txt` — smtplib（标准库）+ pytest
- [ ] A 组入口 prompt（仅 Task）
- [ ] B 组入口 prompt（Task + Context Bundle）
- [ ] 指标采集模板

### 7.2 执行

```
# 1. 准备代码库
cd tests/fixtures/F22/ab-test
pip install -r requirements.txt

# 2. 确认测试当前全部失败（Agent 待实现）
pytest tests/ -v
# 预期：6 failed（email.py 不存在或为空）

# 3. 启动 A 组 Agent（新会话）
# 粘贴 A 组入口 prompt

# 4. Agent 完成后，记录指标

# 5. git checkout 到初始状态

# 6. 启动 B 组 Agent（新会话）
# 粘贴 B 组入口 prompt

# 7. Agent 完成后，记录指标

# 8. 填写对比表
```

---

## 8. 决策规则

| 结果 | B 组一级指标 vs A 组 | 判定 | 下一步 |
|------|-------------------|------|--------|
| ✅ 有效 | B > A 且差值 ≥ 20% | Context Engine 创造价值 | 进入 Phase 3.2（更大规模验证） |
| ⚠️ 无效 | B ≈ A（差值 < 20%） | Context Bundle 无增益 | 审视 Builder 内容是否冗余 |
| ❌ 有害 | B < A | Context Bundle 干扰 Agent | 审视 Budget 是否裁减了关键信息，或信息密度是否过高 |

---

> **核心原则：不增加 Fixture，不继续设计。用 AB Test 回答"Context Bundle 是否让 Agent 更好"这个唯一问题。**
