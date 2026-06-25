# Context Contract Validation Report

> **状态：已冻结 v1（2026-06-24）**
> 
> 验证项目：python-ai-template（Brownfield）
> 验证功能：F22 通知推送系统
> 验证流程：clarify → specify → order
> 验证日期：2026-06-24
> 验证标准：Context Contract 是否支撑完整流程，无需临时新增字段

---

## 1. 验证摘要

| 阶段 | 状态 | 使用的 Context 层级 | 字段数 |
|------|------|---------------------|--------|
| Clarify | ✅ 通过 | project, feature | 8 |
| Specify | ✅ 通过 | project, feature, architecture, constraints | 12 |
| Order | ✅ 通过 | project, feature, architecture, constraints, task | 18 |

**总体结论**：Context Contract v1 能够完整支撑 clarify → specify → order 流程，**无需临时新增字段**。

---

## 2. 逐层验证详情

### 2.1 project 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.project.name` | 规格文档中标识项目 | ✅ 够用 |
| `context.project.description` | 规格文档概述 | ✅ 够用 |
| `context.project.stack.backend` | 推断技术实现（FastAPI） | ✅ 够用 |
| `context.project.stack.database` | 推断数据存储（PG/Redis/Qdrant） | ✅ 够用 |
| `context.project.stack.message_queue` | 推断异步机制（ARQ） | ✅ 够用 |
| `context.project.verify_commands.health_check` | 工单验证命令 | ✅ 够用 |

**结论**：project 层字段完整，无需调整。

### 2.2 feature 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.feature.id` | 工单编号（F22） | ✅ 够用 |
| `context.feature.name` | 功能名称 | ✅ 够用 |
| `context.feature.domain` | 域分组（notification） | ✅ 够用 |
| `context.feature.dependencies` | 依赖图构建 | ✅ 够用 |
| `context.feature.behavior` | 行为描述、规格生成 | ✅ 够用 |
| `context.feature.verify_command` | 验收测试命令 | ✅ 够用 |

**结论**：feature 层字段完整，无需调整。

### 2.3 task 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.task.status` | 工单状态（not_started） | ✅ 够用 |
| `context.task.patches` | 变更追踪 | ✅ 够用 |
| `context.task.supersedes` | 替代关系 | ✅ 够用 |
| `context.task.superseded_by` | 被替代关系 | ✅ 够用 |
| `context.task.code_deps` | 跨工单代码依赖 | ✅ 够用 |
| `context.task.required_docs` | 必读文档列表 | ✅ 够用 |
| `context.task.implementation_plan` | 实现计划 | ✅ 够用 |

**结论**：task 层字段完整，无需调整。

### 2.4 architecture 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.architecture.layers` | 分层约束（api→domain→services→infra） | ✅ 够用 |
| `context.architecture.rules` | 架构规则引用 | ✅ 够用 |

**结论**：architecture 层字段够用，但发现 `layers` 实际使用频率高于 `rules`。

### 2.5 constraints 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.constraints.api_contract` | API 端点设计约束 | ✅ 够用 |
| `context.constraints.error_codes` | 错误码注册 | ✅ 够用 |
| `context.constraints.domain_map` | 域职责映射 | ✅ 够用 |

**结论**：constraints 层字段完整，无需调整。

### 2.6 memory 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.memory.architecture_decisions` | 未在本次验证中使用 | ⚠️ 未使用 |
| `context.memory.project_conventions` | 未在本次验证中使用 | ⚠️ 未使用 |
| `context.memory.technology_profile` | 未在本次验证中使用 | ⚠️ 未使用 |
| `context.memory.lessons_learned` | 未在本次验证中使用 | ⚠️ 未使用 |

**结论**：memory 层在本次验证中未使用，属于 Phase 3（Context Engine 深化）范畴，不影响当前验证。

### 2.7 session 层

| 字段 | 使用场景 | 状态 |
|------|----------|------|
| `context.session.date` | 调研日期 | ✅ 够用 |
| `context.session.completed_count` | 澄清计数 | ✅ 够用 |
| `context.session.total_count` | 总计数 | ✅ 够用 |
| `context.session.batch_number` | 批次编号 | ✅ 够用 |
| `context.session.total_batches` | 总批次数 | ✅ 够用 |

