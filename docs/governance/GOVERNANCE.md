# Harness-Meta 治理信息

> 本文件承载 harness-meta 框架的 Schema 冻结状态、变更政策与阶段记录。
> 面向**框架维护者**，普通使用者无需阅读。

---

## 当前 Schema 冻结状态总览

| 协议 | 版本 | 状态 | 冻结日期 | 冻结依据 |
|------|------|------|---------|---------|
| **Context Contract** | v1.0-frozen | ✅ Stable | 2026-06-24 | clarify → specify → order 全流程验证通过 |
| **Artifact Meta Schema** | v1.0-frozen | ✅ Stable | 2026-06-24 | Artifact Chain Review v2.0 通过（9.25/10） |
| **Spec Schema** | v1.0-frozen | ✅ Stable | 2026-06-24 | 同上 |
| **Task Schema** | v1.0-frozen | ✅ Stable | 2026-06-24 | 同上 |
| **Architecture Schema** | v1.0-frozen | ✅ Stable | 2026-06-24 | 同上 |
| **Verify Schema** | v1.0-frozen | ✅ Stable | 2026-06-24 | Chain Review v2.5 + Consumer Review 双通过（9.75/10） |

### 四层 Schema 架构

```
Context Contract v1
    ↓ 提供项目环境
Artifact Meta Schema v1.0-frozen
    ↓ 统一身份标识 + 引用完整性校验
    ├── Spec Schema v1.0-frozen（业务规格：What）
    ├── Task Schema v1.0-frozen（实现工单：How）
    └── Architecture Schema v1.0-frozen（约束结构：Constraints）
```

### Frozen Schema 文件位置

```
templates/
├── context-schema.yaml                       # Context Contract v1.0-frozen
└── meta/
    ├── artifact-meta-schema.yaml             # Artifact Meta Schema v1.0-frozen
    ├── spec-schema.yaml                       # Spec Schema v1.0-frozen
    ├── task-schema.yaml                       # Task Schema v1.0-frozen
    ├── architecture-schema.yaml               # Architecture Schema v1.0-frozen
    ├── verify-schema.yaml                     # Verify Schema v1.0-frozen
    └── schema-change-policy.md                # Schema 变更政策
```

---

## Schema Change Policy

冻结后，任何 Schema 修改必须遵循 SemVer 规范：

| 类型 | 场景 | 版本号 | 审批 |
|------|------|--------|------|
| **PATCH** | 兼容性修复（注释、示例、拼写） | v1.0.x | 单人 review |
| **MINOR** | 新增可选字段 | v1.x.0 | 维护者 review |
| **MAJOR** | 删除字段、修改语义、修改 ID 格式 | vx.0.0 | RFC + 投票 |

详见 `templates/meta/schema-change-policy.md`。

---

## Artifact 追踪链路

```
Feature (project.yaml)
    ↓
Spec (requirements → scenarios → acceptance_criteria)
    ↓ requirement_refs + acceptance_criteria_ids
Task (implementation_steps → validation_steps → DoD)
    ↓ constraint_refs
Architecture (constraints → modules → interfaces → decisions)
    ↓
Verify Schema（链路最终消费者）
```

### 引用完整性规则

跨 Artifact 引用必须使用**结构化 ID**，禁止自由文本：

```yaml
# ❌ 错误：自由文本
architecture_rules:
  - "Service 层不得直接访问数据库"

# ✅ 正确：结构化 ID
constraints:
  constraint_refs:
    - "CON-NOT-001"
```

ID 格式：

| 类型 | 格式 | 示例 |
|------|------|------|
| Requirement | `REQ-{domain}-{seq:03d}` | `REQ-NOT-001` |
| Acceptance Criteria | `AC-{domain}-{seq:03d}` | `AC-NOT-001` |
| Constraint | `CON-{domain}-{seq:03d}` | `CON-NOT-001` |
| Module | `MOD-{domain}-{seq:03d}` | `MOD-NOT-001` |

详见 `templates/meta/artifact-meta-schema.yaml` Rules 6/7/8。

### Skill 与 Schema 的契约

所有 Skill 必须：

