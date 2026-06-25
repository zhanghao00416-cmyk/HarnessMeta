# B 组入口 Prompt（Task + Context Bundle）

---

## 任务：实现 EmailChannelSender

### 背景
通知系统需要支持邮件渠道发送。基础接口 `ChannelAdapter` 已定义在
`src/notification/channels/base.py`。你需要实现 `src/notification/channels/email.py`
中的 `EmailChannelSender` 类。

### 目标
实现 `EmailChannelSender` 类，继承 `ChannelAdapter` 接口。

### 代码库结构
```
ab-test/
├── src/notification/
│   ├── models.py          # Notification, NotificationStatus（已实现）
│   ├── repository.py      # NotificationRepository 接口（已实现）
│   ├── service.py         # NotificationService（已实现）
│   └── channels/
│       ├── base.py        # ChannelAdapter 接口（已实现）
│       └── email.py       # ← 你需要实现这个文件
└── tests/
    └── test_email_channel.py  # 测试用例（定义预期行为）
```

### 要求
1. 实现 `send()` — 使用 Python 标准库 `smtplib.SMTP` 发送邮件
2. 实现 `retry()` — 失败时重试指定次数，每次间隔 30 秒
3. 实现 `get_status()` — 返回通知当前状态
4. 必须继承 `ChannelAdapter` 接口

### 通过标准
运行 `pytest tests/ -v`，6 个测试全部通过。

---

## ⬇️ 以下为 Context Bundle（自动解析的上下文）

```yaml
# ============================================================
# Context Bundle — 由 harness-context v2.0 自动生成
# 输入：task_id = "F22-order-001"
# 以下信息来自 Frozen Schema 引用链的自动解析
# ============================================================

# ── 关联需求（V1 路径：task.requirement_refs → Spec） ──
requirements:
  - id: "REQ-NOT-001"
    title: "用户可以通过邮件接收通知"
    description: "当系统产生通知事件时，系统应该通过 SMTP 将通知内容发送给用户。"
    priority: "must"
    coverage: "full"

  - id: "REQ-NOT-002"
    title: "通知发送状态可追踪"
    description: "用户可以查看通知的发送状态（pending/sent/failed），并看到失败原因。"
    priority: "must"
    coverage: "full"

# ── 验收标准（V2 路径：validation_steps → Spec） ──
acceptance_criteria:
  - id: "AC-NOT-002"
    description: "SMTP 发送失败时自动重试 3 次，间隔 30 秒"
    covered_by_step: "VAL-F22-001-002"

# ── 架构约束（V3 路径：constraint_refs → Architecture） ──
constraints:
  - id: "CON-NOT-001"
    severity: "block"
    rule: "Service 层不得直接访问数据库，必须通过 Repository 接口"
    note: "EmailChannelSender 位于 infrastructure 层，不需要关心此约束"

  - id: "CON-NOT-002"
    severity: "block"
    rule: "所有通知事件必须持久化到数据库后才能确认消费"
    note: "持久化由 NotificationService 负责，Channel 只负责发送"

# ── 架构决策（来自 Architecture.adr） ──
architecture_decisions:
  - id: "ADR-001"
    title: "使用 SMTP 而非第三方 API"
    decision: "使用标准 SMTP 协议发送邮件，不依赖 SendGrid/AWS SES"
    consequence: "需要自行处理 SMTP 连接池和重试逻辑"

  - id: "ADR-002"
    title: "使用 Repository 模式隔离数据访问"
    decision: "引入 Repository 接口，Service 层通过 Repository 访问数据"
    consequence: "EmailChannelSender 不需要关心数据持久化"

# ── 解析追踪（这些信息来自以下文件） ──
resolve_trace:
  - source: "F22-specs"        → requirements, acceptance_criteria
  - source: "notification-architecture" → constraints, architecture_decisions
```

### 代码库探索指引
- 先从 `models.py` 和 `channels/base.py` 开始读
- 测试文件 `tests/test_email_channel.py` 定义了具体预期行为
- `service.py` 展示了 Service 层如何使用 Channel（含 Repository）
- **注意**：CON-NOT-001 和 CON-NOT-002 规定了数据访问约束。EmailChannelSender 不应出现任何数据库操作代码。

---

> **这是 B 组（实验组）。Agent 看到 Task + 上述 Context Bundle。**