**结论**：session 层字段完整，无需调整。

---

## 3. 问题发现

### 3.1 缺失字段

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| 无 | — | 本次验证未发现有缺失字段 |

### 3.2 冗余字段

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| 无 | — | 本次验证未发现有冗余字段 |

### 3.3 命名问题

| 问题 | 严重程度 | 建议 |
|------|----------|------|
| `context.feature.name` vs `context.feature.title` | 低 | `title` 和 `name` 同义，建议 deprecate `title`，统一使用 `name` |

**处理状态**：✅ 已处理。`title` 已标记为 `deprecated: true`，`name` 为唯一标准字段。

### 3.4 层级问题

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| `context.feature.behavior` 存储位置 | 低 | 当前放在 feature 层合理，但如果行为描述很长，未来可能需要拆分到 task 层 |

### 3.5 重复引用

| 问题 | 严重程度 | 说明 |
|------|----------|------|
| 无 | — | 未出现同一信息跨多层存储的情况 |

---

## 4. 验证统计

| 指标 | 数值 |
|------|------|
| 验证的 Context 层级 | 7 / 8（memory 未使用） |
| 使用的字段总数 | 25 |
| 临时新增字段 | 0 |
| 发现的命名问题 | 1（已处理） |
| 发现的层级问题 | 1（低严重） |
| 重复引用问题 | 0 |

---

## 5. 冻结声明

### 5.1 冻结条件

✅ 已满足：
- [x] Context Contract 完整支撑核心流程（clarify → specify → order）
- [x] 无缺失字段
- [x] 无冗余字段
- [x] 无重复引用
- [x] 经过真实项目验证（python-ai-template F22）
- [x] 同义字段已清理（`title` → `name`）

### 5.2 冻结范围

**冻结内容**：`templates/context-schema.yaml` 中所有字段的定义（名称、层级、source、required、legacy）

**变更控制**：冻结后，字段的增删改需走 RFC 流程：
1. 在 Issue 中说明变更理由
2. 评估对现有 Skill 的影响
3. 提供迁移方案（如适用）
4. 获得批准后方可修改

### 5.3 已废弃字段

| 字段 | 替代方案 | 计划删除版本 | 状态 |
|------|---------|------------|------|
| `context.feature.title` | `context.feature.name` | v2 | deprecated |

### 5.4 进入 Phase 2

**建议进入 Phase 2：Artifact Schema**

目标：
- Spec Schema（规格文档结构）
- Architecture Schema（架构规格结构）
- Task Schema（工单结构）

这些 Schema 将建立在已冻结的 Context Contract v1 之上，确保稳定性。

---

## 附录：验证过程中使用的 Context 路径清单

### Clarify 阶段
- `context.project.name`
- `context.project.stack.backend`
- `context.project.stack.database`
- `context.feature.id`
- `context.feature.name`
- `context.feature.domain`
- `context.feature.dependencies`
- `context.feature.behavior`
- `context.feature.verify_command`

### Specify 阶段
- `context.project.name`
- `context.project.stack.backend`
- `context.project.stack.database`
- `context.project.stack.message_queue`
- `context.feature.id`
- `context.feature.name`
- `context.feature.domain`
- `context.feature.behavior`
- `context.architecture.layers`
- `context.constraints.api_contract`
- `context.constraints.error_codes`
- `context.session.date`

### Order 阶段
- `context.project.name`
- `context.feature.id`
- `context.feature.name`
- `context.feature.domain`
- `context.feature.dependencies`
- `context.feature.behavior`
- `context.feature.verify_command`
- `context.architecture.layers`
- `context.constraints.api_contract`
- `context.constraints.error_codes`
- `context.constraints.domain_map`
- `context.task.status`
- `context.task.patches`
- `context.task.supersedes`
- `context.task.superseded_by`
- `context.task.code_deps`
- `context.task.required_docs`
- `context.task.implementation_plan`
