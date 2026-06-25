# Phase 2.5 Freeze Declaration

> **冻结日期**：2026-06-24
> **冻结执行人**：AI Agent（harness-meta 维护）
> **冻结范围**：harness-meta Phase 2.5 全部产物（Verify Schema + 4 个 Consumer Skill）
> **解冻条件**：触发 Schema Change Policy 的 MAJOR 变更流程

---

## 1. 冻结声明

自本声明发布之时起，以下 Schema 与 Skill 进入 Frozen 状态：

### 1.1 Frozen Schema 清单

| Schema | 文件路径 | 版本 | 冻结前版本 | 冻结依据 |
|--------|----------|------|------------|----------|
| Verify Schema | `templates/meta/verify-schema.yaml` | v1.0-frozen | v0.2-draft | Chain Review + Consumer Review 双通过 |

### 1.2 Frozen Consumer Skill 清单

| Skill | 文件路径 | 角色 | 升级版本 |
|-------|----------|------|---------|
| harness-verify | `skills/harness-verify/SKILL.md` | 聚合消费者（V1-V6 规则执行） | v1.0（接入 Verify Schema） |
| harness-runtime-verify | `skills/harness-runtime-verify/SKILL.md` | 执行消费者（V6 实现） | v1.0（修复重复 + 接入 validation_status_map） |
| harness-review-loop | `skills/harness-review-loop/SKILL.md` | 约束消费者（V3 + severity_distribution） | v1.0（修复重复 + 接入 constraint_coverage） |
| harness-analyze | `skills/harness-analyze/SKILL.md` | 预检消费者（4 类 coverage + verify_output_mode） | v2.0（接入 4 类 coverage + 三模式输出） |

### 1.3 Frozen 配套文档

| 文档 | 文件路径 | 状态 |
|------|----------|------|
| Verify Consumer Review | `docs/governance/verify-consumer-review.md` | v2.5 通过（4/4 一致） |
| Schema Change Policy | `templates/meta/schema-change-policy.md` | v1.0（已扩展覆盖 Verify Schema） |

---

## 2. 冻结前质量保证

### 2.1 Chain Review 通过记录

**Artifact Chain Review v2.5（v0.2 修复后）**：

| 维度 | 评分 | 评级 |
|------|------|------|
| 与 Frozen Schema 兼容性 | 10/10 | ✅ 通过 |
| V1-V6 规则可生成性 | 9/10 | ✅ 通过 |
| 字段命名一致性 | 10/10 | ✅ 通过 |
| V6 status 字段解决方案 | 10/10 | ✅ 通过（引入 validation_status_map） |
| **总分** | **9.75/10** | **✅ 通过** |

### 2.2 Consumer Review 通过记录

**Verify Consumer Review v2.5（4/4 一致）**：

| Consumer Skill | 字段一致性 | 规则映射 | 字节状态 | 评分 |
|---------------|-----------|---------|---------|------|
| harness-verify | ✅ 100% | ✅ V1-V6 全覆盖 | ✅ 21449 字节干净 | 10/10 |
| harness-runtime-verify | ✅ 100% | ✅ V6 实现 | ✅ 18579 字节干净 | 10/10 |
| harness-review-loop | ✅ 100% | ✅ V3 实现 | ✅ 19213 字节干净 | 9.5/10 |
| harness-analyze | ✅ 100% | ✅ V1-V6 预检 | ✅ 18753 字节干净 | 9.5/10 |
| **总分** | **100%** | **完整** | **4 文件全干净** | **9.75/10** |

### 2.3 关键修复项（v0.2-draft → v1.0-frozen）

| # | 问题 | 修复方案 | 状态 |
|---|------|----------|------|
| 1 | V6 status 字段引用问题 | 引入 `context.validation_status_map`（runtime 状态在 Verify Report 维护） | ✅ 已修复 |
| 2 | V2 伪代码使用 `spec.scenarios[]`（错误路径） | 改为 `spec.acceptance_criteria[].id`（全局 AC 路径） | ✅ 已修复 |
| 3 | 4 个 Consumer 字段命名不一致 | 统一为 `requirement_coverage` / `acceptance_coverage` / `constraint_coverage` / `validation_coverage` | ✅ 已修复 |
| 4 | Consumer 输出模式不明确 | 引入 `verify_output_mode`（dual / schema-only / markdown-only） | ✅ 已修复 |
| 5 | 严重度词汇表混淆 | 采用"统一字段名 + 分维度词汇表"策略 | ✅ 已文档化 |
| 6 | harness-runtime-verify 重复内容 | 修复"检查清单"和"修复后验证"两处重复 | ✅ 已修复 |
| 7 | harness-review-loop 重复内容 | 修复"轮次管理"和"输出"两处重复 | ✅ 已修复 |
| 8 | harness-analyze UTF-8 字节损坏（460 个问题字符） | 从 git HEAD v1.0 恢复 → 增量重建 v2.0 完整内容 | ✅ 已修复 |

