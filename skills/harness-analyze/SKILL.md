---
name: harness-analyze
description: 跨文档一致性审计。在工单生成后、执行前，扫描规格→工单之间的覆盖缺口、术语漂移、路径不一致。复用 Verify Schema 的 4 类 coverage 计算（requirement/acceptance/constraint/validation）。只读不改文件。支持 Skill 参数控制输出格式。
---

# harness-analyze：跨文档一致性审计（Verify Schema 覆盖率复用器）

## 触发条件

harness-order 完成后，harness-execute 之前执行。用户要求审计一致性时触发。

## 输入

- `project.yaml`（features 段完整）
- `docs/specs/`（域规格 + 架构规格）
- `orders/`（已生成的工单文件）
- `docs/meta/DEPENDENCY_MAP.md`
- `docs/meta/ARCHITECTURE.md`（新增：用于 constraint_coverage 计算）
- **新增**：Task Schema `validation_steps[]`（用于 acceptance_coverage + validation_coverage）
- `verify_output_mode`（可选参数）

## 输出

根据 `verify_output_mode` 参数：

| 输出模式 | 生成文件 | 适用场景 |
|---------|---------|---------|
| `dual`（默认） | `analyze-report.md` + `analyze-report.yaml` | 人类阅读 + 机器消费 |
| `schema-only` | `analyze-report.yaml` | CI / 自动消费 |
| `markdown-only` | `analyze-report.md` | 向后兼容（v1 行为） |

`analyze-report.yaml` 严格遵循 **Verify Schema v0.2-draft** 的子集：

- `coverage.requirement_coverage`（保留并对齐命名）
- `coverage.acceptance_coverage`（新增）
- `coverage.constraint_coverage`（新增）
- `coverage.validation_coverage`（新增）

**核心改进**：复用 Verify Schema 的 4 类 coverage 计算逻辑，避免重复实现。

---

## 参数控制

### `verify_output_mode`

```yaml
verify_output_mode:
  type: string
  enum: [dual, schema-only, markdown-only]
  default: dual
  description: |
    dual: 双建输出（默认）
    schema-only: 仅 YAML
    markdown-only: 仅 markdown（向后兼容）
```

### 参数传递方式

1. **命令行参数**：`/harness-analyze --mode=schema-only`
2. **环境变量**：`HARNESS_ANALYZE_OUTPUT_MODE=schema-only`

## 约束

- **严格只读**：不修改任何文件，只输出审计报告
- **ARCHITECTURE.md 是最高权威**：架构约束冲突自动标记为 CRITICAL
- **发现上限 50 条**：超出部分汇总在溢出摘要中
- **复用 Verify Schema**：4 类 coverage 计算算法与 Verify Schema 完全对齐，输出字段命名一致

## 步骤

### 0. 前置检查

确认所有工单已生成（扫描 `orders/` 目录）。若有缺失，报告"工单不完整，请先运行 /harness-order 补齐"，终止审计。

### 1. 加载文档（渐进式，按需读取）

**必读**：
- `project.yaml` → features 列表、constitution
- `ARCHITECTURE.md` → 分层规则、禁止清单、**架构约束列表**
- `docs/meta/DEPENDENCY_MAP.md` → 依赖关系表

**按需读取**（检测路径存在才读）：
- `docs/specs/` → 域规格（行为定义）
- `docs/specs/_architecture/` → 架构规格（API_CONTRACT / DATA_MODEL / DOMAIN_MAP / ERROR_CODE）
- `orders/*.md` → 逐个读取，提取元数据 + 功能三元组 + 实现清单 + **Task Schema 字段**

### 2. 构建语义模型（Verify Schema 对齐）

从加载的文档中提取结构化数据（内部使用，不输出）：

