---
name: harness-context
description: 上下文自动构建器。输入 task_id，自动遍历 Frozen Schema 引用链（V1 requirement_refs → V2 acceptance_criteria_ids → V3 constraint_refs），聚合 Spec/Architecture/Task/Verify/Project State，生成 context_bundle.yaml 供 Agent 消费。只读，不修改代码。v2.0 引入 P0 Builder / P1 Resolver / P2 Budget 三组件架构。
---

# harness-context：上下文自动构建器（Context Builder）

> **版本**：v2.0（Phase 3 Context Engine）
> **前身**：v1.x（手工打包上下文）
> **核心改进**：从"手工指定 file_list"升级为"自动遍历 Frozen Schema 引用链"

## 触发条件

以下场景执行：

1. **工单执行前**：`harness-execute` 阶段 1 之前，自动执行本 Skill 生成上下文
2. **分析阶段后**：`harness-analyze` 完成后，为待执行工单打包上下文
3. **用户主动要求**：用户说"准备执行上下文"、"打包上下文"或"构建 Context Bundle"
4. **上下文过期**：项目结构或规格文档发生重大变化后，原有 context_bundle.yaml 已过时

## 输入

- `task_id`（**v2.0 新增，P0 输入**）：工单 ID，如 `F22-order-001`。Skill 自动定位 Task artifact 文件
- `project.yaml`（必须存在）：项目级配置
- `progress.md`（必须存在）：项目进度

> **v2.0 变更**：不再需要手工指定 `file_list`、`api_contract`、`reference_module`。P1 Resolver 自动从 Task artifact 的 Frozen Schema 引用链（V1/V2/V3）推导所有相关上下文。

## 输出

生成：

```text
orders/<TASK_ID>/context_bundle.yaml   # v2.0 主输出：结构化上下文（Agent 可直接消费）
orders/<TASK_ID>/context.md            # v1.x 兼容输出：人类可读版
```

更新：

- `progress.md`：记录上下文构建状态

> **v2.0 变更**：`context_bundle.yaml` 是主输出。`context.md` 保留用于人类阅读和 v1.x 兼容。

---

## 步骤

### 0. 前置检查

确认以下文件存在：

- [ ] `project.yaml`
- [ ] `progress.md`
- [ ] Task artifact（`orders/<TASK_ID>/order.md` 或等价位置）

如 task_id 对应的文件不存在，报错退出。

---

### 1. 读取 Task Artifact（P1 Resolver 入口）

从 `orders/<TASK_ID>/order.md`（或从 `progress.md` 推断路径）读取 Task artifact。

提取三个关键引用字段：

```yaml
# 从 Task artifact 提取
task:
  id: "F22-order-001"
  title: "..."
  description: "..."
  feature_id: "F22"
  domain: "notification"
  dependencies: ["F22-specs", "notification-architecture"]

  requirement_refs:             # V1 路径
    - requirement_id: "REQ-NOT-001"
    - requirement_id: "REQ-NOT-002"

  constraints:                   # V3 路径
    constraint_refs: ["CON-NOT-001"]

  validation_steps:             # V2 路径
    - id: "VAL-F22-001-001"
      type: "unit_test"
      command: "pytest tests/test_notification.py::test_send_email -v"
      acceptance_criteria_ids: ["AC-NOT-001"]
```

**关键原则**：只使用 Task Schema v1.0-frozen 中已定义的字段。如 Task artifact 使用旧格式（无 `requirement_refs[]` 等），降级到 v1.x 手工模式。

---

### 2. P1 Resolver：解析 Requirements（V1 路径）

遍历 `task.requirement_refs[].requirement_id`，从 Spec artifact 加载完整 requirement。

**算法**：

```
输入：task（从步骤 1 提取）
输出：requirements[], resolve_trace[]

for each ref in task.requirement_refs:
  1. 从 task.dependencies 找到 spec artifact（如 "F22-specs"）
  2. 定位 spec 文件：docs/specs/{domain}/spec.md
  3. 在 spec 中搜索 ref.requirement_id（如 "REQ-NOT-001"）
  4. 提取完整 requirement：
     - id, title, description
     - scenarios[]（含嵌套 acceptance_criteria[]）
     - priority, status
  5. 记录 resolve_trace：
     { source: "task.requirement_refs[0].requirement_id",
       target: "spec.requirements.REQ-NOT-001",
       status: "resolved", artifact: "F22-specs" }

如果 requirement_id 在 spec 中不存在：
  记录 resolve_trace.status = "broken_ref"
  跳过该条（不阻塞流程）
```

