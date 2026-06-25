---
name: harness-runtime-verify
description: 运行时验证。通过实际工具命令（lint、test、build）验证代码可执行性，填充 Verify Schema 的 validation_status_map。最多 3 轮修复。支持 Skill 参数控制输出格式。
---

# harness-runtime-verify：运行时验证（Verify Schema 验证步骤执行器）

## 触发条件

以下场景执行：

1. **代码审查后**：`harness-review-loop` 通过后，执行运行时验证确保代码可运行
2. **变更应用后**：`harness-apply` 完成后，验证变更是否破坏构建/测试
3. **链路验证前**：`harness-verify` 调用本 Skill 填充 `validation_status_map`（V6 规则依赖）
4. **用户主动要求**：用户说"运行测试"或"验证构建"
5. **提交前**：作为提交前的质量门禁，确保代码可编译、可通过测试

## 输入

- 实现结果（代码文件路径列表）
- `orders/<ORDER_ID>/` 或 `changes/<CHANGE_NAME>/` 目录
- `project.yaml`（用于检测项目类型和技术栈）
- `tasks.md`（**新增**：包含 Task Schema `validation_steps[]` 字段）
- `review-report.md`（可选，来自 harness-review-loop）
- `verify_output_mode`（可选参数，控制输出格式）
- 项目依赖文件（`requirements.txt`、`package.json`、`pyproject.toml` 等）

## 输出

根据 `verify_output_mode` 参数：

| 输出模式 | 生成文件 | 适用场景 |
|---------|---------|---------|
| `dual`（默认） | `runtime-report.md` + `runtime-report.yaml` | 人类阅读 + 机器消费 |
| `schema-only` | `runtime-report.yaml` | CI / 自动消费 / harness-verify 调用 |
| `markdown-only` | `runtime-report.md` | 向后兼容（v1 行为） |

`runtime-report.yaml` 严格遵循 **Verify Schema v0.2-draft** 的子集：

- `coverage.validation_coverage`
- `context.validation_status_map`
- `meta_evaluation.*`

可被 `harness-verify` 直接消费，作为 V6 规则的输入。

---

## 参数控制

### `verify_output_mode`

```yaml
verify_output_mode:
  type: string
  enum: [dual, schema-only, markdown-only]
  default: dual
  description: |
    控制 Runtime Report 的输出格式。
    - dual: 双轨输出（默认）
    - schema-only: 仅 YAML（被 harness-verify 消费时使用）
    - markdown-only: 仅 markdown（向后兼容）
```

### 参数传递方式

支持以下三种方式（按优先级）：

1. **命令行参数**：`/harness-runtime-verify --mode=schema-only {{ORDER_ID}}`
2. **环境变量**：`HARNESS_RUNTIME_VERIFY_OUTPUT_MODE=schema-only`
3. **harness-verify 调用**：自动使用 `schema-only` 模式

---

## 步骤

### 1. 检测项目类型

从以下线索推断项目类型和技术栈：

| 检测依据 | 项目类型 |
|---------|---------|
| `project.yaml` 中的 `tech_stack` 字段 | 直接读取 |
| `requirements.txt` / `pyproject.toml` | Python |
| `package.json` | Node.js |
| `manage.py` + `settings.py` | Django |
| `main.py` + FastAPI 导入 | FastAPI |
| `src/main.rs` / `Cargo.toml` | Rust |
| `go.mod` | Go |
| `Dockerfile` / `docker-compose.yml` | Docker |
| `vite.config.ts` / `vue.config.js` | Vue/React |

输出：

```yaml
project_type:
  primary: python
  framework: fastapi
  frontend: vue
  package_manager: pip
```

### 2. 解析 Task Schema 的 validation_steps（新增）

**新增步骤**：从 `tasks.md` 解析 Task Schema 字段：

