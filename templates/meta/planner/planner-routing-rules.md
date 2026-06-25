# Planner Routing Rules

> **Phase**：4（Rule-Based Planner）
> **版本**：v1.0-draft
> **依赖**：planner-state-model.md
> **原则**：基于 Frozen Protocol，不新增 Schema。确定性规则，无随机性。

---

## 1. 路由引擎架构

```
project_state（来自 planner-state-model.md）
    │
    ▼
┌─────────────────────────────┐
│ R1：模式检测                  │
│ greenfield / brownfield      │
│ / adopt / unknown            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ R2：流程链定位               │
│ 找到当前在 A/B/C 流程的      │
│ 哪个位置                     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ R3：前置条件检查             │
│ 下一个 Skill 的前置条件      │
│ 是否满足？                   │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ R4：决策输出                 │
│ next_skill                   │
│ 或 execution_plan            │
└─────────────────────────────┘
```

---

## 2. R1：模式检测

### 2.1 检测规则

```
如果 project.yaml 不存在：
    → mode = greenfield
    → next_skill = harness-init

如果 project.yaml 存在：
    如果 所有 features.status == "passing"：
        → mode = adopt
    如果 存在 features.status != "passing"：
        → mode = brownfield

如果 progress.md 或 feature_list.json 缺失：
    → mode = unknown
    → next_skill = harness-init（重建骨架）
```

### 2.2 三种模式的 Skill 链

**Flow A（Greenfield）**：
```
harness-init
    → harness-init-docs
    → harness-clarify
    → harness-specify
    → harness-specify-arch
    → harness-order
    → [harness-analyze]       ← 可选（建议）
    → [harness-context]       ← 可选（但建议在 execute 前）
    → harness-execute
    → [harness-review-loop]   ← 可选
    → [harness-runtime-verify] ← 可选
    → harness-verify
    → [harness-project-memory] ← 可选
    → harness-archive
```

**Flow B（Brownfield）**：
```
[harness-explore]            ← 可选
    → harness-change
    → harness-apply
    → [harness-review-loop]   ← 可选
    → [harness-runtime-verify] ← 可选
    → harness-verify
    → [harness-project-memory] ← 可选
    → harness-archive
```

**Flow C（Adopt）**：
```
harness-adopt-scan
    → [harness-context-index] ← 可选（建议）
    → harness-adopt-spec
    → 后续改代码走 Flow B
```

### 2.3 可选 vs 必选

| Skill | 必选/可选 | 条件 |
|-------|----------|------|
| harness-init | 必选 | mode=greenfield，project.yaml 不存在 |
| harness-init-docs | 必选 | harness-init 完成 |
| harness-clarify | 必选 | 至少一个 feature 状态 = not_started |
| harness-specify | 必选 | 至少一个 feature 状态 = clarifying |
| harness-specify-arch | 必选 | 至少一个 feature 状态 = specifying |
| harness-order | 必选 | 至少一个 feature 状态 = ordered 的前置（specifying done） |
| harness-analyze | 可选 | harness-order 完成。**建议**：发现 coverage < 0.8 时推荐 |
| harness-context | 建议 | harness-order 完成 + 有待执行 task |
| harness-execute | 必选 | 有待执行 task（status=active） |
| harness-review-loop | 可选 | harness-execute 完成。**建议**：首次执行或代码量大 |
| harness-runtime-verify | 可选 | harness-execute 完成。**建议**：有 validation_steps 且 command 非空 |
| harness-verify | 必选 | harness-execute 完成 |
| harness-project-memory | 可选 | harness-verify passing。**建议**：每完成一个 feature 运行一次 |
| harness-archive | 必选 | harness-verify passing |
| harness-explore | 可选 | mode=brownfield，用户不确定需求 |
| harness-change | 必选 | mode=brownfield，有待变更 |
| harness-apply | 必选 | harness-change 完成 |
| harness-adopt-scan | 必选 | mode=adopt |
| harness-context-index | 建议 | harness-adopt-scan 完成 |
| harness-adopt-spec | 必选 | harness-adopt-scan 完成 |

---

## 3. R2：流程链定位

### 3.1 定位算法

