---
name: harness-verify
description: 链路验证。基于 Verify Schema v0.2-draft（待冻结为 v1.0），输出 Verify Report（覆盖度/检查项/失败分析/修复建议）。支持 Skill 参数控制输出格式：dual（默认）/ schema-only / markdown-only。
---

# harness-verify：链路验证（Verify Schema 消费者）

## 触发条件

harness-apply 完成后，用户要求验证实现时执行。

## 输入

- 变更名称（可选）
- `changes/{{change_name}}/`（完整变更文件夹）
- `verify_output_mode`（可选参数，控制输出格式）

## 输出

根据 `verify_output_mode` 参数：

| 输出模式 | 生成文件 | 适用场景 |
|---------|---------|---------|
| `dual`（默认） | `verify-report.md` + `verify-report.yaml` | 人类阅读 + 机器消费双轨 |
| `schema-only` | `verify-report.yaml` | CI / 自动消费 |
| `markdown-only` | `verify-report.md` | 向后兼容（v1 行为） |

`verify-report.yaml` 严格遵循 **Verify Schema v0.2-draft**（待冻结为 v1.0-frozen）。

---

## 参数控制

### `verify_output_mode`

```yaml
verify_output_mode:
  type: string
  enum: [dual, schema-only, markdown-only]
  default: dual
  description: |
    控制 Verify Report 的输出格式。
    - dual: 双轨输出（默认），同时生成 markdown 和 yaml
    - schema-only: 仅生成 yaml（机器消费）
    - markdown-only: 仅生成 markdown（人类阅读，向后兼容）
  example: dual
```

### 参数传递方式

支持以下三种方式（按优先级）：

1. **命令行参数**：`/harness-verify --mode=schema-only {{change_name}}`
2. **环境变量**：`HARNESS_VERIFY_OUTPUT_MODE=schema-only`
3. **Skill 默认值**：未指定时使用 `dual`

---

## 步骤

### 1. 选择变更

如果未指定，自动选择或提示用户选择（同 harness-apply）。

### 2. 读取变更上下文

读取变更文件夹中所有 artifacts：

**必读**：
- `delta-spec.md` → 提取 `requirements[]` / `scenarios[]` / `acceptance_criteria[]`
- `tasks.md` → 解析所有 Task Schema 字段：
  - `task.requirement_refs[].requirement_id`
  - `task.validation_steps[].id`
  - `task.validation_steps[].acceptance_criteria_ids[]`
  - `task.constraints.constraint_refs[]`
  - `task.definition_of_done.criteria[].checked`
- `design.md`（如存在）→ 提取技术决策

**Schema 必读**：
- 如任务已结构化为 Schema 格式（Task Schema v1.0-frozen），直接解析 YAML
- 如为旧 markdown checkbox 格式，启发式提取

### 3. 初始化验证报告

根据 `verify_output_mode` 选择输出格式，初始化 Verify Schema 骨架：

```yaml
verify_report:
  # === 继承自 Artifact Meta ===
  artifact:
    id: "{{change_name}}-verify-report-{{iteration}}"
    type: report
    title: "{{change_name}} 链路验证报告"
    domain: "{{domain}}"
    status: active
    version: "0.1.0"
    source:
      skill: harness-verify
      feature_id: "{{feature_id}}"
      created: "{{timestamp}}"
      updated: "{{timestamp}}"
    dependencies:
      - "{{spec_id}}"
      - "{{task_ids}}"
      - "{{architecture_id}}"
  
  target:
    feature_id: "{{feature_id}}"
    task_ids: []
    spec_id: "{{spec_id}}"
    architecture_id: "{{architecture_id}}"  # 可选
  
  iteration: 1
  
  summary:
    total_checks: 0
    passed: 0
    failed: 0
    warned: 0
    overall_status: passing
  
  coverage:
    requirement_coverage: { total_requirements: 0, covered_requirements: 0, coverage_rate: 0.0, uncovered: [] }
    acceptance_coverage:   { total_criteria: 0,   covered_criteria: 0,   coverage_rate: 0.0, uncovered: [] }
    constraint_coverage:   { total_constraints: 0, referenced_constraints: 0, coverage_rate: 0.0, unreferenced: [] }
    validation_coverage:   { total_validations: 0, passed_validations: 0, coverage_rate: 0.0 }
  
  checks: []
  failures: []
  recommendations: []
  
  context:
    environment:
      runner: harness-verify
      version: v1.0
      timestamp: "{{timestamp}}"
      verify_output_mode: "{{verify_output_mode}}"
    inputs: []
    validation_status_map: {}  # 由 harness-runtime-verify 填充
```