```yaml
extracted_validation_steps:
  - step_id: "VAL-F22-001-001"
    command: "pytest tests/test_auth.py::test_login"
    description: "登录接口返回 JWT token"
    expected_result: "返回 200 + JWT"
    acceptance_criteria_ids: ["AC-AUTH-001"]
    requirement_refs: ["REQ-AUTH-001"]
    type: "test"
  - step_id: "VAL-F22-001-002"
    command: "ruff check backend/auth/"
    description: "代码风格检查"
    expected_result: "无错误"
    acceptance_criteria_ids: ["AC-AUTH-002"]
    type: "lint"
```

**解析策略**：

1. **优先**：如任务为结构化 Task Schema YAML 格式，直接解析 `validation_steps[]`
2. **回退**：如为旧 markdown 格式，从 ```` ```bash ```` 代码块启发式提取命令
3. **最终回退**：使用项目类型默认命令（步骤 3）

**step_id 生成规则**（如未指定）：

```
格式：VAL-{task_id}-{seq:03d}
示例：VAL-F22-001-001
```

### 3. 构建验证计划

**原有逻辑保留**：根据项目类型选择默认验证命令。

**新增合并逻辑**：

```yaml
validation_plan:
  # 来源 1：Task Schema 定义的 validation_steps（优先级最高）
  from_task_schema:
    - step_id: "VAL-F22-001-001"
      command: "pytest tests/test_auth.py::test_login"
      runner: pytest
      source: "task_schema"
  
  # 来源 2：项目类型默认验证命令（兜底）
  from_project_defaults:
    - step_id: "VAL-F22-DEFAULT-LINT"
      command: "ruff check ."
      runner: ruff
      source: "project_default"
      applies_when: "no_task_schema_validation"
```

**合并策略**：

1. **优先使用 Task Schema 中的 `validation_steps[].command`**——这是用户明确声明的验证步骤
2. **如未指定**，使用项目类型默认命令
3. **每条命令必须能映射到一个 `step_id`**——用于填充 `validation_status_map`

### 4. 执行验证命令

按顺序执行验证计划中的命令，记录结果。

**新增**：每条结果必须包含 `step_id` 映射：

```yaml
results:
  - step_id: "VAL-F22-001-001"
    command: "pytest tests/test_auth.py::test_login"
    runner: pytest
    exit_code: 0
    stdout: "1 passed"
    stderr: ""
    status: passed       # passed/failed/skipped/error
    started_at: "2026-06-24T18:00:00+08:00"
    duration_ms: 1234
    mapped_validation_step: "VAL-F22-001-001"
```

### 5. 分类失败

将失败的命令按类别归类（保留原逻辑）：

| 类别 | 说明 | 示例 |
|------|------|------|
| `lint` | 代码风格/格式问题 | ruff, eslint 报错 |
| `typing` | 类型错误 | mypy, TypeScript 类型检查失败 |
| `test` | 测试失败 | pytest, jest 测试不通过 |
| `build` | 构建失败 | npm run build, docker build 失败 |
| `dependency` | 依赖问题 | 缺少依赖、版本冲突 |
| `runtime` | 运行时错误 | 导入错误、模块未找到 |
| `configuration` | 配置错误 | 环境变量缺失、配置格式错误 |

输出结构化发现：

```yaml
failures:
  - step_id: "VAL-F22-001-002"
    category: test
    command: "pytest tests/test_auth.py"
    error: "AssertionError: expected 200, got 401"
    affected_files:
      - backend/auth/service.py
```

### 6. 填充 validation_status_map（核心新增）

基于执行结果填充 Verify Schema 的 `validation_status_map`：

```yaml
validation_status_map:
  "VAL-F22-001-001": "passed"     # exit_code == 0
  "VAL-F22-001-002": "failed"     # exit_code != 0
  "VAL-F22-001-003": "skipped"    # 未执行
  "VAL-F22-001-004": "error"      # 执行器本身出错