- 生成符合对应 Schema 的 Artifact（spec / task / architecture 等）
- 使用结构化 ID 引用其他 Artifact
- 在引用前验证目标存在性（Rules 8：评审时验证）
- 对 Frozen Schema 字段采用 forward compatibility（容忍未知字段）

---

## 闭环验证链路（Verify Schema）

```
Requirement (Spec)        → V1 requirement_covered
    ↓
Acceptance Criteria (Spec) → V2 acceptance_covered
    ↓
Task (requirement_refs + acceptance_criteria_ids)
    ↓
Constraint (Architecture.constraint_refs)      → V3 constraint_referenced
    ↓
Validation (Task.validation_steps + status_map) → V6 validation_passed
    ↓
Verify Report (4 类 coverage + checks + failures + recommendations)
```

### Consumer Skill（已接入 Verify Schema）

| Skill | 角色 | 输出 |
|-------|------|------|
| **harness-verify** | 聚合消费者（V1-V6 规则执行） | Verify Schema 格式 |
| **harness-runtime-verify** | 执行消费者（V6 status_map 填充） | Verify Schema 格式 |
| **harness-review-loop** | 约束消费者（V3 + severity_distribution） | Verify Schema 格式 |
| **harness-analyze** | 预检消费者（4 类 coverage + 3 模式输出） | 按 verify_output_mode |

### Verify Schema 冻结字段与词汇表

**冻结字段命名**（6 项）：

- `coverage.requirement_coverage`
- `coverage.acceptance_coverage`
- `coverage.constraint_coverage`
- `coverage.validation_coverage`
- `context.validation_status_map`
- `verify_output_mode`

**冻结枚举值**（3 套分维度词汇表）：

- 架构约束严重度：`must` / `should` / `may`
- 运行时验证状态：`passed` / `failed` / `skipped` / `error`
- 问题严重度：`block` / `warning` / `info`

详见 `templates/meta/verify-schema.yaml` §4 与 `docs/governance/phase2.5-freeze-declaration.md`。

---

## Context Contract 冻结记录

> **状态：v1 已冻结（2026-06-24）**
>
> 经过 clarify → specify → order 全流程验证，Context Contract v1 已达到冻结条件。
> 冻结后，字段变更需走 RFC 流程。

**已废弃字段**：

| 字段 | 替代方案 | 计划删除版本 |
|------|---------|------------|
| `context.feature.title` | `context.feature.name` | v2 |

---

## 阶段冻结记录

### Phase 2 冻结（2026-06-24）

- **冻结依据**：Artifact Chain Review v2.0 通过（总分 9.25/10）
- **冻结范围**：Context Contract + Artifact Meta Schema + Spec/Task/Architecture Schema
- **详细记录**：`docs/governance/phase2-freeze-declaration.md`
- **链路审查**：`docs/governance/artifact-chain-review.md`

### Phase 2.5 冻结（2026-06-24）

- **冻结依据**：Chain Review v2.5 + Consumer Review v2.5 双通过（总分 9.75/10）
- **新增协议**：Verify Schema v1.0-frozen（链路最终消费者）
- **详细记录**：`docs/governance/phase2.5-freeze-declaration.md`
- **链路审查**：`docs/governance/artifact-chain-review-v2.5.md`
- **消费者审查**：`docs/governance/verify-consumer-review.md`

### Harness Core v1.0 冻结

- **详细记录**：`docs/governance/harness-core-v1-freeze-declaration.md`

### Phase 3 Context Engine（设计阶段）

- **设计文档**：`docs/governance/phase3-context-engine.md`
- **状态**：Context Engine v2.0 已落地（P0 Builder / P1 Resolver / P2 Budget），AB Test 验证完成

---

## 过程审查文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| Artifact Chain Review v2.0 | `docs/governance/artifact-chain-review.md` | Phase 2 冻结链路审查 |
| Artifact Chain Review v2.5 | `docs/governance/artifact-chain-review-v2.5.md` | Phase 2.5 Verify Schema 兼容性审查 |
| Context Contract Validation Report | `docs/governance/context-contract-validation-report.md` | Context Contract v1 专项验证 |
| Verify Consumer Review | `docs/governance/verify-consumer-review.md` | Verify Schema 四消费者一致性审查（4/4 通过） |
