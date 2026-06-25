# Verify Schema Consumer Review

> **审查日期**：2026-06-24
> **审查阶段**：Phase 2.5.8.5
> **审查对象**：4 个 Verify Schema 消费者 Skill
> **审查结论**：✅ **通过**（4/4 一致）
> **下一步**：进入 Phase 2.5.9（Freeze Verify Schema v1.0）

---

## 审查范围

本次审查覆盖 4 个直接消费 Verify Schema v0.2-draft 的 Skill：

| # | Skill | 角色 | 核心职责 |
|---|-------|------|---------|
| 1 | harness-verify | **聚合消费者** | 4 类 coverage 聚合 + V1-V6 规则执行 + checks/failures/recommendations 生成 |
| 2 | harness-runtime-verify | **执行消费者** | validation_steps 执行 + validation_status_map 填充 + V6 规则实现 |
| 3 | harness-review-loop | **约束消费者** | 架构约束引用追踪 + constraint_coverage 计算（V3）+ issue 严重度 → status 映射 |
| 4 | harness-analyze | **预检消费者** | 工单生成后审计 + 4 类 coverage 预检 + 6 维度一致性检测 |

---

## 字节状态检查

通过 PowerShell 脚本读取每个文件的 UTF-8 字节流，识别所有非中文字符的 Unicode 码点。

| 文件 | 总字节 | 有效中文 | 非 CN 字符 | 非 CN 类型 | 结论 |
|------|--------|---------|-----------|-----------|------|
| harness-verify/SKILL.md | 21449 | 1910 | 27 | 全部合法符号（→、—、⚠️、✅） | ✅ 干净 |
| harness-runtime-verify/SKILL.md | 18579 | 2021 | 18 | 全部合法符号（—、→、⚠️、✅、❌） | ✅ 干净 |
| harness-review-loop/SKILL.md | 19213 | 2175 | 23 | 全部合法符号（—、∈、→、❌、⚠️、✅） | ✅ 干净 |
| harness-analyze/SKILL.md | 18753 | 2171 | 18 | 全部合法符号（→、—、∈、⚠️、✅） | ✅ 干净 |

**修复记录**：
- harness-runtime-verify：v2.0 初版含重复内容，已清理（624 行）
- harness-review-loop：v2.0 初版含重复内容，已清理（596 行）
- harness-analyze：v2.0 文件含 460 个非预期 Unicode 字符（UTF-8 字节损坏），已通过 `git checkout HEAD` 恢复 v1.0 后增量重建（529 行）

---

## 一致性检查

### 1. front matter 字段命名

| 文件 | `name` | `description` 关键词 |
|------|--------|---------------------|
| harness-verify | `harness-verify` | Verify Schema v0.2-draft、verify_output_mode |
| harness-runtime-verify | `harness-runtime-verify` | validation_status_map、verify_output_mode |
| harness-review-loop | `harness-review-loop` | constraint_coverage、validation_status_map、verify_output_mode |
| harness-analyze | `harness-analyze` | 4 类 coverage（requirement/acceptance/constraint/validation）、verify_output_mode |

✅ **全部一致**：均引用 Verify Schema v0.2-draft，均提及 `verify_output_mode` 参数。

---

### 2. `verify_output_mode` 参数定义

| 文件 | enum | default | 传递方式 |
|------|------|---------|---------|
| harness-verify | dual / schema-only / markdown-only | dual | 命令行 / 环境变量 / 默认 |
| harness-runtime-verify | dual / schema-only / markdown-only | dual | 命令行 / 环境变量 / harness-verify 自动 schema-only |
| harness-review-loop | dual / schema-only / markdown-only | dual | 命令行 / 环境变量 / harness-verify 自动 schema-only |
| harness-analyze | dual / schema-only / markdown-only | dual | 命令行 / 环境变量 |

✅ **全部一致**：相同的 3 个枚举值，相同的默认值。

---

### 3. 4 类 coverage 字段命名