```

**填充规则**：

| 执行结果 | status 值 | 触发条件 |
|---------|----------|---------|
| 命令 exit_code == 0 | `passed` | 测试/构建通过 |
| 命令 exit_code != 0 | `failed` | 测试失败/lint 报错 |
| 命令未执行 | `skipped` | 标记为 skip 或前序失败导致跳过 |
| 执行器本身出错 | `error` | 命令找不到、权限不足、环境异常 |

**完整性保证**：必须包含所有 `task.validation_steps[].id`，缺失项标记为 `skipped` 并在报告中标注。

### 7. 计算 validation_coverage（新增）

基于 `validation_status_map` 计算 `coverage.validation_coverage`：

```yaml
coverage:
  validation_coverage:
    total_validations: 8
    passed_validations: 7
    coverage_rate: 0.875
    status_distribution:
      passed: 7
      failed: 1
      skipped: 0
      error: 0
```

**计算公式**：

```
total_validations = task.validation_steps[].length
passed_validations = count(validation_status_map[k] == "passed")
coverage_rate = passed_validations / total_validations
```

### 8. 检查 DoD（V5 规则，新增）

如 Task Schema 中定义了 `definition_of_done.criteria[]`，自动检查：

```yaml
dod_status:
  total_criteria: 5
  checked: 5
  unchecked: 0
  satisfied: true   # 所有 checked 均为 true
  output:
    coverage:
      dod_coverage:
        total: 5
        satisfied: 5
        rate: 1.0
```

未满足的 DoD 进入 `failures[]` 列表（V5 规则）：

```yaml
failures:
  - failure_id: "FAIL-{{verify_id}}-001"
    category: dod_unsatisfied
    affected_ids: ["{{task_id}}.definition_of_done.criteria[2]"]
    impact: "1 个 DoD 条件未勾选"
    recommended_fix: "手动完成遗漏步骤并勾选 DoD"
    blocking: true
```

### 9. 修复阶段（如存在失败）

保留原 3 轮修复循环逻辑。

生成修复请求，包含：

- 失败类别和具体错误信息
- 失败的命令 + step_id
- 受影响的文件

**调用 Agent 修复**（如支持 Agent 模式）：

| 失败类别 | 调用 Agent |
|---------|-----------|
| lint / typing / runtime / test（后端） | `backend-dev` |
| lint / typing / build / test（前端） | `frontend-dev` |
| dependency / configuration | 根据项目类型调用对应 Agent |

### 10. 重新验证

修复完成后，重新执行失败的命令：

```yaml
round: 2
previous_failures:
  total: 3
  resolved: 2
  remaining: 1
