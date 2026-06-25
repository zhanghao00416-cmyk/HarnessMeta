---
name: harness-review-loop
description: 迭代代码审查与修复闭环。对实现结果进行多轮审查，计算 constraint_coverage（V3 规则），填充 validation_status_map，最多 3 轮。支持 Skill 参数控制输出格式。
---

# harness-review-loop：迭代代码审查闭环（Verify Schema 约束覆盖计算器）

## 触发条件

以下场景执行：

1. **工单执行后**：`harness-execute` 阶段 3（自审）完成后，执行本 Skill 进行独立审查
2. **变更应用后**：`harness-apply` 完成后，审查变更实现质量
3. **用户主动要求**：用户说"审查代码"或"代码审查"
4. **运行时验证前**：`harness-runtime-verify` 前，先通过代码审查确保基本质量
5. **链路验证前**：`harness-verify` 调用本 Skill 计算 `constraint_coverage`（V3 规则）

## 输入

- 当前工单/变更 ID
- `orders/<ORDER_ID>/` 或 `changes/<CHANGE_NAME>/` 目录
- `context.md`（如存在，由 harness-context 生成）
- 相关规格文档（`spec.md`、`delta-spec.md`）
- **新增**：架构文档（`ARCHITECTURE.md`、`API_CONTRACT.md`、`DATA_MODEL.md` 等）—— 用于约束引用追踪
- **新增**：Task Schema 字段（`task.constraints.constraint_refs`）
- `AGENTS.md`（如存在，用于 Agent 调用协议）
- `verify_output_mode`（可选参数）

## 输出

根据 `verify_output_mode` 参数：

| 输出模式 | 生成文件 | 适用场景 |
|---------|---------|---------|
| `dual`（默认） | `review-report.md` + `review-report.yaml` | 人类阅读 + 机器消费 |
| `schema-only` | `review-report.yaml` | CI / 自动消费 / harness-verify 调用 |
| `markdown-only` | `review-report.md` | 向后兼容（v1 行为） |

`review-report.yaml` 严格遵循 **Verify Schema v0.2-draft** 的子集：

- `coverage.constraint_coverage`（核心新增）
- `context.validation_status_map`
- `meta_evaluation.*`

---

## 参数控制

### `verify_output_mode`

```yaml
verify_output_mode:
  type: string
  enum: [dual, schema-only, markdown-only]
  default: dual
  description: |
    dual: 双轨输出（默认）
    schema-only: 仅 YAML（被 harness-verify 消费时使用）
    markdown-only: 仅 markdown（向后兼容）
```

### 参数传递方式

1. **命令行参数**：`/harness-review-loop --mode=schema-only {{ORDER_ID}}`
2. **环境变量**：`HARNESS_REVIEW_LOOP_OUTPUT_MODE=schema-only`
3. **harness-verify 调用**：自动使用 `schema-only` 模式

---

## 步骤

### 1. 启动审查（第 1 轮）

读取实现结果（代码文件、变更说明），对照以下维度审查：

| 维度 | 检查内容 | 映射到 Verify Schema |
|------|---------|---------------------|
| **architecture** | 是否遵循架构约束？目录结构正确？设计模式一致？ | `coverage.constraint_coverage` |
| **coding_style** | 命名规范？代码格式？注释质量？ | `checks[].constraint_referenced`（如 style 已被定义为约束） |
| **naming** | 变量/函数/类名语义清晰？与项目约定一致？ | （保留原逻辑，不直接映射） |
| **security** | 输入验证？权限检查？SQL 注入/XSS 防护？ | `failures[].category = security_issue` |
| **performance** | 不必要的查询？循环嵌套？大数据量处理？ | `failures[].category = performance_issue` |
| **requirement_coverage** | 是否覆盖所有需求？边界条件处理？ | （由 harness-verify 聚合） |

**审查方式**：

- 如支持 Agent 模式，调用 `code-reviewer` Agent 执行审查
- 如不支持 Agent 模式，自行按维度逐项检查

### 2. 解析架构约束（核心新增）

**新增步骤**：从架构文档解析约束列表：