**去重**：同一个 requirement 只保留一份（按 id 去重）。

---

### 3. P1 Resolver：解析 Acceptance Criteria（V2 路径）

遍历 `task.validation_steps[].acceptance_criteria_ids[]`，从 Spec artifact 加载完整 AC。

**算法**：

```
输入：task（从步骤 1 提取）
输出：acceptance_criteria[], resolve_trace[]

for each step in task.validation_steps:
  for each ac_id in step.acceptance_criteria_ids:
    1. 从 task.dependencies 找到 spec artifact
    2. 定位 spec 文件
    3. 在 spec 中搜索 ac_id（如 "AC-NOT-001"）
       - 优先：spec.acceptance_criteria[]（全局 AC 列表）
       - 其次：spec.requirements[].scenarios[].acceptance_criteria[]（嵌套 AC）
    4. 提取 AC：id, description, expected_outcome（如有）
    5. 记录 covered_by_steps（被哪些 validation_step 引用）
    6. 记录 resolve_trace

如果 ac_id 在 spec 中不存在：
  记录 resolve_trace.status = "broken_ref"
  跳过该条
```

**去重**：同一个 AC 只保留一份，但合并 covered_by_steps。

---

### 4. P1 Resolver：解析 Constraints（V3 路径）

遍历 `task.constraints.constraint_refs[]`，从 Architecture artifact 加载完整 constraint。

**算法**：

```
输入：task（从步骤 1 提取）
输出：constraints[], resolve_trace[]

for each con_id in task.constraints.constraint_refs:
  1. 从 task.dependencies 找到 architecture artifact
  2. 定位 architecture 文件：docs/architecture/{domain}/architecture.yaml
  3. 在架构文件中搜索 con_id（如 "CON-NOT-001"）
  4. 提取 constraint：
     - id, description, severity（must/should/may）
     - related_modules[], related_requirements[]
  5. 记录 resolve_trace

如果 con_id 在 architecture 中不存在：
  记录 resolve_trace.status = "broken_ref"
  跳过该条
```

**注意**：如果 Task 的 `constraints.constraint_refs[]` 为空，跳过本步骤，不报错。

---

### 5. 加载项目状态与记忆

从以下文件加载非引用链的上下文：

```yaml
# 从 project.yaml
project_state:
  name: "{{context.project.name}}"
  stack:
    backend: "{{context.project.stack.backend}}"
    database: "{{context.project.stack.database}}"
  verify_commands:
    health_check: "{{context.project.verify_commands.health_check}}"

# 从 ARCHITECTURE.md（如果存在）
project_state:
  architecture_rules:
    - "Service 层负责业务逻辑，不得直接操作数据库"
    - "所有 API 返回标准 JSON 格式"

# 从 progress.md
project_state:
  active_orders: ["F22-order-001", "F22-order-002"]

# 从 session-handoff.md（如果存在）
project_state:
  session:
    next_step: "继续执行 F22-order-001 阶段 2"
    pause_point: "..."

# 从 docs/memory/ 或 harness-project-memory 输出（如果存在）
memory:
  adr:
    - id: "ADR-001"
      title: "..."
      decision: "..."
  conventions:
    - "使用 Repository Pattern 访问数据库"
    - "错误码必须注册到 ERROR_CODE.md"
```

**加载策略**：优先加载，不强制存在。如果 ADR / Memory 目录不存在，跳过不报错。

---

### 6. P2 Budget：上下文大小控制

**预算模型**：

```yaml
max_tokens: 30000
reserve_tokens: 5000       # 留给 Agent 响应
available_tokens: 25000
```

**计算当前使用量**：

```
used_tokens ≈ context_bundle_yaml_byte_count / 4
```

**裁减优先级**（从低到高）：