new_failures: 0
```

对比上一轮：

- 记录已修复的失败（`validation_status_map` 中 status 从 failed → passed）
- 记录未修复的失败
- 记录新引入的失败（回归）

### 11. 循环控制

**最大修复轮次**：3 轮

```yaml
max_fix_rounds: 3
```

**终止条件**：

- 验证全部通过（所有 validation_step status == "passed"）→ 立即停止，生成报告
- 达到最大轮次仍有失败 → 标记 `status: verification_failed`，升级人工处理

### 12. 生成运行时报告

#### 模式 1：`dual`（默认）

生成两个文件：

**`runtime-report.md`**（人类阅读）：
- 保留原报告结构（rounds / commands / failures / fix_history）
- 新增 `validation_status_map` 摘要
- 新增 `coverage.validation_coverage` 摘要
- 新增 DoD 状态

**`runtime-report.yaml`**（机器消费）：
- 严格遵循 Verify Schema v0.2-draft 子集
- 包含 `coverage.validation_coverage` 和 `context.validation_status_map`
- 可被 `harness-verify` 直接消费

#### 模式 2：`schema-only`

仅生成 `runtime-report.yaml`，跳过 markdown 输出。

#### 模式 3：`markdown-only`

仅生成 `runtime-report.md`（保持原行为），但应在 markdown 顶部提示：

```
> ⚠️ 当前为 markdown-only 模式，validation_status_map 未生成。
> harness-verify 调用时将无法获取 V6 规则所需的运行时状态。
```

---

## 与 Verify Schema 字段映射表

| Verify Schema 字段 | 数据来源 | 计算逻辑 |
|--------------------|---------|---------|
| `coverage.validation_coverage.total_validations` | Task Schema | `task.validation_steps[].length` |
| `coverage.validation_coverage.passed_validations` | 执行结果 | `status == "passed"` 的数量 |
| `coverage.validation_coverage.coverage_rate` | 派生 | `passed / total` |
| `context.validation_status_map` | 执行结果 | 每个 `step.id` → status |
| `context.environment.runner` | Skill 元数据 | `"harness-runtime-verify"` |
| `context.environment.verify_output_mode` | 参数 | `dual` / `schema-only` / `markdown-only` |
| `meta_evaluation.verify_confidence` | 综合评估 | 基于 `validation_status_map` 完整度 + 通过率 |

**注意**：本 Skill 不计算 `coverage.requirement_coverage` / `acceptance_coverage` / `constraint_coverage`，这些由 `harness-verify` 聚合。

---

## 约束

- **不直接修改代码**：验证 Skill 只执行命令和记录结果，修复由 Agent 或用户执行
- **安全执行**：优先使用只读命令（lint、type-check），谨慎使用副作用命令（migrate、deploy）
- **环境隔离**：尽量在隔离环境中运行测试，避免污染开发环境
- **可配置**：如 `project.yaml` 中定义了自定义验证命令，优先使用项目配置
- **快速失败**：lint 类问题优先修复，避免运行耗时测试后发现格式问题
- **Schema 合规**：YAML 输出必须 100% 符合 Verify Schema v0.2-draft 子集
- **validation_status_map 完整性**：必须包含所有 `task.validation_steps[].id`，缺失项标记为 `skipped` 并在报告中标注

---

## 验证清单

执行完成后自检：

- [ ] 项目类型已检测
- [ ] Task Schema 的 `validation_steps` 已解析
- [ ] 验证命令已执行
- [ ] 失败已分类记录（含 step_id）
- [ ] `validation_status_map` 已填充（包含所有 step.id）
- [ ] `coverage.validation_coverage` 已计算
- [ ] DoD 检查已完成（如适用）
- [ ] 如存在失败，修复请求已生成
- [ ] 如进入修复，修复后重新验证已执行
- [ ] 轮次控制已生效（不超过 3 轮）
- [ ] `runtime-report.yaml` 已生成（除非 markdown-only 模式）
- [ ] `runtime-report.yaml` 符合 Verify Schema v0.2-draft 子集
- [ ] `runtime-report.md` 已生成（除非 schema-only 模式）
- [ ] `progress.md` 已更新验证状态

---

## 返回格式

```yaml
summary:
  order_id: {{ORDER_ID}}
  output_mode: {{verify_output_mode}}
  schema_version: "v0.2-draft"
  commands:
    total: {{total}}
    passed: {{passed}}
    failed: {{failed}}
  rounds: {{rounds}}
  coverage:
    validation: 1.0
  validation_status_map:
    filled: {{filled_count}}
    total: {{total_count}}
    completeness: 1.0   # filled / total
  failures:
    total: {{total_failures}}
    resolved: {{resolved}}
    remaining: {{remaining}}
  dod_satisfied: true
  status: {{passed/verification_failed}}
  
report_paths:
  yaml: "orders/{{ORDER_ID}}/runtime-report.yaml"
  markdown: "orders/{{ORDER_ID}}/runtime-report.md"
```

---

## 示例：Runtime Report（dual 模式）

### runtime-report.yaml 示例

```yaml
---
artifact:
  id: F22-runtime-report-001
  type: report
  title: F22 通知推送系统运行时验证报告
  domain: notification
  status: active
  version: "0.1.0"
  source:
    skill: harness-runtime-verify
    feature_id: F22
    created: "2026-06-24T18:00:00+08:00"
    updated: "2026-06-24T18:00:00+08:00"
  dependencies:
    - F22-order-001
    - F22-order-002

target:
  feature_id: F22
  task_ids:
    - F22-order-001
    - F22-order-002