```yaml
extracted_constraints:
  - constraint_id: "CON-AUTH-001"
    description: "密码必须使用 bcrypt 哈希存储"
    source: "ARCHITECTURE.md"
    related_requirements: ["REQ-AUTH-001"]
    related_modules: ["backend.auth.service"]
    severity: "must"   # must/should/may
  - constraint_id: "CON-DATA-002"
    description: "用户表必须有 created_at 和 updated_at 字段"
    source: "DATA_MODEL.md"
    related_requirements: ["REQ-DATA-001"]
    severity: "must"
```

**解析来源**（按优先级）：

1. `ARCHITECTURE.md` 中的 "架构约束" 章节
2. `API_CONTRACT.md` 中的约束声明
3. `DATA_MODEL.md` 中的字段约束
4. `ERROR_CODE.md` 中的错误处理约束
5. Task Schema 中的 `task.constraints.constraint_refs`（反向查询）

### 3. 计算 constraint_coverage（核心新增，V3 规则）

**核心新增**：基于架构约束列表和 Task Schema 的 `constraint_refs` 计算覆盖率：

```yaml
rule_id: V3
name: constraint_referenced
input:
  architecture.constraints[].id
  all_tasks[*].constraints.constraint_refs[]
algorithm: |
  for each con_id in architecture.constraints:
    if con_id not in any task.constraints.constraint_refs:
      warn (missing_constraint_ref)
output: coverage.constraint_coverage
```

**输出**：

```yaml
coverage:
  constraint_coverage:
    total_constraints: 5          # 架构中定义的总约束数
    referenced_constraints: 4     # 被至少一个 Task 引用的约束数
    coverage_rate: 0.8            # 4 / 5
    unreferenced:                 # 未被引用的约束 ID 列表
      - CON-AUTH-001
    severity_distribution:        # 按严重级别统计
      must:
        total: 3
        referenced: 2
        unreferenced: 1
      should:
        total: 2
        referenced: 2
        unreferenced: 0
```

**计算逻辑**：

```
total_constraints = architecture.constraints[].length
referenced_constraints = count(con_id ∈ any task.constraints.constraint_refs)
coverage_rate = referenced_constraints / total_constraints
```

### 4. 结构化发现问题

审查结果格式（保留原结构 + 新增字段）：

```yaml
issues:
  - issue_id: "ISS-{{review_id}}-001"
    severity: high
    category: security
    description: "登录接口未对密码进行强度验证"
    recommendation: "在 service 层添加密码长度和复杂度检查"
    affected_files:
      - backend/auth/service.py
    related_constraints:           # 新增：关联的架构约束
      - CON-AUTH-002
    validation_step_id: "VAL-F22-001-002"   # 新增：对应的验证步骤
    mapped_to:                     # 新增：映射到 Verify Schema
      coverage_impact: "constraint_coverage"
      failure_category: "constraint_violation"
  
  - issue_id: "ISS-{{review_id}}-002"
    severity: medium
    category: coding_style
    description: "函数名 login_user 不符合项目约定"
    recommendation: "重命名为 authenticate_user"
    affected_files:
      - backend/auth/router.py
      - backend/auth/service.py
    validation_step_id: "VAL-F22-001-003"
```

**严重级别定义**：

| 级别 | 含义 | 处理要求 | 映射到 validation_status_map |
|------|------|---------|------------------------------|
| `high` | 阻塞性问题：安全漏洞、架构偏离、需求遗漏 | 必须修复 | `failed` |
| `medium` | 重要问题：风格不一致、命名错误、性能隐患 | 建议修复 | `failed`（如未修复） |
| `low` | 轻微问题：格式、注释、可优化点 | 可选修复 | `passed`（记录但不阻塞） |

### 5. 填充 validation_status_map（新增）

**新增**：将审查结果映射到 `validation_status_map`：

```yaml
validation_status_map:
  "VAL-F22-001-001": "passed"        # 无关联 issue
  "VAL-F22-001-002": "failed"        # 关联 high/medium issue
  "VAL-F22-001-003": "failed"        # 关联 medium issue
  "VAL-F22-001-004": "passed"        # 关联 low issue
```