### 3.5 选择验证 Agent（如适用）

如果当前会话支持 Agent 模式（多 Agent 协作），将验证任务分配给对应 Agent：

| 验证类型 | 分配 Agent | 映射到 Verify Schema |
|----------|-----------|---------------------|
| 规格验证（V1/V2/V4） | `spec-validator` | `coverage.requirement_coverage` / `coverage.acceptance_coverage` / `checks[].reference_valid` |
| 代码审查（V3） | `code-reviewer` | `coverage.constraint_coverage` / `checks[].constraint_referenced` |
| 运行时验证（V6） | 调用 `harness-runtime-verify` | `coverage.validation_coverage` / `context.validation_status_map` |

**执行顺序**：
1. 先执行 `spec-validator`：验证规格覆盖和引用完整性（V1/V2/V4）
2. 再执行 `code-reviewer`：验证约束引用（V3）
3. 再执行 `harness-runtime-verify`：填充 `validation_status_map`（V6）
4. 接收所有结果，整合到 Verify Schema 报告

### 4. 验证完整性 → V1 规则

**任务完成情况**（保留原逻辑）：

- 解析 `tasks.md` 中的 checkbox
- 统计 `- [ ]`（未完成）vs `- [x]`（已完成）
- 每个未完成任务 → CRITICAL

**V1 规则：requirement_covered**

```yaml
rule_id: V1
input:
  spec.requirements[].id
  all_tasks[*].requirement_refs[].requirement_id
algorithm: |
  for each req_id in spec.requirements:
    if req_id not in any task.requirement_refs:
      fail (missing_task)
output: coverage.requirement_coverage
```

输出字段：

```yaml
coverage:
  requirement_coverage:
    total_requirements: 5
    covered_requirements: 5
    coverage_rate: 1.0
    uncovered: []

checks:
  - check_id: "VRF-{{verify_id}}-001"
    type: requirement_covered
    target_id: "REQ-NOT-001"
    status: pass
    message: "需求 REQ-NOT-001 被 F22-order-001 引用"
    evidence:
      artifact_id: "F22-order-001"
      field_path: "requirement_refs[0].requirement_id"
```

### 5. 验证正确性 → V2/V5 规则

**需求实现映射**（保留原逻辑）：

- 对每个需求，搜索代码中的实现证据
- 实现偏离规格意图 → WARNING

**场景覆盖**（保留原逻辑）：

- 对每个场景（前置/当/则），检查代码是否处理
- 检查是否有对应测试
- 未覆盖的场景 → WARNING

**V2 规则：acceptance_covered**

```yaml
rule_id: V2
input:
  spec.acceptance_criteria[].id              # 全局 AC（Spec Schema 全局段）
  # 也可使用嵌套 AC：spec.requirements[].scenarios[].acceptance_criteria[]
  all_tasks[*].validation_steps[].acceptance_criteria_ids[]
algorithm: |
  for each ac_id in spec.acceptance_criteria:
    if ac_id not in any validation_steps.acceptance_criteria_ids:
      fail (missing_validation)
output: coverage.acceptance_coverage
```

**V5 规则：dod_satisfied**