| 字段 | verify | runtime-verify | review-loop | analyze |
|------|--------|----------------|-------------|---------|
| `coverage.requirement_coverage` | ✓（V1） | — | — | ✓（V1） |
| `coverage.acceptance_coverage` | ✓（V2） | — | — | ✓（V2） |
| `coverage.constraint_coverage` | ✓（V3） | — | ✓（V3） | ✓（V3） |
| `coverage.validation_coverage` | ✓（V6） | ✓（V6） | — | ✓（V6 预检版） |

✅ **命名完全一致**：
- `total_*` / `covered_*` / `coverage_rate` 命名一致
- `uncovered[]`（requirement/acceptance）vs `unreferenced[]`（constraint）vs `pending[]`（validation 预检版）语义清晰区分

---

### 4. `validation_status_map` 状态值

| 文件 | 状态值集合 |
|------|----------|
| harness-runtime-verify | passed / failed / skipped / error（4 种） |
| harness-review-loop | passed / failed（基于 issue 严重度 high/medium → failed，low → passed） |
| harness-verify | 消费上述两者输出 |

✅ **状态值闭合**：4 种状态值（passed/failed/skipped/error）覆盖了所有执行场景，consumer 之间无歧义。

---

### 5. 严重度词汇表

| 文件 | 严重度词汇 | 维度 |
|------|-----------|------|
| harness-analyze | CRITICAL / HIGH / MEDIUM / LOW（4 级） | 规格层审计（工单生成前） |
| harness-verify | CRITICAL / WARNING / SUGGESTION（3 级） | 实现层验证（代码完成后） |
| harness-review-loop | high / medium / low（issue 严重度）+ must / should / may（constraint 严重度） | 代码审查（实现中） |
| harness-runtime-verify | passed / failed / skipped / error（执行状态） | 运行时验证（执行后） |

✅ **设计合理**：不同 Skill 在不同维度使用不同严重度词汇表，避免"CRITICAL"语义在不同上下文冲突：

| 词汇 | 用途 | 触发阶段 |
|------|------|---------|
| CRITICAL | 阻塞执行/验证，必须先修 | analyze + verify |
| HIGH / WARNING | 重要问题，强烈建议修复 | analyze + verify |
| MEDIUM / SUGGESTION | 中风险/可选改进 | analyze + verify |
| LOW | 风格/措辞 | analyze |
| must / should / may | 架构约束严重度 | review-loop + analyze |
| high / medium / low | 审查问题严重度 | review-loop |
| passed / failed / skipped / error | 验证步骤执行状态 | runtime-verify |

---

### 6. 6 个规则（V1-V6）映射

| 规则 ID | 名称 | verify | runtime-verify | review-loop | analyze |
|---------|------|--------|----------------|-------------|---------|
| V1 | requirement_covered | ✓ | — | — | ✓（预检） |
| V2 | acceptance_covered | ✓ | — | — | ✓（预检） |
| V3 | constraint_referenced | ✓ | — | ✓ | ✓（预检） |
| V4 | reference_valid | ✓ | — | — | — |
| V5 | dod_satisfied | ✓ | ✓ | — | — |
| V6 | validation_passed | ✓ | ✓ | — | ✓（预检：步骤定义覆盖率） |

✅ **规则映射完整**：
- V1/V2/V3 在 verify 和 analyze 中算法完全一致（同一公式）
- V6 在 verify（消费）、runtime-verify（执行）、analyze（预检）形成链路
- V4 仅 verify 执行（消费所有引用字段）
- V5 在 verify 和 runtime-verify 中执行

---

### 7. 与 Verify Schema 字段映射表

| 文件 | "与 Verify Schema 字段映射表"章节 |
|------|----------------------------------|
| harness-verify | ✓（覆盖 target.* / summary.* / coverage.* / checks.* / failures.* / recommendations.* / context.* / meta_evaluation.*） |
| harness-runtime-verify | ✓（覆盖 coverage.validation_coverage / context.validation_status_map / context.environment.*） |
| harness-review-loop | ✓（覆盖 coverage.constraint_coverage / context.validation_status_map / context.environment.*） |
| harness-analyze | ✓（覆盖 coverage.* 4 类 / context.environment.* / meta_evaluation.*） |

