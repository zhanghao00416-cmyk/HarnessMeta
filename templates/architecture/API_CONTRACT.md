# API 契约

> 由 harness-specify-arch 根据 project.yaml 的 features 和 constitution 自动生成。
> 本文档是所有 API 端点的权威来源，代码实现必须与此保持一致。

## 概述

本文档定义 {{project_name}} 的 API 契约。所有端点遵循 REST 约定。

## 基础 URL

```
{{api_prefix}}
```

## 通用响应信封

```json
{
  "code": 0,
  "message": "ok",
  "request_id": "uuid",
  "trace_id": "uuid",
  "data": { }
}
```

错误响应：

```json
{
  "code": {{error_code_example}},
  "message": "{{error_message}}",
  "request_id": "uuid",
  "trace_id": "uuid"
}
```

---

## API 选型决策表

> 实现业务域前，先在此表中确定每个域使用的端点类型。

| 业务域 | 端点 | 方法 | 传输方式 | 说明 |
|--------|------|------|---------|------|
| {{domain}} | {{path}} | {{method}} | JSON / SSE | {{description}} |

---

## 端点注册表

> 按业务域分组，每个端点包含请求/响应格式。

### {{Domain}} — [TBD: filled by Fxx]

| Method | Path | Description |
|--------|------|-------------|
| {{method}} | {{path}} | {{description}} |

#### {{method}} {{path}}

**Request**:

```json
{
  "{{field}}": "{{type}}"
}
```

**Response**:

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "{{field}}": "{{type}}"
  }
}
```

---

## SSE 事件协议（如适用）

> 若项目包含流式传输功能，在此定义所有 SSE 事件类型。

| 事件类型 | 触发时机 | data 字段 |
|----------|---------|----------|
| {{event_type}} | {{trigger}} | {{data_schema}} |

---

## 变更规则

1. API 契约变更**必须先于代码**：先改本文档，再改实现
2. 涉及接口变更时必须走 `docs/meta/CHANGE_WORKFLOW.md` 流程
3. 变更后同步更新 `docs/meta/FACT_REGISTRY.md` 的相关条目