```yaml
rule_id: V5
input:
  task.definition_of_done.criteria[].checked
algorithm: |
  for each criterion in task.definition_of_done.criteria:
    if not criterion.checked:
      fail (dod_unsatisfied)
output: failures[].category = dod_unsatisfied
```

### 6. 验证一致性 → V3/V4 规则

**设计遵循**（保留原逻辑）：

- 如果存在 `design.md`，提取技术决策
- 检查代码是否遵循这些决策
- 矛盾 → WARNING

**V3 规则：constraint_referenced**

```yaml
rule_id: V3
input:
  architecture.constraints[].id
  all_tasks[*].constraints.constraint_refs[]
algorithm: |
  for each con_id in architecture.constraints:
    if con_id not in any task.constraints.constraint_refs:
      warn (missing_constraint_ref)
output: coverage.constraint_coverage
```

**V4 规则：reference_valid**

```yaml
rule_id: V4
input:
  - task.requirement_refs[].requirement_id
  - task.requirement_refs[].scenario_ids[]
  - task.validation_steps[].acceptance_criteria_ids[]
  - task.constraints.constraint_refs[]
  - architecture.constraints[].related_requirements[]
algorithm: |
  for each ref_id in any reference field:
    if ref_id not in target_artifact:
      fail (broken_reference)
output: checks[].status
```

### 7. 验证执行 → V6 规则

**V6 规则：validation_passed**

依赖：`harness-runtime-verify` 填充的 `validation_status_map`

```yaml
rule_id: V6
input:
  all_tasks[*].validation_steps[].id
  context.validation_status_map
algorithm: |
  for each task in tasks:
    for step in task.validation_steps:
      status = validation_status_map.get(step.id)
      if status is None:
        fail (validation_failed, "未执行")
      elif status != "passed":
        fail (validation_failed, status)
output: coverage.validation_coverage
```

**`validation_status_map` 填充机制**：

| 来源 | 填充时机 | 字段来源 |
|------|---------|---------|
| `harness-runtime-verify` 执行结果 | runtime-verify 完成后 | 每条 command 的 exit_code → passed/failed |
| `harness-review-loop` 审查结果 | review-loop 完成后 | 高/中/低问题 → failed/passed |
| 手动测试结果 | 用户输入 | 用户报告 |

如未执行 `harness-runtime-verify`，`validation_status_map: {}`，V6 规则全部 `fail (未执行)`，并在 `meta_evaluation.verify_confidence` 中标注可信度降低。

### 8. 附修复路径（针对每个失败项）

每个 `fail` 和 `warn` 项，生成 `fix_path`：

| 失败类别 | 修复路径 | target_skill |
|---------|---------|--------------|
| `missing_task` | 运行 `harness-order` 为缺失 REQ 生成工单 | `harness-order` |
| `missing_validation` | 在对应 task 的 `validation_steps` 中增加步骤 | `harness-execute` |
| `missing_constraint_ref` | 在对应 task 的 `constraints.constraint_refs` 中增加引用 | `harness-execute` |
| `broken_reference` | 修正引用 ID 拼写错误 | `harness-specify` |
| `validation_failed` | 运行 `harness-runtime-verify` 修复 | `harness-runtime-verify` |
| `dod_unsatisfied` | 手动勾选 DoD 或执行遗漏步骤 | `harness-execute` |

输出字段：

```yaml
failures:
  - failure_id: "FAIL-{{verify_id}}-001"
    category: missing_validation
    affected_ids: ["AC-NOT-005", "AC-NOT-012"]
    impact: "2 个 AC 未被验证步骤覆盖"
    recommended_fix: "在 F22-order-001 的 validation_steps 中增加 validation 步骤引用这些 AC"
    blocking: true

recommendations:
  - priority: P0
    action: "为 AC-NOT-005, AC-NOT-012 增加 validation 步骤"
    target_skill: harness-execute
    target_artifact: F22-order-001
    estimated_effort: s
```

### 9. 生成验证报告

根据 `verify_output_mode` 选择输出：

#### 模式 1：`dual`（默认）

