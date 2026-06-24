# 域职责映射

> 由 harness-specify-arch 根据 project.yaml 的 features 和 constitution 自动生成。
> 本文档定义每个域包的职责边界，是分层架构的核心参考。

## 概述

本文档将每个域包映射到其职责，并定义域之间的边界。

## 分层规则（回顾）

```
{{layer_rules}}
```

域禁止：
- 直接访问外部服务 SDK（必须通过 Provider/Infra 层）
- 硬编码配置值（必须通过配置管理）
- 反向依赖（下层不得调用上层）

---

## 域注册表

> 每个业务域一行，由 harness-specify 根据功能拆解自动填充。

### {{domain_name}} — [TBD: filled by Fxx]

| 方面 | 详情 |
|------|------|
| 包 | `{{package_path}}` |
| 职责 | {{responsibility}} |
| 关键文件 | {{key_files}} |
| 依赖 | {{dependencies}} |
| API 端点 | {{api_endpoints}} |
| 数据模型 | {{data_models}} |
| 工单 | {{order_ids}} |

---

## 域间调用规则

| 调用方 | 被调用方 | 方式 | 说明 |
|--------|---------|------|------|
| {{caller_domain}} | {{callee_domain}} | {{method}} | {{reason}} |

---

## 跨域禁止清单

以下调用关系**严格禁止**：

| 禁止调用 | 原因 |
|----------|------|
| {{forbidden_caller}} → {{forbidden_callee}} | {{reason}} |

---

## 变更规则

1. 新增域时必须更新本文档
2. 域职责变更需评估对所有关联域的影响
3. 同步更新 `DEPENDENCY_MAP.md` 和 `FACT_REGISTRY.md`