**填充规则**：

| 审查结果 | validation_status_map 值 | 触发条件 |
|---------|--------------------------|---------|
| 无 issue | `passed` | 该 step 关联的所有审查通过 |
| high issue | `failed` | 阻塞性问题，必须修复 |
| medium issue | `failed` | 重要问题 |
| low issue | `passed` | 轻微问题，记录但不阻塞 |

**step_id 提取策略**：

- 优先：从 `task.validation_steps[].id` 中提取
- 回退：根据审查维度和 task 关联自动生成 `VAL-{task_id}-{review_dim}-{seq}`

### 6. 判断审查结果

```yaml
# 通过条件：无 high 级别问题，且 medium 不超过 2 个
passed: true
overall_status: passing   # passing/warning/failing
```

- **passing**：无 `high` 级别问题，且 `medium` 不超过 2 个 → 进入报告生成
- **warning**：无 `high` 级别问题，但 `medium` 超过 2 个 → 进入修复阶段
- **failing**：存在 `high` 级别问题 → 进入修复阶段

**Verify Schema 映射**：

```yaml
summary:
  overall_status:
    passing: 全部通过
    warning: 有警告但无失败
    failing: 有失败项
```

### 7. 修复阶段（如未通过）

保留原 3 轮修复循环逻辑。

生成修复请求，包含：

- 所有 `high` 和 `medium` 级别问题
- 具体修复建议
- 受影响文件清单
- 关联的架构约束（`related_constraints`）

**调用 Agent 修复**（如支持 Agent 模式）：

| 问题类型 | 调用 Agent |
|---------|-----------|
| 后端代码问题 | `backend-dev` |
| 前端代码问题 | `frontend-dev` |
| 混合问题 | 分别调用对应 Agent |

### 8. 重新审查（第 N 轮）

修复完成后，再次执行审查：

```yaml
round: 2
previous_issues:
  total: 5
  resolved: 3
  remaining: 2
new_issues: 0
```

对比上一轮：

- 记录已修复的问题（`validation_status_map` 中 status 从 failed → passed）
- 记录未修复的问题
- 记录新发现的问题（修复引入的回归）

### 9. 循环控制

**最大轮次**：3 轮

```yaml
max_rounds: 3
```

**终止条件**：

- 审查通过（`passed: true`）→ 立即停止，生成报告
- 达到最大轮次仍未通过 → 标记 `status: review_failed`，升级人工审查

### 10. 生成审查报告

#### 模式 1：`dual`（默认）

生成两个文件：

**`review-report.md`**（人类阅读）：
- 保留原报告结构（issues / rounds / resolved / remaining）
- 新增 `constraint_coverage` 章节
- 新增 `validation_status_map` 摘要
- 新增架构约束引用追踪表

**`review-report.yaml`**（机器消费）：
- 严格遵循 Verify Schema v0.2-draft 子集
- 包含 `coverage.constraint_coverage` 和 `context.validation_status_map`
- 可被 `harness-verify` 直接消费

#### 模式 2：`schema-only`

仅生成 `review-report.yaml`，跳过 markdown 输出。

#### 模式 3：`markdown-only`

仅生成 `review-report.md`（保持原行为）。

---

## 与 Verify Schema 字段映射表

| Verify Schema 字段 | 数据来源 | 计算逻辑 |
|--------------------|---------|---------|
| `coverage.constraint_coverage.total_constraints` | 架构文档 | `architecture.constraints[].length` |
| `coverage.constraint_coverage.referenced_constraints` | Task Schema | `count(con_id ∈ task.constraints.constraint_refs)` |
| `coverage.constraint_coverage.coverage_rate` | 派生 | `referenced / total` |
| `coverage.constraint_coverage.unreferenced` | 派生 | 未被引用的约束 ID 列表 |
| `context.validation_status_map` | 审查结果 | 每条 issue 映射到对应 step.id |
| `context.environment.runner` | Skill 元数据 | `"harness-review-loop"` |
| `meta_evaluation.verify_confidence` | 综合评估 | 基于 issue 严重度分布 + 约束覆盖率 |