```
输入：project_state
输出：current_position（在 Flow A/B/C 中的位置）

算法：
  1. 找到 "最后完成的必选 Skill"
     = max(已完成的必选 Skill 在流程链中的位置)

  2. 如果 session.next_step 明确指定了 Skill：
     优先使用 session 的意图

  3. 如果有 task.status = active：
     定位到执行链（harness-execute / harness-apply）
```

### 3.2 Flow A 定位表

| 条件 | current_position |
|------|-----------------|
| `initialization.project_yaml_exists == false` | 0（需要 harness-init） |
| `initialization.meta_files_exist == false` | 1（需要 harness-init-docs） |
| 至少一个 feature.status = not_started，但无 spec | 2（需要 harness-clarify） |
| 至少一个 feature.status = clarifying | 3（需要 harness-specify） |
| 至少一个 feature.status = specifying | 4（需要 harness-specify-arch） |
| 至少一个 feature.status = ordered | 5（需要 harness-order） |
| 有待执行 task（status=active）+ 无 context_bundle | 6（建议 harness-context） |
| 有待执行 task（status=active） | 7（需要 harness-execute） |
| task.status = active，但已执行（phase 3 done） | 8（建议 harness-review-loop） |
| task 已执行 + 有 validation_steps | 9（建议 harness-runtime-verify） |
| task 已执行 | 10（需要 harness-verify） |
| verify.overall_status = passing | 11（建议 harness-project-memory） |
| verify.overall_status = passing（所有 feature 完成） | 12（需要 harness-archive） |

### 3.3 Flow B 定位表

| 条件 | current_position |
|------|-----------------|
| 有变更意图但未创建变更 | 0（需要 harness-explore，可选） |
| 无活跃变更文件夹 | 1（需要 harness-change） |
| 有待实现的变更任务 | 2（需要 harness-apply） |
| 变更已实现 | 3（建议 harness-review-loop） |
| 变更已实现 + 有 tests | 4（建议 harness-runtime-verify） |
| 变更已实现 | 5（需要 harness-verify） |
| verify.passing | 6（需要 harness-archive） |

---

## 4. R3：前置条件检查

### 4.1 每 Skill 的前置条件

```yaml
harness-init:
  prerequisites: []  # 无前置条件，始终可运行
  blocks_if: "project.yaml 已存在"  # 如果 project.yaml 已存在，应走 brownfield

harness-init-docs:
  prerequisites:
    - "project.yaml 存在"
    - "harness-init 已完成（meta 文件已生成）"

harness-clarify:
  prerequisites:
    - "feature_list.json 存在"
    - "至少一个 feature.status = not_started"
  blocks_if: "所有 feature 都已 clarifying 或更高"

harness-specify:
  prerequisites:
    - "至少一个 feature.status = clarifying"
    - "feature 的 behavior 已填写（clarify 完成）"

harness-specify-arch:
  prerequisites:
    - "至少一个 feature.status = specifying"
    - "spec 文件存在（如 docs/specs/notification/spec.md）"

harness-order:
  prerequisites:
    - "至少一个 feature.status = ordered 的前置（specifying done）"
    - "spec 文件存在"
    - "architecture 文件存在"

harness-analyze:
  prerequisites:
    - "harness-order 已完成"
    - "至少一个 task 存在"

harness-context:
  prerequisites:
    - "task_id 存在（有待执行 task）"
    - "task.status = active"

harness-execute:
  prerequisites:
    - "task.status = active"
    - "task.phase = 1（或未开始）"
  recommendation: "执行前建议运行 harness-context"

harness-review-loop:
  prerequisites:
    - "harness-execute 完成"
    - "task.phase = 3（自审完成）"

harness-runtime-verify:
  prerequisites:
    - "harness-execute 完成"
    - "task.validation_steps 非空"

harness-verify:
  prerequisites:
    - "harness-execute 完成"
    - "spec 文件存在"
    - "architecture 文件存在"

harness-project-memory:
  prerequisites:
    - "harness-verify overall_status = passing"

harness-archive:
  prerequisites:
    - "harness-verify overall_status = passing"
    - "所有 feature.status = passing（或当前 feature 完成）"

# Flow B
harness-explore:
  prerequisites: []  # 始终可运行

harness-change:
  prerequisites:
    - "project.yaml 存在"

harness-apply:
  prerequisites:
    - "harness-change 完成"
    - "变更文件夹存在（含 tasks.md）"

# Flow C
harness-adopt-scan:
  prerequisites: []  # 始终可运行

harness-context-index:
  prerequisites:
    - "项目目录存在"

harness-adopt-spec:
  prerequisites:
    - "harness-adopt-scan 完成"
    - "project.yaml 存在"
```