| 模型 | 来源 | 用途 | 对齐 Verify Schema |
|------|------|------|---------------------|
| **需求清单** | features + 域规格 | 逐项检查是否被工单覆盖 | `coverage.requirement_coverage` 输入 |
| **AC 清单** | spec.acceptance_criteria[] | 逐项检查是否被 validation_steps 覆盖 | `coverage.acceptance_coverage` 输入 |
| **架构约束清单** | ARCHITECTURE.md + 架构规格 | 逐项检查是否被 constraint_refs 引用 | `coverage.constraint_coverage` 输入 |
| **Validation 步骤清单** | task.validation_steps[] | 检查每步是否有可关联 command | `coverage.validation_coverage` 输入 |
| **工单清单** | orders/*.md | 逐项检查是否对应某个需求 | （保留原逻辑） |
| **术语表** | ARCHITECTURE + DOMAIN_MAP | 检查跨文档命名一致性 | （保留原逻辑） |
| **路径清单** | 工单实现清单 + DATA_MODEL | 检查文件路径是否冲突 | （保留原逻辑） |

**关键改进**：analyze 阶段（工单生成后、执行前）的 validation_coverage 是**预检覆盖率**——基于 validation_steps 是否存在可执行 command，与 harness-runtime-verify 的**执行覆盖率**（实际运行结果）区分。

### 3. 计算 4 类 coverage（Verify Schema 对齐）

**核心新增**：与 Verify Schema 完全对齐的 4 种覆盖率计算。

#### A. requirement_coverage（V1 规则）

```yaml
coverage:
  requirement_coverage:
    total_requirements: <spec.requirements[].length>
    covered_requirements: <count(req_id ∈ task.requirement_refs)>
    coverage_rate: <covered / total>
    uncovered:
      - REQ-NOT-002
```

**算法**（与 Verify Schema V1 一致）：

```yaml
for each req_id in spec.requirements:
  if req_id not in any task.requirement_refs:
    fail (missing_task)
```

#### B. acceptance_coverage（V2 规则）

```yaml
coverage:
  acceptance_coverage:
    total_criteria: <spec.acceptance_criteria[].length>
    covered_criteria: <count(ac_id ∈ task.validation_steps.acceptance_criteria_ids)>
    coverage_rate: <covered / total>
    uncovered:
      - AC-NOT-005
      - AC-NOT-012
```

**算法**（与 Verify Schema V2 一致）：

```yaml
for each ac_id in spec.acceptance_criteria:
  if ac_id not in any validation_steps.acceptance_criteria_ids:
    fail (missing_validation)
```

#### C. constraint_coverage（V3 规则）

```yaml
coverage:
  constraint_coverage:
    total_constraints: <architecture.constraints[].length>
    referenced_constraints: <count(con_id ∈ task.constraints.constraint_refs)>
    coverage_rate: <referenced / total>
    unreferenced:
      - CON-AUTH-001
    severity_distribution:   # 新增：按严重度统计
      must:
        total: 3
        referenced: 2
        unreferenced: 1
```

**算法**（与 Verify Schema V3 一致）：

```yaml
for each con_id in architecture.constraints:
  if con_id not in any task.constraints.constraint_refs:
    warn (missing_constraint_ref)
```

#### D. validation_coverage（V6 规则，预检版）

**注意**：analyze 阶段是预检（execution 未发生），所以此处的 validation_coverage 是**步骤定义覆盖率**，而非"执行覆盖率"。

```yaml
coverage:
  validation_coverage:
    total_validations: <task.validation_steps[].length>
    defined_validations: <count(step with command)>
    coverage_rate: <defined / total>
    status_distribution:   # analyze 阶段的预检状态
      defined: 7          # 有 command，可执行
      pending: 1          # 缺少 command，等待 harness-execute 补充
```

**算法**（预检版）：

```yaml
for each step in task.validation_steps:
  if step.command is null:
    pending (validation_step_pending)
  else:
    defined (validation_step_defined)
```

### 4. 检测扫描（6 个维度，保留原逻辑）

#### A. 覆盖缺口

- 需求无对应工单（CRITICAL）— 直接来源于 `requirement_coverage.uncovered`
- 工单无对应需求（HIGH）
- 架构规格中定义的端点/表未被任何工单实现（MEDIUM）

#### B. 术语漂移

- 同一概念在不同文档中命名不同（MEDIUM）
- 工单标题与 feature title 不一致（LOW）

#### C. 路径冲突

- 两个工单修改同一文件但未声明依赖（HIGH）
- 工单实现清单引用不存在的目录结构（MEDIUM）

#### D. 架构合规

- 工单实现计划违反 ARCHITECTURE.md 分层规则（CRITICAL）
- 工单引用了禁止清单中的模式（CRITICAL）
- **新增**：task.constraints.constraint_refs 未覆盖 must 级架构约束（HIGH）

#### E. 错误码一致性

- 工单中的错误码不在 ERROR_CODE.md 分配的域范围内（HIGH）
- 多个工单分配相同错误码（HIGH）

#### F. 依赖完整性

- 工单声明的依赖工单不存在（CRITICAL）
- 工单依赖顺序与 DEPENDENCY_MAP 不一致（HIGH）

### 5. 严重度分级

| 级别 | 含义 | 处理建议 |
|------|------|---------|
| **CRITICAL** | 阻塞执行，必须先修 | 修改工单或规格后再执行 |
| **HIGH** | 高风险，执行中大概率出问题 | 强烈建议先修 |
| **MEDIUM** | 中风险，执行中需要人工判断 | 执行时注意 |
| **LOW** | 风格/措辞改进 | 可忽略 |

> **与 harness-verify 严重度差异说明**：analyze 是规格层审计（工单生成前，用 4 级 CRITICAL/HIGH/MEDIUM/LOW），verify 是实现层验证（代码完成后，用 3 级 CRITICAL/WARNING/SUGGESTION）。两者作用阶段不同，故严重度词汇表不同。

### 6. 输出审计报告（按 `verify_output_mode`）

#### 模式 1：`dual`（默认）

生成两个文件：

**`analyze-report.md`**（人类阅读）：
- 保留原有 6 维度发现汇总
- 新增 4 类 coverage 摘要（与 Verify Schema 一致）
- 新增 CRITICAL 问题回退路径

**`analyze-report.yaml`**（机器消费）：
- 严格遵循 Verify Schema v0.2-draft 子集
- 包含 4 类 coverage 字段
- 可被 `harness-verify` 在执行前预先消费（检查 coverage 趋势）

#### 模式 2：`schema-only`

仅生成 `analyze-report.yaml`。

#### 模式 3：`markdown-only`

仅生成 `analyze-report.md`。

---

## 与 Verify Schema 字段映射表

| Verify Schema 字段 | analyze 来源 | 计算差异 |
|--------------------|--------------|---------|
| `coverage.requirement_coverage` | spec.requirements + task.requirement_refs | **完全一致** |
| `coverage.acceptance_coverage` | spec.acceptance_criteria + task.validation_steps.acceptance_criteria_ids | **完全一致** |
| `coverage.constraint_coverage` | architecture.constraints + task.constraints.constraint_refs | **完全一致**（含 severity_distribution） |
| `coverage.validation_coverage` | task.validation_steps[].command | **预检版**（基于 command 是否定义，非执行结果） |
| `context.environment.runner` | Skill 元数据 | `"harness-analyze"` |
| `meta_evaluation.verify_confidence` | 综合评估 | 基于 coverage + 严重度分布 |

**关键差异**：

- `analyze` 阶段：validation_coverage 是**步骤定义覆盖率**（command 是否定义）
- `verify` 阶段：validation_coverage 是**执行覆盖率**（validation_status_map 中 passed 占比）

两者可拼接形成完整的 validation 链路：`定义（analyze）→ 执行（runtime-verify）→ 验证（verify）`。

```markdown
## 一致性审计报告

> 详细结构化数据见 `analyze-report.yaml`（Verify Schema v0.2-draft）

审计时间：{{timestamp}}
工单数：{{order_count}} | 需求数：{{feature_count}}

### 4 类覆盖率（Verify Schema 对齐）

| 覆盖率 | 值 | 未覆盖项 |
|--------|-----|---------|
| 需求覆盖率 | {{requirement_coverage_rate}}（{{covered}}/{{total}}） | {{requirement_uncovered_count}} 个 |
| AC 覆盖率 | {{acceptance_coverage_rate}}（{{covered}}/{{total}}） | {{acceptance_uncovered_count}} 个 |
| 约束引用率 | {{constraint_coverage_rate}}（{{covered}}/{{total}}） | {{constraint_unreferenced_count}} 个（其中 {{must_unreferenced_count}} 个 must 级） |
| Validation 定义率 | {{validation_coverage_rate}}（{{covered}}/{{total}}） | {{validation_pending_count}} 个 pending |

### 发现汇总

| 级别 | 数量 |
|------|------|
| CRITICAL | {{critical_count}} |
| HIGH | {{high_count}} |
| MEDIUM | {{medium_count}} |
| LOW | {{low_count}} |

### 详细发现

| ID | 维度 | 级别 | 位置 | 描述 | 建议 |
|----|------|------|------|------|------|
| A1 | 覆盖缺口 | CRITICAL | F05 规格 | REQ-NOT-002 无对应工单 | 补充工单 F22-order-003 |
| D2 | 架构合规 | HIGH | F02 | task F02-order-001.constraints 未引用 CON-AUTH-001（must 级） | 增加 constraint_refs |
| C1 | 路径冲突 | HIGH | F02/F09 | 两工单均修改 app/core/config.py 但未声明依赖 | F09 添加 F02 依赖 |

### 下一步

<!-- 根据 critical_count 实际值选择输出一段 -->
若存在 CRITICAL 问题：
⚠️ 存在 {{critical_count}} 个 CRITICAL 问题，建议修复后再执行工单。

若无 CRITICAL 问题：
✅ 无 CRITICAL 问题，可以开始执行工单。

建议执行顺序：
1. 修复 CRITICAL（{{critical_count}} 个）
2. 修复 HIGH（{{high_count}} 个）
3. 开始执行：/harness-execute {{first_order_id}}
```

### CRITICAL 问题回退路径

当审计报告存在 CRITICAL 问题时，按以下规则回退到对应 Skill 修复：

| CRITICAL 类型 | 回退目标 | 操作 |
|-------------|----------|------|
| 覆盖缺口（需求无工单） | harness-order | 补生成缺失工单，更新 DEPENDENCY_MAP |
| 覆盖缺口（工单无需求） | harness-clarify + harness-specify | 补澄清需求，更新域规格 |
| 依赖完整性 | harness-order | 修正 DEPENDENCY_MAP 表 1/表 2 |
| 架构合规 | harness-specify-arch | 修正架构规格约束 |

> analyze 本身不修改任何文件，只输出报告。回退操作需要用户手动执行对应 Skill。

## 完成条件

- [ ] 所有已生成工单已扫描
- [ ] 6 个维度检测完成
- [ ] 4 类 coverage 已计算（requirement/acceptance/constraint/validation）
- [ ] coverage.* 字段命名与 Verify Schema 一致
- [ ] analyze-report.yaml 已生成（除非 markdown-only 模式）
- [ ] analyze-report.yaml 符合 Verify Schema v0.2-draft 子集
- [ ] analyze-report.md 已生成（除非 schema-only 模式）
- [ ] 下一步建议已给出

---

## 验证清单

- [ ] `coverage.requirement_coverage.uncovered` 准确列出未覆盖需求
- [ ] `coverage.acceptance_coverage.uncovered` 准确列出未覆盖 AC
- [ ] `coverage.constraint_coverage.unreferenced` 准确列出未引用约束
- [ ] `coverage.constraint_coverage.severity_distribution` 按 must/should/may 统计
- [ ] `coverage.validation_coverage.status_distribution` 区分 defined/pending
- [ ] 4 类 coverage 字段命名与 Verify Schema v0.2-draft 完全一致

---

## 返回格式

```yaml
summary:
  output_mode: {{verify_output_mode}}
  schema_version: "v0.2-draft"
  feature_count: {{feature_count}}
  order_count: {{order_count}}
  coverage:
    requirement: {{requirement_coverage_rate}}
    acceptance: {{acceptance_coverage_rate}}
    constraint: {{constraint_coverage_rate}}
    validation: {{validation_coverage_rate}}   # 预检版
  findings:
    critical: {{critical_count}}
    high: {{high_count}}
    medium: {{medium_count}}
    low: {{low_count}}
  schema_compliance: true

report_paths:
  yaml: "analyze-report.yaml"
  markdown: "analyze-report.md"
```

---

## 示例：Analyze Report（`dual` 模式）

### analyze-report.yaml 示例

```yaml
---
artifact:
  id: project-analyze-report-001
  type: report
  title: 一致性审计报告
  status: active
  version: "0.1.0"
  source:
    skill: harness-analyze
    created: "2026-06-24T18:00:00+08:00"
    updated: "2026-06-24T18:00:00+08:00"

target:
  scope: project
  order_count: 12

iteration: 1

summary:
  total_checks: 8
  passed: 5
  failed: 2
  warned: 1
  overall_status: warning

coverage:
  requirement_coverage:
    total_requirements: 28
    covered_requirements: 26
    coverage_rate: 0.929
    uncovered:
      - REQ-NOT-002
      - REQ-AUTH-005
  acceptance_coverage:
    total_criteria: 64
    covered_criteria: 58
    coverage_rate: 0.906
    uncovered:
      - AC-NOT-005
      - AC-NOT-012
      - AC-AUTH-003
      - AC-DATA-001
      - AC-DATA-002
      - AC-DATA-007
  constraint_coverage:
    total_constraints: 12
    referenced_constraints: 10
    coverage_rate: 0.833
    unreferenced:
      - CON-AUTH-001
      - CON-DATA-002
    severity_distribution:
      must:
        total: 7
        referenced: 6
        unreferenced: 1
      should:
        total: 5
        referenced: 4
        unreferenced: 1
  validation_coverage:
    total_validations: 36
    defined_validations: 32
    coverage_rate: 0.889
    status_distribution:
      defined: 32
      pending: 4

checks: []   # analyze 不生成逐项 checks（由 verify 生成）

failures: []   # analyze 不生成 failures 列表（输出 finding 列表代替）

recommendations:
  - priority: P0
    action: "为 REQ-NOT-002, REQ-AUTH-005 生成工单或更新现有工单的 requirement_refs"
    target_skill: harness-order
    estimated_effort: s
  - priority: P1
    action: "为 AC-NOT-005, AC-NOT-012 等 6 个 AC 增加 validation_steps"
    target_skill: harness-execute
    estimated_effort: m

context:
  environment:
    runner: harness-analyze
    version: v1.0
    timestamp: "2026-06-24T18:00:00+08:00"
    verify_output_mode: dual
  inputs:
    - artifact_id: project.yaml
      artifact_type: config
    - artifact_id: docs/specs/
      artifact_type: spec_collection
    - artifact_id: orders/
      artifact_type: task_collection
    - artifact_id: docs/meta/ARCHITECTURE.md
      artifact_type: architecture

meta_evaluation:
  schema_compliance: true
  reference_integrity: true
  verify_confidence: 0.91
```

---

## 变更历史

- **v2.0**（2026-06-24，Phase 2.5.8）：复用 Verify Schema v0.2-draft
  - 引入 `verify_output_mode` 参数（dual / schema-only / markdown-only）
  - **核心改进**：4 类 coverage 字段命名与 Verify Schema 完全对齐（requirement/acceptance/constraint/validation）
  - **核心改进**：复用 Verify Schema V1/V2/V3/V6 算法，不重复实现
  - 新增 `coverage.acceptance_coverage`（原 analyze 缺失）
  - 新增 `coverage.constraint_coverage`（原 analyze 缺失）
  - 新增 `coverage.constraint_coverage.severity_distribution`（按 must/should/may 统计）
  - 新增 `coverage.validation_coverage` 预检版（基于 command 定义，非执行结果）
  - 移除原有 `coverage_pct` / `order_match_pct` / `term_consistency`（与 Verify Schema 字段不对齐）
  - 保留原 6 维度检测 + 4 级严重度
  - 保留原 CRITICAL 问题回退路径
  - 新增"与 Verify Schema 字段映射表"

- **v1.0**：初始版本，自有 coverage_pct/order_match_pct/term_consistency 命名
---