iteration: 1

summary:
  total_checks: 8
  passed: 7
  failed: 1
  warned: 0
  overall_status: failing

coverage:
  validation_coverage:
    total_validations: 8
    passed_validations: 7
    coverage_rate: 0.875
    status_distribution:
      passed: 7
      failed: 1
      skipped: 0
      error: 0

checks:
  - check_id: VRF-F22-RT-001
    type: validation_passed
    target_id: VAL-F22-001-001
    status: pass
    message: "validation_step VAL-F22-001-001 已通过"
    evidence:
      artifact_id: F22-order-001
      field_path: validation_steps[0]
  - check_id: VRF-F22-RT-002
    type: validation_passed
    target_id: VAL-F22-001-002
    status: fail
    message: "validation_step VAL-F22-001-002 失败：2 个测试未通过"
    severity: block
    fix_path: "运行 harness-execute F22-order-001 修复失败的测试"

failures:
  - failure_id: FAIL-F22-RT-001
    category: validation_failed
    affected_ids:
      - VAL-F22-001-002
    impact: "1 个验证步骤未通过"
    recommended_fix: "运行 harness-execute F22-order-001 修复失败的测试"
    blocking: true

context:
  environment:
    runner: harness-runtime-verify
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
  validation_status_map:
    VAL-F22-001-001: passed
    VAL-F22-001-002: failed
    VAL-F22-001-003: passed
    VAL-F22-001-004: passed
    VAL-F22-001-005: passed
    VAL-F22-002-001: passed
    VAL-F22-002-002: passed
    VAL-F22-002-003: passed

meta_evaluation:
  schema_compliance: true
  reference_integrity: true
  verify_confidence: 0.92
```

### runtime-report.md 示例（精简版）

```markdown
# F22 运行时验证报告

> 详细结构化数据见 `runtime-report.yaml`（Verify Schema v0.2-draft）

## 摘要

| 指标 | 数值 |
|------|------|
| 验证步骤数 | 8 |
| 通过 | 7 |
| 失败 | 1 |
| 修复轮次 | 1 |
| **最终状态** | ⚠️ failing |

## 覆盖度

| 覆盖率 | 值 |
|--------|---|
| 验证执行 | 87.5% (7/8) |

## validation_status_map 摘要

| Step ID | Status | 命令 |
|---------|--------|------|
| VAL-F22-001-001 | ✅ passed | `pytest tests/test_auth.py::test_login` |
| VAL-F22-001-002 | ❌ failed | `pytest tests/test_auth.py` |
| VAL-F22-001-003 | ✅ passed | `pytest tests/test_notif.py` |
| ... | ... | ... |

## 失败项

### FAIL-001：validation_failed
- **影响**：VAL-F22-001-002
- **错误**：2 个测试未通过
- **修复路径**：运行 `harness-execute F22-order-001`

## DoD 状态

| 状态 | 值 |
|------|---|
| 总条件 | 5 |
| 已勾选 | 5 |
| **全部满足** | ✅ |

## 下一步

⚠️ 1 个验证步骤失败，需修复后重新运行 `harness-runtime-verify`。

或执行 `harness-verify --mode=schema-only` 聚合所有覆盖率。
```

---

## 变更历史

- **v2.0**（2026-06-24，Phase 2.5.6）：完整对接 Verify Schema v0.2-draft
  - 引入 `verify_output_mode` 参数（dual / schema-only / markdown-only）
  - 新增 `validation_status_map` 填充机制（核心对接）
  - 新增 `coverage.validation_coverage` 自动计算
  - 新增 Task Schema `validation_steps` 解析与映射
  - 新增 DoD 自动检查（V5 规则）
  - 新增 step_id 自动生成（格式：VAL-{task_id}-{seq:03d}）
  - 保留原 3 轮修复循环逻辑
  - 保留原命令分类（lint/typing/test/build/dependency/runtime/configuration）
- **v1.0**：初始版本，仅 markdown runtime-report.md
---