✅ **全部包含**：每个 consumer 都明确列出与 Verify Schema 的字段对应关系。

---

### 8. 修复轮次

| 文件 | 最大轮次 | 终止条件 |
|------|---------|---------|
| harness-runtime-verify | 3 轮 | 全部 passed / 达到上限仍失败 |
| harness-review-loop | 3 轮 | passed / 达到上限仍未通过 |

✅ **轮次一致**：均为 3 轮，且终止条件明确。

---

### 9. meta_evaluation 字段

| 文件 | schema_compliance | reference_integrity | verify_confidence |
|------|------------------|---------------------|-------------------|
| harness-verify | ✓ | ✓ | ✓ |
| harness-runtime-verify | ✓ | ✓ | ✓ |
| harness-review-loop | ✓ | ✓ | ✓ |
| harness-analyze | ✓ | ✓ | ✓ |

✅ **3 个评估字段完全一致**。

---

### 10. 步骤编号风格

| 文件 | 步骤范围 | 风格 |
|------|---------|------|
| harness-verify | 1-9（+ 3.5 选择 Agent） | 顺序编号 |
| harness-runtime-verify | 1-12 | 顺序编号 |
| harness-review-loop | 1-10 | 顺序编号 |
| harness-analyze | 0-6（0 = 前置检查） | 前置检查 + 顺序编号 |

✅ **风格合理**：analyze 因为有"前置检查"（确认工单完整性）使用 0 编号，其他 3 个不需要前置检查，从 1 开始。差异可接受。

---

## 关键设计观察

### 1. analyze vs verify 的 validation_coverage 语义区分

analyze 阶段（工单生成后、执行前）的 `validation_coverage` 是**预检版**（步骤定义覆盖率），verify 阶段（代码完成后）的 `validation_coverage` 是**执行版**（validation_status_map 通过率）。

**完整链路**：
```
定义（analyze）：validation_steps 是否定义 command
       ↓
执行（runtime-verify）：exit_code → passed/failed
       ↓
验证（verify）：聚合所有 validation_status_map → coverage_rate
```

✅ 4 个 Skill 形成闭环，preflight 与 execution 覆盖度可对比，发现"定义但未执行"或"执行但未定义"的异常情况。

---

### 2. constraint_coverage 的 severity_distribution

`coverage.constraint_coverage.severity_distribution` 字段由 review-loop 提出（must/should/may），被 analyze 复用，verify 通过 V3 规则间接消费。

✅ 该字段在两个 consumer（review-loop + analyze）中使用方式一致，可作为 Phase 2.5.9 冻结候选字段。

---

### 3. harness-verify 的 4 类 coverage 聚合

harness-verify 是**唯一聚合所有 4 类 coverage** 的 Skill：
- requirement_coverage：自行计算（V1）
- acceptance_coverage：自行计算（V2）
- constraint_coverage：自行计算（V3）+ review-loop 提供数据
- validation_coverage：依赖 runtime-verify 填充的 validation_status_map（V6）

✅ 设计合理：verify 是唯一报告生成点，其他 3 个 consumer 是数据提供者。

---

## 总体结论

### 一致性评分：9.5/10

| 维度 | 评分 | 说明 |
|------|------|------|
| 字段命名一致性 | 10/10 | 4 类 coverage、verify_output_mode、validation_status_map 全部对齐 |
| 规则映射完整性 | 10/10 | V1-V6 在合适的 consumer 中实现，预检版与执行版语义清晰 |
| 参数一致性 | 10/10 | verify_output_mode 3 个枚举值在 4 个文件中完全一致 |
| 严重度词汇表 | 9/10 | 不同维度使用不同词汇表（合理设计），但需在文档中明确映射关系 |
| 字节状态 | 10/10 | 4 个文件全部干净（仅合法符号） |
| 与 Verify Schema 字段映射 | 10/10 | 每个 consumer 都有"与 Verify Schema 字段映射表"章节 |
| 修复轮次 | 10/10 | runtime-verify + review-loop 均为 3 轮 |
| meta_evaluation | 10/10 | 3 个评估字段（schema_compliance / reference_integrity / verify_confidence）一致 |