### 4.2 前置条件不满足时的处理

| 不满足条件 | Planner 行为 |
|-----------|------------|
| 前置 Skill 未完成 | 推荐前置 Skill（而非当前 Skill） |
| 必选 Skill 被跳过 | 推荐被跳过的 Skill（阻塞下游） |
| 依赖的 Task 未完成 | 推荐完成依赖 Task 的 harness-execute |
| Artifact 缺失（如 spec 文件丢失） | 推荐生成该 Artifact 的 Skill |
| 状态不一致（如 progress 和 session 冲突） | 以 session-handoff.md 为准，输出 warn |

---

## 5. R4：决策输出

### 5.1 单 Skill 输出（默认）

```yaml
decision:
  next_skill: "harness-specify"
  reason: "F22 功能状态 = clarifying，需要生成 spec"
  prerequisites_met: true
  warnings: []
```

### 5.2 执行计划输出（多 Skill）

```yaml
decision:
  execution_plan:
    - skill: "harness-context"
      reason: "为 F22-order-001 构建上下文"
      optional: false
    - skill: "harness-execute"
      reason: "执行 F22-order-001"
      optional: false
    - skill: "harness-review-loop"
      reason: "首次执行建议审查"
      optional: true
    - skill: "harness-verify"
      reason: "验证 F22-order-001 实现"
      optional: false
  warnings: []
```

### 5.3 阻塞输出

```yaml
decision:
  blocked: true
  reason: "F22-order-003 依赖 F22-order-001 完成，但 F22-order-001 status=active"
  next_skill: "harness-execute"
  target_task: "F22-order-001"
```

---

## 6. 决策树（完整）

```
Planner(project_state):

  # R1：模式检测
  if project_state.mode == "greenfield":
      return route_greenfield(project_state)
  elif project_state.mode == "brownfield":
      return route_brownfield(project_state)
  elif project_state.mode == "adopt":
      return route_adopt(project_state)
  else:
      return { next_skill: "harness-init", reason: "未知模式，初始化项目" }


route_greenfield(state):
  # 按 Flow A 顺序检查
  for skill in Flow_A_chain:
      if not prerequisites_met(skill, state):
          return { next_skill: skill.prerequisite, reason: ... }
      if skill_completed(skill, state):
          continue  # 已完成，检查下一个
      if skill_optional(skill) and not skill_recommended(skill, state):
          continue  # 可选且不推荐，跳过
      return { next_skill: skill, reason: ... }

  # 所有 Skill 完成
  return { done: true }


route_brownfield(state):
  # 有活跃工单？
  if state.tasks.any(t => t.status == "active"):
      # 回到执行链
      return route_execution_chain(state)
  # 有待归档的变更？
  if state.artifacts.verify_report.exists and state.verify_results.overall_status == "passing":
      return { next_skill: "harness-archive" }
  # 有待创建变更？
  return { next_skill: "harness-change" }
```

---

## 7. 可选 Skill 推荐规则

| 可选 Skill | 推荐条件 |
|-----------|---------|
| harness-analyze | `coverage.* < 0.8` 或首次生成工单 |
| harness-context | 任何 task.status = active |
| harness-review-loop | 首次执行或代码量 > 200 行 |
| harness-runtime-verify | task.validation_steps 非空且 command 非空 |
| harness-project-memory | feature 刚完成（status 刚变为 passing） |
| harness-explore | 用户表示"不确定"或"需要了解现有实现" |
| harness-context-index | 项目文件 > 50 个且无索引 |

---

> **v1.0-draft（2026-06-25）**：初始版本。定义 4 层路由规则（模式检测 → 链定位 → 前置条件 → 决策输出）。