生成两个文件：

**`changes/{{change_name}}/verify-report.md`**（人类阅读）：
- 保留原有三维度报告结构（完整性/正确性/一致性）
- 新增覆盖度摘要（4 种覆盖率）
- 新增修复建议表格

**`changes/{{change_name}}/verify-report.yaml`**（机器消费）：
- 严格遵循 Verify Schema v0.2-draft
- 包含所有 coverage / checks / failures / recommendations / context 字段

#### 模式 2：`schema-only`

仅生成 `verify-report.yaml`，跳过 markdown 输出。

#### 模式 3：`markdown-only`

仅生成 `verify-report.md`（保持原行为，向后兼容），但应在 markdown 顶部提示：

```
> ⚠️ 当前为 markdown-only 模式，结构化数据未生成。
> 建议使用默认（dual）或 schema-only 模式以获得机器可消费的 Verify Report。
```

---

## 与 Verify Schema 字段映射表

| Verify Schema 字段 | 数据来源 | 计算逻辑 |
|--------------------|---------|---------|
| `target.feature_id` | 变更上下文 | 来自 `changes/{{change_name}}/delta-spec.md` |
| `target.task_ids` | 任务清单 | 解析自 `tasks.md` |
| `iteration` | 验证轮次 | 第 1 轮 = 1，第 N 轮 = N |
| `summary.total_checks` | 统计 | `checks[].length` |
| `summary.passed/failed/warned` | 统计 | 各类 checks 计数 |
| `coverage.requirement_coverage` | V1 规则 | 已覆盖需求 / 总需求 |
| `coverage.acceptance_coverage` | V2 规则 | 已覆盖 AC / 总 AC |
| `coverage.constraint_coverage` | V3 规则 | 已引用约束 / 总约束 |
| `coverage.validation_coverage` | V6 规则 | 已通过 validation / 总 validation |
| `checks[]` | V1-V6 规则 | 每条规则生成一条 check |
| `failures[]` | 聚合 | 按失败类别分组 |
| `recommendations[]` | 修复建议 | 从 failures 派生 |
| `context.validation_status_map` | harness-runtime-verify | 运行时执行结果 |
| `meta_evaluation.schema_compliance` | 自检 | YAML 是否通过 Schema 校验 |
| `meta_evaluation.reference_integrity` | V4 规则 | 引用是否全部有效 |
| `meta_evaluation.verify_confidence` | 综合评估 | 基于 Schema 合规性 + 引用完整性 + 覆盖率 |

---

## 约束

- **不修改代码**（只读验证）
- **不修改变更文件夹中的文件**（除生成 verify-report）
- **验证启发**：不确定时，SUGGESTION > WARNING > CRITICAL（宁缺勿滥）
- **每个问题必须给出具体建议和文件引用**
- **Schema 合规**：YAML 输出必须 100% 符合 Verify Schema v0.2-draft（待 v1.0 冻结）
- **validation_status_map 必填**：如未执行 harness-runtime-verify，必须在报告中明确标注 `validation_status_map: {}` 并将 V6 规则全部标记为 `fail (未执行)`，同时在 `meta_evaluation.verify_confidence` 中降低可信度评分

---

## 验证清单

执行完成后自检：

- [ ] 根据 `verify_output_mode` 正确生成对应文件
- [ ] verify-report.yaml 已生成（除非 markdown-only 模式）
- [ ] verify-report.yaml 符合 Verify Schema v0.2-draft
- [ ] coverage.requirement_coverage 计算正确（V1）
- [ ] coverage.acceptance_coverage 计算正确（V2）
- [ ] coverage.constraint_coverage 计算正确（V3）
- [ ] coverage.validation_coverage 计算正确（V6，依赖 validation_status_map）
- [ ] checks[].check_id 唯一
- [ ] checks[].fix_path 可执行
- [ ] failures[].blocking 准确标记
- [ ] recommendations[].target_skill 指向具体 Skill
- [ ] context.validation_status_map 已填充（如执行了 harness-runtime-verify）
- [ ] context.verify_output_mode 字段准确记录