| 优先级 | 内容 | 裁减策略 |
|--------|------|---------|
| **P2（先裁）** | memory.adr[], memory.conventions[] | 逐条删除，保留最近的 ADR |
| **P2** | project_state.architecture_rules[] | 逐条删除，保留架构核心原则 |
| **P1** | acceptance_criteria[].description | 截断到 200 字符 |
| **P1** | requirements[].scenarios[].description | 截断到 300 字符 |
| **P0（最后裁）** | task.description, requirements[].description | 截断到 500 字符 |

**裁减算法**：

```
while estimated_tokens > available_tokens:
  1. 按优先级从 P2 → P1 → P0 逐层裁减
  2. 每次裁减后重新估算
  3. 如果 P0 仍超限：报 warn（上下文可能不完整）
  4. 记录所有裁减项到 budget.truncated[]
```

**记录格式**：

```yaml
budget:
  max_tokens: 30000
  used_tokens: 28500
  reserve_tokens: 5000
  utilization: 0.95
  truncated:
    - section: "memory.adr"
      item: "ADR-003"
      reason: "超出预算（P2 优先级）"
```

---

### 7. P0 Builder：生成 context_bundle.yaml

将步骤 1-6 的结果组装为结构化上下文。

**完整结构**（详见 `docs/governance/phase3-context-engine.md` §3.1）：

```yaml
context_bundle:
  meta:
    task_id: "F22-order-001"
    generated_at: "2026-06-24T18:00:00+08:00"
    version: "2.0"
    source_skill: "harness-context"

  task: {...}                    # 步骤 1
  requirements: [...]            # 步骤 2（P1 Resolved）
  acceptance_criteria: [...]     # 步骤 3（P1 Resolved）
  constraints: [...]             # 步骤 4（P1 Resolved）
  validation_steps: [...]        # 步骤 1（从 Task 直接取）

  project_state: {...}           # 步骤 5
  memory: {...}                  # 步骤 5

  budget: {...}                  # 步骤 6（P2 Budget）
  resolve_trace: [...]           # 步骤 2-4 汇总
```

**字段命名约束**：所有 coverage 相关字段必须使用 Verify Schema v1.0-frozen 中定义的命名（`requirement_coverage` / `acceptance_coverage` / `constraint_coverage` / `validation_coverage`）。

---

### 8. 生成 context.md（人类可读版，v1.x 兼容）

保留 v1.x 的 context.md 格式，供人类阅读：

```markdown
# Context Bundle: {{task.id}} - {{task.title}}

生成时间：{{generated_at}}
版本：v2.0（Context Builder）

---

## Task

{{task.description}}

## Requirements（V1 路径，{{requirement_count}} 条）

{{#each requirements}}
### {{this.id}}：{{this.title}}

{{this.description}}

{{#if this.scenarios.length > 0}}
**场景**：
{{#each this.scenarios}}
- {{this.description}}
{{/each}}
{{/if}}
{{/each}}

## Acceptance Criteria（V2 路径，{{ac_count}} 条）

| ID | 描述 | 覆盖步骤 |
|----|------|---------|
{{#each acceptance_criteria}}
| {{this.id}} | {{this.description}} | {{this.covered_by_steps}} |
{{/each}}

## Constraints（V3 路径，{{constraint_count}} 条）

{{#each constraints}}
- **[{{this.severity}}]** {{this.id}}：{{this.description}}
{{/each}}

## Validation Steps

{{#each validation_steps}}
1. **{{this.id}}**（{{this.type}}）
   - 命令：`{{this.command}}`
   - 覆盖 AC：{{this.acceptance_criteria_ids}}
{{/each}}

## Budget

- 使用 token：{{used_tokens}} / {{available_tokens}}（利用率 {{utilization}}%）
{{#if truncated.length > 0}}
- 裁减项：{{truncated.length}} 条
{{/if}}

## Resolve Trace（审计）

| 来源 | 目标 | 状态 |
|------|------|------|
{{#each resolve_trace}}
| {{this.source}} | {{this.target}} | {{this.status}} |
{{/each}}
```

---

### 9. 更新项目状态

更新 `progress.md`：