**注意**：本 Skill 不计算 `coverage.requirement_coverage` / `acceptance_coverage` / `validation_coverage`，这些由 `harness-verify` 聚合。

---

## 约束

- **不直接修改代码**：审查 Skill 只发现问题，修复由 Agent 或用户执行
- **客观标准**：审查依据项目已有规格和架构文档，不引入个人偏好
- **增量审查**：每轮只关注变更部分，不重复审查未修改的文件
- **可追溯**：每轮审查结果必须记录，便于追踪问题生命周期
- **Schema 合规**：YAML 输出必须 100% 符合 Verify Schema v0.2-draft 子集
- **约束优先**：架构约束覆盖率（`constraint_coverage`）必须每次审查都计算，即使所有 issue 都已修复

---

## 验证清单

执行完成后自检：

- [ ] 架构约束已从架构文档解析
- [ ] `coverage.constraint_coverage` 已计算（V3 规则）
- [ ] `coverage.constraint_coverage.unreferenced` 准确列出未引用约束
- [ ] 审查已执行（至少 1 轮）
- [ ] 发现的问题已结构化记录（含严重级别、类别、建议、`related_constraints`）
- [ ] `validation_status_map` 已填充（每个 step.id → passed/failed）
- [ ] 如未通过，修复请求已生成
- [ ] 如进入修复，修复后重新审查已执行
- [ ] 轮次控制已生效（不超过 3 轮）
- [ ] `review-report.yaml` 已生成（除非 markdown-only 模式）
- [ ] `review-report.yaml` 符合 Verify Schema v0.2-draft 子集
- [ ] `review-report.md` 已生成（除非 schema-only 模式）
- [ ] `progress.md` 已更新审查状态

---

## 返回格式

```yaml
summary:
  order_id: {{ORDER_ID}}
  output_mode: {{verify_output_mode}}
  schema_version: "v0.2-draft"
  rounds: {{rounds}}
  issues:
    total: {{total}}
    resolved: {{resolved}}
    remaining: {{remaining}}
    severity_distribution:
      high: {{high_count}}
      medium: {{medium_count}}
      low: {{low_count}}
  coverage:
    constraint: 0.8
    constraint_unreferenced: ["{{unreferenced_constraint_ids}}"]
  validation_status_map:
    filled: {{filled_count}}
    total: {{total_count}}
  status: {{passed/review_failed}}
  
report_paths:
  yaml: "orders/{{ORDER_ID}}/review-report.yaml"
  markdown: "orders/{{ORDER_ID}}/review-report.md"
```

---

## 示例：Review Report（dual 模式）

### review-report.yaml 示例