---

## 返回格式

```yaml
summary:
  verify_id: "{{change_name}}-verify-report-{{iteration}}"
  output_mode: "{{verify_output_mode}}"
  schema_version: "v0.2-draft"
  iteration: 1
  coverage:
    requirement: 1.0
    acceptance: 0.833
    constraint: 1.0
    validation: 1.0
  checks:
    total: 25
    passed: 22
    failed: 2
    warned: 1
  overall_status: warning
  schema_compliance: true
  report_paths:
    yaml: "changes/{{change_name}}/verify-report.yaml"
    markdown: "changes/{{change_name}}/verify-report.md"
```

---

## 示例：完整 Verify Report（dual 模式）

### verify-report.yaml（机器消费）

```yaml
---
artifact:
  id: F22-verify-report-001
  type: report
  title: F22 通知推送系统验证报告
  domain: notification
  status: active
  version: "0.1.0"
  source:
    skill: harness-verify
    feature_id: F22
    created: "2026-06-24T18:00:00+08:00"
    updated: "2026-06-24T18:00:00+08:00"
  dependencies:
    - F22-specs
    - F22-order-001
    - F22-order-002
    - notification-architecture

target:
  feature_id: F22
  task_ids:
    - F22-order-001
    - F22-order-002
  spec_id: F22-specs
  architecture_id: notification-architecture

iteration: 1

summary:
  total_checks: 25
  passed: 22
  failed: 2
  warned: 1
  overall_status: warning

coverage:
  requirement_coverage:
    total_requirements: 5
    covered_requirements: 5
    coverage_rate: 1.0
    uncovered: []
  acceptance_coverage:
    total_criteria: 12
    covered_criteria: 10
    coverage_rate: 0.833
    uncovered:
      - AC-NOT-005
      - AC-NOT-012
  constraint_coverage:
    total_constraints: 3
    referenced_constraints: 3
    coverage_rate: 1.0
    unreferenced: []
  validation_coverage:
    total_validations: 8
    passed_validations: 8
    coverage_rate: 1.0

checks:
  - check_id: VRF-F22-001
    type: requirement_covered
    target_id: REQ-NOT-001
    status: pass
    message: "需求 REQ-NOT-001 被 F22-order-001 引用"
    evidence:
      artifact_id: F22-order-001
      field_path: requirement_refs[0].requirement_id
  - check_id: VRF-F22-002
    type: requirement_covered
    target_id: REQ-NOT-002
    status: fail
    message: "需求 REQ-NOT-002 未被任何 Task 引用"
    severity: block
    fix_path: "运行 harness-order 为 REQ-NOT-002 生成新工单"
  - check_id: VRF-F22-013
    type: acceptance_covered
    target_id: AC-NOT-005
    status: fail
    message: "AC-NOT-005 未被任何 validation_step 覆盖"
    severity: block
    fix_path: "在 F22-order-001.validation_steps 中增加步骤引用 AC-NOT-005"
  # ... 更多 checks

failures:
  - failure_id: FAIL-F22-001
    category: missing_task
    affected_ids:
      - REQ-NOT-002
    impact: "1 个需求未被实现，影响功能 F22 核心邮件发送能力"
    recommended_fix: "运行 harness-order 为 REQ-NOT-002 生成新工单 F22-order-003"
    blocking: true
  - failure_id: FAIL-F22-002
    category: missing_validation
    affected_ids:
      - AC-NOT-005
      - AC-NOT-012
    impact: "2 个 AC 未被验证步骤覆盖"
    recommended_fix: "在 F22-order-001.validation_steps 中增加 validation 步骤引用这些 AC"
    blocking: true

recommendations:
  - priority: P0
    action: "为 REQ-NOT-002 生成工单"
    target_skill: harness-order
    target_artifact: F22-order-003
    estimated_effort: s
  - priority: P0
    action: "为 AC-NOT-005, AC-NOT-012 增加 validation 步骤"
    target_skill: harness-execute
    target_artifact: F22-order-001
    estimated_effort: s

context:
  environment:
    runner: harness-verify
    version: v1.0
    timestamp: "2026-06-24T18:00:00+08:00"
    verify_output_mode: dual
  inputs:
    - artifact_id: F22-specs
      artifact_type: spec
      version: "1.0.0"
    - artifact_id: F22-order-001
      artifact_type: task
      version: "1.0.0"
    - artifact_id: F22-order-002
      artifact_type: task
      version: "1.0.0"
    - artifact_id: notification-architecture
      artifact_type: architecture
      version: "1.0.0"
  validation_status_map:
    VAL-F22-001-001: passed
    VAL-F22-001-002: passed
    VAL-F22-001-003: passed
    VAL-F22-002-001: passed
    # ... 由 harness-runtime-verify 填充

meta_evaluation:
  schema_compliance: true
  reference_integrity: true
  verify_confidence: 0.95
```