### 发现的问题（已修复）

1. **harness-runtime-verify 重复内容**：v2.0 初版含重复段落，已清理 → 624 行 ✅
2. **harness-review-loop 重复内容**：v2.0 初版含重复段落，已清理 → 596 行 ✅
3. **harness-analyze UTF-8 字节损坏**：v2.0 文件含 460 个非预期 Unicode 字符，已通过 git HEAD 恢复 + 增量重建 → 529 行 ✅

### 发现的问题（设计层面，需 Phase 2.5.9 决策）

1. **严重度词汇表分散**：analyze 用 CRITICAL/HIGH/MEDIUM/LOW，verify 用 CRITICAL/WARNING/SUGGESTION。两者交叉场景（如"CRITICAL 重复"）的语义由调用方解读，建议 Phase 2.5.9 在 Verify Schema 中明确 `severity` 字段的可选值集合。
2. **constraint severity（must/should/may）vs issue severity（high/medium/low）**：两者不同维度（约束 vs 问题），建议在 Verify Schema 中作为独立字段，Phase 2.5.9 冻结时明确。

---

## Phase 2.5.9 冻结建议

基于本次 Consumer Review，建议 Phase 2.5.9（Freeze Verify Schema v1.0）冻结以下字段为**必填**：

```yaml
verify_schema_v1.0_frozen:
  # === 必填字段（4 类 coverage）===
  coverage:
    requirement_coverage:    # V1
      total_requirements: int
      covered_requirements: int
      coverage_rate: float [0, 1]
      uncovered: string[]
    acceptance_coverage:     # V2
      total_criteria: int
      covered_criteria: int
      coverage_rate: float [0, 1]
      uncovered: string[]
    constraint_coverage:     # V3
      total_constraints: int
      referenced_constraints: int
      coverage_rate: float [0, 1]
      unreferenced: string[]
      severity_distribution:    # 可选，但推荐
        must: { total: int, referenced: int, unreferenced: int }
        should: { total: int, referenced: int, unreferenced: int }
    validation_coverage:     # V6
      total_validations: int
      passed_validations: int   # execution 版（verify/runtime-verify）
      # 或 defined_validations: int  # preflight 版（analyze）
      coverage_rate: float [0, 1]

  # === 必填字段（context）===
  context:
    validation_status_map:
      type: object
      # key: step_id, value: passed | failed | skipped | error
    environment:
      runner: enum[harness-verify, harness-runtime-verify, harness-review-loop, harness-analyze]
      verify_output_mode: enum[dual, schema-only, markdown-only]

  # === 必填字段（meta_evaluation）===
  meta_evaluation:
    schema_compliance: bool
    reference_integrity: bool
    verify_confidence: float [0, 1]
```

**冻结建议**：
- ✅ 4 类 coverage 字段命名冻结为 v1.0
- ✅ validation_status_map 4 种状态值（passed/failed/skipped/error）冻结
- ✅ verify_output_mode 3 个枚举值冻结
- ⚠️ severity_distribution 字段建议纳入冻结（must/should/may 命名稳定）
- ⚠️ 严重度词汇表建议在 Phase 2.5.9 决策：是分维度（当前设计）还是统一词汇表

---

## 变更历史

- **v1.0**（2026-06-24，Phase 2.5.8.5）：首次 Consumer Review
  - 审查 4 个 Verify Schema 消费者（verify / runtime-verify / review-loop / analyze）
  - 修复 3 个文件问题（重复内容 ×2 + UTF-8 字节损坏 ×1）
  - 验证 4 个文件字节状态全部干净
  - 验证字段命名、规则映射、参数定义在 4 个文件中一致
  - 总体一致性评分 9.5/10
  - 给出 Phase 2.5.9 冻结建议