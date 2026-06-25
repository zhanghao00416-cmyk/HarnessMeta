---
artifact:
  id: F22-order-001
  type: task
  title: F22 通知推送系统 — 核心服务实现
  domain: notification
  status: active
  version: "1.0.0"
  source:
    skill: harness-order
    feature_id: F22
    created: "2026-06-25T14:10:00+08:00"
    updated: "2026-06-25T14:10:00+08:00"
  dependencies:
    - F22-specs
    - notification-architecture
---

# 工单 F22-order-001：核心服务实现

## 需求映射

| 需求 ID | 覆盖程度 | 场景 |
|---------|---------|------|
| REQ-NOT-001 | full | SC-REQ-NOT-001-01, SC-REQ-NOT-001-02 |
| REQ-NOT-002 | full | SC-REQ-NOT-002-01 |
| REQ-NOT-003 | partial | SC-REQ-NOT-003-01 |

## 目标

实现通知发送核心服务，支持邮件渠道发送和状态追踪。

## 实现步骤

### STEP-F22-001-001：创建 NotificationService 类

**类型**：code
**预估工作量**：m
**描述**：在 services/notification 目录下创建 NotificationService 类，实现 send() 方法，接收通知事件并调用渠道发送器。
**关联需求**：REQ-NOT-001

### STEP-F22-001-002：实现邮件渠道发送器

**类型**：code
**预估工作量**：m
**描述**：实现 EmailChannelSender，集成 SMTP 客户端。支持重试 3 次，间隔 30 秒。
**关联需求**：REQ-NOT-001
**依赖**：STEP-F22-001-001

### STEP-F22-001-003：实现发送状态追踪

**类型**：code
**预估工作量**：s
**描述**：在 NotificationRecord 模型中记录发送状态（pending/sent/failed）和失败原因。
**关联需求**：REQ-NOT-002

### STEP-F22-001-004：编写单元测试

**类型**：test
**预估工作量**：m
**描述**：为 NotificationService 和 EmailChannelSender 编写单元测试，覆盖率 > 80%。
**关联需求**：REQ-NOT-001, REQ-NOT-002

## 验证步骤

### VAL-F22-001-001：运行单元测试

**类型**：automated_test
**命令**：`pytest tests/services/test_notification.py -v`
**预期结果**：所有测试通过，覆盖率 > 80%
**关联需求**：REQ-NOT-001, REQ-NOT-002

### VAL-F22-001-002：验证邮件发送重试

**类型**：automated_test
**命令**：`pytest tests/services/test_notification.py::test_retry -v`
**预期结果**：失败时重试 3 次，最终状态为 failed
**验收标准**：AC-NOT-002

### VAL-F22-001-003：验证状态追踪

**类型**：automated_test
**命令**：`pytest tests/services/test_notification.py::test_status_tracking -v`
**预期结果**：状态正确记录为 pending → sent/failed
**验收标准**：AC-NOT-003

### VAL-F22-001-004：代码审查

**类型**：code_review
**预期结果**：无 block 项，命名规范符合项目约定
**验收标准**：AC-NOT-004

## 完成定义

### 标准

- [ ] DOD-F22-001-001：所有实现步骤已完成
- [ ] DOD-F22-001-002：所有验证步骤已通过
- [ ] DOD-F22-001-003：覆盖率 > 80%

### 必须评审

| 类型 | 状态 |
|------|------|
| self_review | pending |

## 约束

### 架构规则

- 分层架构：Service 层不得直接访问数据库

### 约束引用

- CON-NOT-001
- CON-NOT-002

### 代码规范

- 遵循项目命名规范
- 类型注解覆盖率 100%

### 必读文档

- ARCHITECTURE.md
- API_CONTRACT.md

## 风险

### RISK-F22-001-001：SMTP 服务配置延迟

**影响**：medium
**缓解**：使用本地 MailHog 进行开发测试

## 执行指令

```text
按 AGENTS.md 启动；执行工单 F22-order-001，严格阶段 1→2→3。
阶段 1：读 DEPENDENCY_MAP F22-order-001 行 + F22-specs + notification-architecture
阶段 2：仅实现 implementation_steps 清单
阶段 3：自审 + 更新 feature_list / progress / session-handoff
```
