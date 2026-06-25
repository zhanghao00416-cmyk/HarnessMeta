# A 组入口 Prompt（仅 Task，无 Context Bundle）

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

### 代码库探索指引
- 先从 `models.py` 和 `channels/base.py` 开始读
- 测试文件 `tests/test_email_channel.py` 定义了具体预期行为
- `service.py` 展示了 Service 层如何使用 Channel

---

> **这是 A 组（对照组）。Agent 只看到以上内容，看不到 Spec/Architecture 的解析结果。**
