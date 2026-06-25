# Phase 2 Freeze Declaration

> **冻结日期**：2026-06-24
> **冻结执行人**：AI Agent（harness-meta 维护）
> **冻结范围**：harness-meta Phase 2 全部产物
> **解冻条件**：触发 Schema Change Policy 的 MAJOR 变更流程

---

## 1. 冻结声明

自本声明发布之时起，以下 Schema 进入 Frozen 状态：

### 1.1 Frozen Schema 清单

| Schema | 文件路径 | 版本 | 冻结前版本 | 冻结依据 |
|--------|----------|------|------------|----------|
| Context Contract | `templates/context-schema.yaml` | v1.0-frozen | v1.0 | Phase 1.5 验证通过 |
| Artifact Meta Schema | `templates/meta/artifact-meta-schema.yaml` | v1.0-frozen | v1.0-draft | Chain Review v2.0 通过（10/10） |
| Spec Schema | `templates/meta/spec-schema.yaml` | v1.0-frozen | v0.1-draft | Chain Review v2.0 通过（10/10） |
| Task Schema | `templates/meta/task-schema.yaml` | v1.0-frozen | v0.1-draft | Chain Review v2.0 通过（10/10，修复后） |
| Architecture Schema | `templates/meta/architecture-schema.yaml` | v1.0-frozen | v0.1-draft | Chain Review v2.0 通过（10/10，修复后） |

### 1.2 Frozen 配套文档

| 文档 | 文件路径 | 状态 |
|------|----------|------|
| Artifact Chain Review | `docs/governance/artifact-chain-review.md` | v2.0 已批准 |
| Schema Change Policy | `templates/meta/schema-change-policy.md` | v1.0 已发布 |

---

## 2. 冻结前质量保证

### 2.1 复审通过记录

**Artifact Chain Review v2.0（修复后复审）**：

| 维度 | 评分 | 评级 |
|------|------|------|
| Traceability 完整性 | 10/10 | ✅ 通过 |
| Artifact 一致性 | 9/10 | ✅ 通过 |
| DAG 完整性 | 9/10 | ✅ 通过 |
| Verify 可生成性 | 9/10 | ✅ 通过 |
| **总分** | **9.25/10** | **✅ 通过** |

### 2.2 关键修复项（v1.0 → v2.0）

| # | 问题 | 修复方案 | 状态 |
|---|------|----------|------|
| 1 | Task 与 Architecture 约束无强关联 | `architecture_rules` → `constraint_refs`（引用 CON ID） | ✅ 已修复 |
| 2 | Task 验证步骤与验收标准无关联 | `validation_steps` 增加 `acceptance_criteria_ids` | ✅ 已修复 |
| 3 | Architecture 约束可能孤立 | `constraints.related_requirements` → `required: true` | ✅ 已修复 |
| 4 | 引用无运行时验证机制 | 增加 Rules 6/7/8 引用完整性校验规则 | ✅ 已修复 |

---

## 3. Phase 2 目标达成情况

### 3.1 原定目标

> Phase 2 目标：建立 Artifact Contract 分层架构，使所有 Skill 输出符合统一 Schema，形成可追踪、可验证的产物链路。

### 3.2 达成情况

| 目标项 | 状态 |
|--------|------|
| Context Contract 标准化（项目环境层） | ✅ v1.0-frozen |
| Artifact Meta Schema（统一身份标识） | ✅ v1.0-frozen |
| Spec Schema（业务规格层） | ✅ v1.0-frozen |
| Task Schema（实现工单层） | ✅ v1.0-frozen |
| Architecture Schema（约束结构层） | ✅ v1.0-frozen |
| 完整追踪链路建立 | ✅ Chain Review 通过 |
| 引用完整性校验机制 | ✅ Rules 6/7/8 已发布 |
| Schema Change Policy 建立 | ✅ v1.0 已发布 |

**结论**：Phase 2 全部目标已达成。

---

## 4. Frozen Schema 的能力

冻结后，harness-meta 已具备以下能力：

### 4.1 身份标识能力

所有 Artifact 通过统一的 Meta Schema 描述：

- `artifact.id` 全局唯一
- `artifact.type` 限定类型（spec / task / architecture 等）
- `artifact.source` 记录生成 Skill
- `artifact.status` 跟踪生命周期

### 4.2 引用能力

跨 Artifact 引用通过结构化 ID 实现：

```
REQ-{domain}-{seq:03d}    # 需求
AC-{domain}-{seq:03d}     # 验收标准
CON-{domain}-{seq:03d}    # 架构约束
MOD-{domain}-{seq:03d}    # 模块
ADR-{seq:03d}             # 架构决策
```

### 4.3 追踪链路

```
Feature (project.yaml)
    ↓
Spec (requirements → scenarios → acceptance_criteria)
    ↓
Task (requirement_refs + constraint_refs + acceptance_criteria_ids)
    ↓
Architecture (constraints → modules → interfaces → decisions)
    ↓
[Verify Schema - Phase 2.5 待设计]
```

### 4.4 校验能力

- **ID 格式校验**：Rules 7 覆盖 17 种 ID 类型
- **引用目标存在性校验**：Rules 6 覆盖 10 种跨 Artifact 引用
- **校验执行时机**：Rules 8 覆盖生成时、评审时、执行时三个阶段

---

## 5. 冻结期间禁止行为

冻结期间，以下行为被禁止：

1. 直接修改 Frozen Schema 文件的字段定义
2. 在 Skill 中使用未注册的 `context.*` 变量
3. 使用非标准 ID 格式（如 `REQ-NTO-001` 错别字）
4. 绕过 Schema 校验机制
5. 在未升级版本号的情况下修改字段语义

如需变更，必须遵循 Schema Change Policy：

- PATCH：兼容性修复 → v1.0.x
- MINOR：新增可选字段 → v1.x.0
- MAJOR：破坏性变更 → v2.0.0（RFC）

---

## 6. 进入 Phase 2.5

Phase 2 冻结完成后，正式进入 **Phase 2.5 Verify Schema** 设计。

### 6.1 Verify Schema 的定位

Verify Schema 是整个 Artifact 链路的**最终消费者**，形成真正的闭环验证体系：

```
Requirement (Spec)
    ↓
Acceptance Criteria (Spec)
    ↓
Task (requirement_refs + acceptance_criteria_ids)
    ↓
Constraint (Architecture.constraint_refs)
    ↓
Validation (Task.validation_steps)
    ↓
Verify Report (Phase 2.5 新增)
```

### 6.2 Phase 2.5 范围

- 设计 Verify Schema v0.1-draft
- 定义验证报告结构（覆盖率、通过率、缺陷率）
- 验证 Verify Schema 与四层 Frozen Schema 的兼容性
- 升级 harness-verify、harness-runtime-verify、harness-review-loop 以消费 Verify Schema

---

## 7. 冻结声明有效性

本声明自 2026-06-24 起生效，有效期至 Phase 3 完成。

如发生以下情况，本声明自动失效：

1. Phase 3 进入执行（需要 Schema 重大调整）
2. 维护者社区通过新的 RFC 推翻本声明
3. 发现 Frozen Schema 存在严重设计缺陷（经架构委员会确认）

---

## 8. 签核

**冻结执行**：AI Agent（harness-meta 维护）
**审查依据**：Artifact Chain Review v2.0
**批准时间**：2026-06-24
**下一次审查**：Phase 3 启动前

---

> **Phase 2 正式冻结，进入 Phase 2.5 Verify Schema 设计阶段。**