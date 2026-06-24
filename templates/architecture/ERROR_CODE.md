# 错误码体系

> 由 harness-specify-arch 根据 project.yaml 的 features 自动生成。
> 本文档是所有错误码的权威来源，禁止在代码中硬编码未注册的错误码。

## 概述

所有平台错误使用**域编码**。错误码按域分类。绝不向客户端返回原始堆栈跟踪。

## 规范格式

| 场景 | `code` 字段类型 | 示例 | 说明 |
|------|----------------|------|------|
| **REST JSON 响应** | `integer` | `{{code_example}}` | 成功为 `0` |
| **SSE `error` 事件** | `string` | `"{{sse_prefix}}{{code_example}}"` | 带前缀格式 |
| **日志/轨迹** | `string` | `"{{sse_prefix}}{{code_example}}"` | 便于检索 |
| **代码异常类** | `int` | `{{code_example}}` | 与 REST 整数一致 |

---

## 错误响应格式

```json
{
  "code": {{code}},
  "message": "{{message}}",
  "request_id": "uuid",
  "trace_id": "uuid"
}
```

---

## 域编码范围

> 按业务域划分编码范围，由 harness-specify 根据功能拆解自动分配。

| Range | Domain | Description |
|-------|--------|-------------|
| 0xxx | System | 通用/基础设施错误 |
| {{range}} | {{domain}} | {{description}} |

---

## 错误码定义

### 0xxx — 系统/基础设施 — [TBD: filled by Fxx]

| Code | Name | HTTP Status | Description |
|------|------|-------------|-------------|
| 0001 | INTERNAL_ERROR | 500 | 未处理的内部错误 |
| 0002 | CONFIG_ERROR | 500 | 配置加载或校验错误 |
| 0003 | SERVICE_UNAVAILABLE | 503 | 所需服务不可用 |
| 0004 | TIMEOUT_ERROR | 504 | 操作超时 |
| 0005 | VALIDATION_ERROR | 400 | 请求校验失败 |
| 0006 | RATE_LIMITED | 429 | 请求速率超限 |

### {{range}} — {{domain}} — [TBD: filled by Fxx]

| Code | Name | HTTP Status | Description |
|------|------|-------------|-------------|
| {{code}} | {{name}} | {{http_status}} | {{description}} |

---

## 变更规则

1. 新增错误码时必须先在本文档注册，再写代码
2. 错误码变更必须同步 `docs/meta/FACT_REGISTRY.md`
3. 涉及 SSE 事件时同步 `API_CONTRACT.md` 的事件协议章节
4. 禁止复用已废弃的错误码编号