---

## 3. Phase 2.5 目标达成情况

### 3.1 原定目标

> Phase 2.5 目标：设计 Verify Schema（链路最终消费者），形成闭环验证体系，覆盖 Requirement → AC → Task → Constraint → Validation → Verify Report 全链路。

### 3.2 达成情况

| 目标项 | 状态 |
|--------|------|
| Verify Schema 设计（4 类 coverage + V1-V6 规则） | ✅ v0.2-draft |
| 与 4 层 Frozen Schema 兼容性验证 | ✅ Chain Review 通过 |
| harness-verify 接入 Verify Schema | ✅ v1.0 |
| harness-runtime-verify 接入 Verify Schema | ✅ v1.0 |
| harness-review-loop 接入 Verify Schema | ✅ v1.0 |
| harness-analyze 接入 Verify Schema | ✅ v2.0 |
| Consumer 字段一致性 | ✅ 4/4 一致 |
| 字节状态干净（4 个文件） | ✅ 全部干净 |
| 冻结字段词汇表权威定义 | ✅ verify-schema.yaml §4 |

**结论**：Phase 2.5 全部目标已达成。

---

## 4. Frozen 字段命名与枚举词汇表

### 4.1 冻结字段命名（6 项）

```yaml
coverage:
  requirement_coverage      # 需求覆盖率
  acceptance_coverage       # 验收标准覆盖率
  constraint_coverage       # 约束引用覆盖率
  validation_coverage       # 验证步骤执行率（预检版）
context:
  validation_status_map     # validation_step 执行状态映射
verify_output_mode:         # harness-analyze 输出模式参数
  - dual | schema-only | markdown-only
```

### 4.2 冻结枚举值（3 套）

```yaml
# 架构约束严重度（Architecture Constraint）
severity_distribution:
  - must       # 必须（硬约束，违反 = 阻塞）
  - should     # 推荐（软约束，违反 = 警告）
  - may        # 可选（信息性，违反 = 提示）

# 运行时验证状态（Runtime Verify）
validation_status:
  - passed     # 验证通过
  - failed     # 验证失败
  - skipped    # 跳过（前置条件未满足）
  - error      # 执行异常（工具故障/超时/配置错误）

# 问题严重度（Issue Severity）
issue_severity:
  - block      # 阻塞（必须修复）
  - warning    # 警告（建议修复）
  - info       # 信息（仅提示）
```

### 4.3 分维度词汇表策略

> **冻结决策**：采用"统一字段名 + 分维度词汇表"策略。**不强制统一枚举词汇表**。

**理由**：

| 维度 | 词汇表 | 语义重点 |
|------|--------|---------|
| Architecture Constraint | `must / should / may` | 表达约束的强制级别 |
| Runtime Verify | `passed / failed / skipped / error` | 表达执行结果状态 |
| Issue Severity | `block / warning / info` | 表达问题对流程的影响 |

强制统一将损失语义表达能力。例如：

- 运行时验证的 `passed` 无法用 `must` 表达（"必须"不是状态）
- 问题严重度的 `block` 无法用 `must` 表达（"必须"是要求，不是状态）

**原则**：

- ✅ 统一字段名（如 `severity` 字段名统一）
- ✅ 统一枚举定义位置（`verify-schema.yaml` §4 为权威）
- ✅ 允许不同维度使用不同词汇表

---

## 5. Frozen Schema 与 Skill 的能力

冻结后，harness-meta 在 Phase 2.5 增加了以下能力：

### 5.1 闭环验证能力

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

### 5.2 覆盖率计算能力

