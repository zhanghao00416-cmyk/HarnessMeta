# 数据模型

> 由 harness-specify-arch 根据 project.yaml 的 features 自动生成。
> 本文档是所有数据库模型和存储结构的权威来源。

## 概述

本文档定义 {{project_name}} 的数据模型框架。

| 存储类型 | 用途 | 技术选型 |
|----------|------|---------|
| 主数据库 | {{purpose}} | {{database_tech}} |
| 缓存 | {{purpose}} | {{cache_tech}} |
| 向量存储 | {{purpose}} | {{vector_tech}} |

---

## 主数据库表

> 每张表对应一个 ORM 模型，由对应工单实现。

### {{table_name}} — [TBD: filled by Fxx]

{{table_description}}

| Column | Type | Description |
|--------|------|-------------|
| id | {{type}} | 主键标识符 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 最后更新时间 |

---

## 缓存结构

> 列出 Redis/缓存中使用的 key 模式。

| Key 模式 | 用途 | TTL |
|----------|------|-----|
| {{pattern}} | {{purpose}} | {{ttl}} |

---

## 向量存储集合（如适用）

> 列出向量数据库中的集合配置。

| 集合名 | 维度 | 距离度量 | 用途 |
|--------|------|---------|------|
| {{collection}} | {{dimension}} | {{metric}} | {{purpose}} |

---

## 对象存储（如适用）

> 列出对象存储中的存储桶配置。

| 存储桶 | 用途 | 访问策略 | 大小限制 |
|--------|------|---------|---------|
| {{bucket_name}} | {{purpose}} | {{access_policy}} | {{size_limit}} |

---

## 表关系图

```
{{table_a}} 1──N {{table_b}}
{{table_b}} N──1 {{table_c}}
```

---

## 变更规则

1. 数据模型变更必须同步更新本文档
2. 涉及表结构变更时，需评估对已有工单的影响（更新 DEPENDENCY_MAP）
3. 新增表时标注对应的工单编号