```markdown
### 上下文构建完成
- 工单：{{task.id}}
- 生成文件：orders/{{task.id}}/context_bundle.yaml
- Token 使用：{{used_tokens}} / {{available_tokens}}
- 解析状态：{{resolved_count}}/{{total_refs}} 成功
```

---

## 约束

- **只读**：禁止修改任何源代码或文档文件
- **不生成代码**：仅收集和整理信息
- **路径相对化**：所有路径使用相对路径（相对于项目根目录）
- **Frozen Schema 只读**：只读取 Spec/Task/Architecture/Verify Schema，不修改
- **兼容降级**：如 Task artifact 使用旧格式（无结构化引用），降级到 v1.x 手工模式
- **可复用**：如 context_bundle.yaml 已存在且项目未变化，可复用（向用户确认）
- **broken_ref 不阻塞**：引用断裂时记录 resolve_trace，不阻断流程

---

## 验证清单

执行完成后自检：

**P1 Resolver 验证**：
- [ ] 所有 `requirement_refs` 已解析（V1 路径）
- [ ] 所有 `acceptance_criteria_ids` 已解析（V2 路径）
- [ ] 所有 `constraint_refs` 已解析（V3 路径）
- [ ] 引用断裂的 ref 已在 resolve_trace 中记录

**P0 Builder 验证**：
- [ ] `orders/<TASK_ID>/context_bundle.yaml` 已生成
- [ ] `orders/<TASK_ID>/context.md` 已生成
- [ ] context_bundle 结构完整（task / requirements / acceptance_criteria / constraints / validation_steps）
- [ ] 字段命名与 Verify Schema v1.0-frozen 一致

**P2 Budget 验证**：
- [ ] context_bundle 估算 token ≤ available_tokens
- [ ] 如有裁减，budget.truncated 已记录

**通用验证**：
- [ ] `progress.md` 已更新
- [ ] 未修改任何 Frozen Schema

---

## 返回格式

```markdown
## Context Bundle 构建完成

- 工单：{{task.id}} - {{task.title}}
- 域：{{task.domain}}
- 输出：
  - `orders/{{task.id}}/context_bundle.yaml`（结构化）
  - `orders/{{task.id}}/context.md`（人类可读）

### P1 解析统计
| 路径 | 总数 | 成功 | 断裂 | 覆盖率 |
|------|------|------|------|--------|
| V1 requirement_refs | {{v1_total}} | {{v1_resolved}} | {{v1_broken}} | {{v1_rate}}% |
| V2 acceptance_criteria_ids | {{v2_total}} | {{v2_resolved}} | {{v2_broken}} | {{v2_rate}}% |
| V3 constraint_refs | {{v3_total}} | {{v3_resolved}} | {{v3_broken}} | {{v3_rate}}% |

### P2 Budget
- 使用 token：{{used_tokens}} / {{available_tokens}}（利用率 {{utilization}}%）
{{#if truncated}}
- 裁减项：{{truncated.length}} 条
{{/if}}

### 注意事项
{{#if v1_broken > 0}}
- ⚠️ V1 路径有 {{v1_broken}} 条引用断裂，Agent 可能缺少部分 Requirement 上下文
{{/if}}
{{#if v2_broken > 0}}
- ⚠️ V2 路径有 {{v2_broken}} 条引用断裂，Agent 可能缺少部分 AC 上下文
{{/if}}
{{#if truncated}}
- ⚠️ 上下文已裁减，详见 `budget.truncated`
{{/if}}
{{#if notes}}
- {{notes}}
{{/if}}
```

---

## 变更历史

- **v2.0**（2026-06-24，Phase 3 Context Engine）：
  - **核心改进**：从"手工指定 file_list"升级为"自动遍历 Frozen Schema 引用链"
  - 引入 P0 Builder（context_bundle.yaml 结构化输出）
  - 引入 P1 Resolver（V1 requirement_refs → V2 acceptance_criteria_ids → V3 constraint_refs 自动解析）
  - 引入 P2 Budget（优先级裁减 + resolve_trace 审计）
  - 输入简化为 task_id（单一入口）
  - 保留 context.md 人类可读版（v1.x 兼容）
  - 详见 `docs/governance/phase3-context-engine.md`
- **v1.0**：初始版本，手工指定 file_list 和约束