| 维度 | 计算公式 | 输出字段 |
|------|---------|---------|
| Requirement | `covered_requirements / total_requirements` | `coverage.requirement_coverage.coverage_rate` |
| Acceptance | `covered_criteria / total_criteria` | `coverage.acceptance_coverage.coverage_rate` |
| Constraint | `referenced_constraints / total_constraints` | `coverage.constraint_coverage.coverage_rate` |
| Validation | `defined_validations / total_validations`（预检）<br>`passed_validations / total_validations`（执行） | `coverage.validation_coverage.coverage_rate` |

### 5.3 V1-V6 规则引擎

| 规则 ID | 名称 | 输入 | 输出 |
|--------|------|------|------|
| V1 | requirement_covered | spec.requirements[].id + task.requirement_refs | coverage.requirement_coverage |
| V2 | acceptance_covered | spec.acceptance_criteria[].id + validation_steps.acceptance_criteria_ids | coverage.acceptance_coverage |
| V3 | constraint_referenced | architecture.constraints[].id + task.constraints.constraint_refs | coverage.constraint_coverage |
| V4 | reference_valid | 所有引用字段 | checks[].status |
| V5 | dod_satisfied | task.definition_of_done.criteria[].checked | failures[].category |
| V6 | validation_passed | validation_steps[].id + validation_status_map | coverage.validation_coverage |

### 5.4 多模式输出能力

`harness-analyze` 通过 `verify_output_mode` 参数支持 3 种输出：

| 模式 | 输出 |
|------|------|
| `dual`（默认） | YAML Schema + Markdown 报告 |
| `schema-only` | 仅 YAML Schema |
| `markdown-only` | 仅 Markdown 报告 |

---

## 6. 冻结期间禁止行为

冻结期间，以下行为被禁止：

1. 直接修改 Verify Schema 字段定义（必须走 Schema Change Policy）
2. 在 Consumer Skill 中使用未注册的 coverage 字段名
3. 在 `validation_status_map.value` 中使用 passed/failed/skipped/error 之外的取值
4. 在 `verify_output_mode` 中使用 dual/schema-only/markdown-only 之外的取值
5. 绕过 V1-V6 规则自行实现验证逻辑
6. 在未升级版本号的情况下修改字段语义

如需变更，必须遵循 Schema Change Policy：

- PATCH：兼容性修复 → v1.0.x
- MINOR：新增可选字段 → v1.x.0
- MAJOR：破坏性变更 → v2.0.0（RFC）

---

## 7. 进入 Phase 3

Phase 2.5 冻结完成后，正式进入 **Phase 3 Context Engine**。

### 7.1 Phase 3 目标

> **核心目标**：将 harness-meta 的能力从"协议层"扩展到"运行时能力层"，使验证、上下文打包、能力发现等可以自动化执行。

### 7.2 Phase 3 范围（预告）

- **Context Engine**：自动化上下文打包、跨 Skill 数据流
- **Verify Runtime**：V6 规则的自动化执行（不再依赖人工运行 lint/test/build）
- **Capability Discovery**：Skill 能力自动发现与组合
- **Multi-Agent 协作**：基于 Phase 2.5 Agent 体系扩展

### 7.3 Phase 3 与 Frozen Schema 的关系

Phase 3 是**运行时能力建设**，不修改任何 Frozen Schema：

- ✅ Verify Schema v1.0-frozen 保持稳定
- ✅ Context Contract v1.0-frozen 保持稳定
- ✅ Artifact Meta / Spec / Task / Architecture Schema 保持稳定
- 🆕 新增 Runtime Layer（不进入 Schema 冻结范围）

---

## 8. 冻结声明有效性

本声明自 2026-06-24 起生效，有效期至 Phase 3 完成。

如发生以下情况，本声明自动失效：

1. Phase 3 进入执行（需要 Schema 重大调整）
2. 维护者社区通过新的 RFC 推翻本声明
3. 发现 Frozen Schema 存在严重设计缺陷（经架构委员会确认）

---

## 9. 签核

**冻结执行**：AI Agent（harness-meta 维护）
**审查依据**：Artifact Chain Review v2.5 + Verify Consumer Review v2.5
**批准时间**：2026-06-24
**下一次审查**：Phase 3 启动前

---

> **Phase 2.5 正式冻结，进入 Phase 3 Context Engine 建设阶段。**
