---
artifact:
  id: notification-architecture
  type: architecture
  title: 通知推送系统架构规格
  domain: notification
  status: reviewed
  version: "1.0.0"
  source:
    skill: harness-specify-arch
    feature_id: F22
    created: "2026-06-25T14:05:00+08:00"
    updated: "2026-06-25T14:05:00+08:00"
  dependencies:
    - F22-specs
---

# 通知推送系统架构规格

## 概述

通知推送系统采用分层架构，包含 Service 层和 Infrastructure 层。所有通知通过统一的事件队列分发，支持多渠道并行发送。

## 模块

### MOD-NOT-001：notification

**职责**：负责通知事件的接收、路由和发送
**层**：service

**接口**：
- NotificationService.send()
  - 协议：internal_api
  - 描述：接收通知事件并触发发送流程

**依赖**：MOD-NOT-002

**约束**：
- 不得直接调用外部 HTTP API

### MOD-NOT-002：channel-sender

**职责**：负责具体渠道（邮件）的发送实现
**层**：infrastructure

## 约束

### CON-NOT-001：分层访问约束

**类型**：architecture
**规则**：Service 层不得直接访问数据库，必须通过 Repository 接口
**违反后果**：block
**验证方法**：code_review
**关联模块**：MOD-NOT-001
**关联需求**：REQ-NOT-001

### CON-NOT-002：消息可靠性约束

**类型**：reliability
**规则**：所有通知事件必须持久化到数据库后才能确认消费
**违反后果**：block
**验证方法**：code_review
**关联模块**：MOD-NOT-001
**关联需求**：REQ-NOT-001

### CON-NOT-003：渠道适配器接口约束

**类型**：architecture
**规则**：所有渠道发送器必须实现 ChannelAdapter 接口（send / retry / getStatus）
**违反后果**：block
**验证方法**：code_review
**关联需求**：REQ-NOT-003

### CON-NOT-004：邮件发送性能约束

**类型**：performance
**规则**：单封邮件发送耗时不超过 5 秒（P95）
**违反后果**：warning
**验证方法**：automated_test
**关联需求**：REQ-NOT-001

## 架构决策

### ADR-001：使用 SMTP 而非第三方 API

**状态**：accepted
**背景**：通知系统需要发送邮件，可选方案包括 SMTP 直连或第三方 API（SendGrid/AWS SES）
**决策**：使用标准 SMTP 协议发送邮件，不依赖第三方 API
**后果**：需要自行处理 SMTP 连接池和重试逻辑，但不增加外部依赖
**关联需求**：REQ-NOT-001

### ADR-002：使用 Repository 模式隔离数据访问

**状态**：accepted
**背景**：Service 层需要访问通知记录数据
**决策**：引入 Repository 接口，Service 层通过 Repository 访问数据
**后果**：增加一层抽象，但提高了可测试性
**关联需求**：REQ-NOT-001, REQ-NOT-002

## 追踪矩阵

**关联需求**：
- REQ-NOT-001
- REQ-NOT-002
- REQ-NOT-003

**受影响任务**：
- F22-order-001

**上游**：
- spec: F22-specs