### verify-report.md（人类阅读）

```markdown
# F22 通知推送系统验证报告

> 详细结构化数据见 `verify-report.yaml`（Verify Schema v0.2-draft）
>
> 验证轮次：第 1 轮 | 生成时间：2026-06-24T18:00:00+08:00 | 输出模式：dual

## 摘要

| 维度 | 状态 |
|------|------|
| 完整性 | 5/5 需求已覆盖 |
| 正确性 | 10/12 AC 已覆盖 |
| 一致性 | 3/3 约束已引用 |
| 执行性 | 8/8 validation 通过 |
| **整体** | ⚠️ warning（2 个 P0 失败） |

## 覆盖度

| 覆盖率 | 值 | 状态 |
|--------|----|----|
| 需求覆盖 | 100% (5/5) | ✅ |
| AC 覆盖 | 83.3% (10/12) | ⚠️ |
| 约束引用 | 100% (3/3) | ✅ |
| 验证执行 | 100% (8/8) | ✅ |

## 失败项

### FAIL-001：missing_task
- **影响**：REQ-NOT-002
- **影响范围**：1 个需求未被实现，影响核心邮件发送能力
- **建议修复**：运行 `harness-order` 为 REQ-NOT-002 生成新工单 F22-order-003
- **阻塞**：是

### FAIL-002：missing_validation
- **影响**：AC-NOT-005, AC-NOT-012
- **影响范围**：2 个 AC 未被验证步骤覆盖
- **建议修复**：在 `F22-order-001.validation_steps` 中增加步骤
- **阻塞**：是

## 修复建议

| 优先级 | 动作 | 目标 Skill | 工作量 |
|--------|------|-----------|--------|
| P0 | 为 REQ-NOT-002 生成工单 | harness-order | S |
| P0 | 增加 AC-NOT-005, AC-NOT-012 的 validation 步骤 | harness-execute | S |

## 下一步

⚠️ 2 个 P0 失败需修复后重新验证（执行 `harness-verify` 第 2 轮）。

修复路径：
1. 运行 `harness-order F22` → 生成 F22-order-003
2. 运行 `harness-execute F22-order-001` → 增加 validation 步骤
3. 运行 `harness-verify F22 --mode=schema-only` → 第 2 轮验证
```

---

## 变更历史

- **v2.0**（2026-06-24，Phase 2.5.5）：完整对接 Verify Schema v0.2-draft
  - 引入 `verify_output_mode` 参数（dual / schema-only / markdown-only）
  - 实现 V1-V6 全部规则
  - 新增 `coverage.*` 四种覆盖率计算
  - 新增 `checks[]` / `failures[]` / `recommendations[]` 结构化输出
  - 保留原三维度报告作为 markdown 友好格式
  - 新增 `context.validation_status_map` 填充机制
- **v1.0**：初始版本，仅三维度 markdown 报告