```yaml
---
artifact:
  id: F22-review-report-001
  type: report
  title: F22 通知推送系统代码审查报告
  domain: notification
  status: active
  version: "0.1.0"
  source:
    skill: harness-review-loop
    feature_id: F22
    created: "2026-06-24T18:00:00+08:00"
    updated: "2026-06-24T18:00:00+08:00"
  dependencies:
    - F22-order-001
    - F22-order-002
    - notification-architecture

target:
  feature_id: F22
  task_ids:
    - F22-order-001
    - F22-order-002
  architecture_id: notification-architecture

iteration: 1

summary:
  total_checks: 12
  passed: 9
  failed: 2
  warned: 1
  overall_status: failing

coverage:
  constraint_coverage:
    total_constraints: 5
    referenced_constraints: 4
    coverage_rate: 0.8
    unreferenced:
      - CON-AUTH-001
    severity_distribution:
      must:
        total: 3
        referenced: 2
        unreferenced: 1
      should:
        total: 2
        referenced: 2
        unreferenced: 0

checks:
  - check_id: VRF-F22-RV-001
    type: constraint_referenced
    target_id: CON-AUTH-001
    status: warn
    message: "约束 CON-AUTH-001 未被任何 Task 引用"
    severity: warning
    fix_path: "在 F22-order-001.constraints.constraint_refs 中增加 CON-AUTH-001"
  - check_id: VRF-F22-RV-002
    type: constraint_referenced
    target_id: CON-AUTH-002
    status: pass
    message: "约束 CON-AUTH-002 被 F22-order-001 引用"
    evidence:
      artifact_id: F22-order-001
      field_path: constraints.constraint_refs[0]
  # ... 更多 checks

failures:
  - failure_id: FAIL-F22-RV-001
    category: missing_constraint_ref
    affected_ids:
      - CON-AUTH-001
    impact: "1 个 must 级架构约束未被任何 Task 引用"
    recommended_fix: "在 F22-order-001.constraints.constraint_refs 中增加 CON-AUTH-001"
    blocking: false

recommendations:
  - priority: P1
    action: "为 CON-AUTH-001 添加 Task 引用"
    target_skill: harness-execute
    target_artifact: F22-order-001
    estimated_effort: xs

context:
  environment:
    runner: harness-review-loop
    version: v1.0
    timestamp: "2026-06-24T18:00:00+08:00"
    verify_output_mode: dual
  inputs:
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
    VAL-F22-001-002: failed   # 关联 high issue
    VAL-F22-001-003: failed   # 关联 medium issue
    VAL-F22-001-004: passed   # 关联 low issue
    VAL-F22-002-001: passed

meta_evaluation:
  schema_compliance: true
  reference_integrity: true
  verify_confidence: 0.88
```

### review-report.md 示例（精简版）

```markdown
# F22 代码审查报告

> 详细结构化数据见 `review-report.yaml`（Verify Schema v0.2-draft）

## 摘要

| 指标 | 数值 |
|------|------|
| 审查轮次 | 1 |
| 总问题 | 3 |
| 已修复 | 0 |
| 未修复 | 3 |
| **最终状态** | ❌ failing |

## 约束覆盖度（V3 规则）

| 指标 | 值 |
|------|---|
| 总约束数 | 5 |
| 已引用 | 4 |
| **覆盖率** | 80% |
| 未引用 | CON-AUTH-001 |

### 按严重级别

| 严重度 | 总数 | 已引用 | 未引用 |
|--------|------|--------|--------|
| must | 3 | 2 | **1** ⚠️ |
| should | 2 | 2 | 0 |

## validation_status_map 摘要

| Step ID | Status | 关联 Issue |
|---------|--------|-----------|
| VAL-F22-001-001 | ✅ passed | 无 |
| VAL-F22-001-002 | ❌ failed | ISS-001 (high) |
| VAL-F22-001-003 | ❌ failed | ISS-002 (medium) |
| VAL-F22-001-004 | ✅ passed | ISS-003 (low) |
| VAL-F22-002-001 | ✅ passed | 无 |

## 失败项

### FAIL-001：missing_constraint_ref
- **影响**：CON-AUTH-001
- **影响范围**：1 个 must 级架构约束未被引用
- **建议修复**：在 `F22-order-001.constraints.constraint_refs` 中增加 CON-AUTH-001
- **阻塞**：否（warning）

## 下一步

⚠️ 1 个 must 级约束未被引用，2 个审查问题未修复。需修复后重新审查。
```

---

## 变更历史

- **v2.0**（2026-06-24，Phase 2.5.7）：完整对接 Verify Schema v0.2-draft
  - 引入 `verify_output_mode` 参数（dual / schema-only / markdown-only）
  - **核心新增**：`coverage.constraint_coverage` 计算（V3 规则）
  - **核心新增**：架构约束引用追踪（从 ARCHITECTURE/API_CONTRACT/DATA_MODEL 解析）
  - **核心新增**：`coverage.constraint_coverage.severity_distribution`（按严重度统计）
  - **核心新增**：`validation_status_map` 填充（issue 严重度 → step status）
  - 新增 issue → step_id 映射机制
  - 新增 `related_constraints` 字段（issue 与约束的关联）
  - 保留原 3 轮审查循环
  - 保留原高/中/低严重度分级
- **v1.0**：初始版本，仅 markdown review-report.md
---