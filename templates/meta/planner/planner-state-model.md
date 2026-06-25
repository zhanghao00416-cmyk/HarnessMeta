# Planner State Model

> **Phase**：4（Rule-Based Planner）
> **版本**：v1.0-draft
> **依赖**：Context Contract v1.0-frozen、Artifact Meta Schema v1.0-frozen、Verify Schema v1.0-frozen
> **原则**：不新增 Schema。所有状态字段来自已有 Frozen Schema 或已有文件。
> **职责**：定义 Planner 读取的项目状态向量。Planner 只读，不写。

---

## 1. 设计原则

1. **零新 Schema**：所有状态字段来自现有文件（`project.yaml`、`progress.md`、`session-handoff.md`、`feature_list.json`、Artifact front matter）
2. **确定性**：相同 project_state 产生相同输出
3. **可解释**：每个路由决策可追溯到具体字段
4. **只读**：Planner 不修改任何文件，不推进项目状态
5. **无 Runtime**：Planner 不执行任何 Skill，只输出建议

---

## 2. 状态向量

```yaml
project_state:
  # ── 模式检测 ──
  mode:
    description: "项目当前处于哪个流程"
    type: enum
    values: [greenfield, brownfield, adopt, unknown]
    source:
      greenfield: "project.yaml 不存在"
      brownfield: "project.yaml 存在 + features 至少一个 not_started"
      adopt: "project.yaml 存在 + 所有 features 标记 passing（由 harness-adopt-scan 设定）"
      unknown: "无法判断（缺失关键文件）"

  # ── 功能状态（来自 feature_list.json + progress.md） ──
  features:
    description: "所有功能的当前状态"
    type: array
    source: "feature_list.json + progress.md"
    items:
      id: "F22"
      status:
        type: enum
        values: [not_started, clarifying, specifying, ordered, executing, verifying, passing]
        transitions:
          not_started → clarifying: "harness-clarify 完成"
          clarifying → specifying: "harness-specify 完成"
          specifying → ordered: "harness-specify-arch 完成"
          ordered → executing: "harness-order + harness-analyze（可选）完成"
          executing → verifying: "harness-execute 完成"
          verifying → passing: "harness-verify overall_status=passing"
      domain: "notification"

  # ── 工单状态（来自 progress.md） ──
  tasks:
    description: "所有工单的当前状态"
    type: array
    source: "progress.md"
    items:
      id: "F22-order-001"
      status:
        type: enum
        values: [not_started, active, passing]
      feature_id: "F22"
      dependencies: ["F22-order-000"]  # 依赖的前序工单
      current_phase:
        description: "三段式执行的当前阶段（仅 status=active 时有效）"
        type: enum
        values: [1, 2, 3]
        source: "session-handoff.md"

  # ── Artifact 存在性（来自文件系统扫描） ──
  artifacts:
    description: "关键 Artifact 的存在性和状态"
    type: object
    source: "文件系统扫描 + Artifact front matter"
    properties:
      spec:
        exists: true | false
        ids: ["F22-specs"]
      architecture:
        exists: true | false
        ids: ["notification-architecture"]
      tasks:
        exists: true | false
        count: 12
      verify_report:
        exists: true | false
        ids: ["F22-verify-report-001"]
      context_bundle:
        exists: true | false
        ids: ["F22-order-001"]

  # ── 会话状态（来自 session-handoff.md） ──
  session:
    description: "当前会话的断点和意图"
    type: object
    source: "session-handoff.md"
    properties:
      last_skill:
        type: string
        example: "harness-specify"
      next_step:
        type: string
        example: "运行 harness-specify-arch 生成架构规格"
      pause_point:
        type: string | null
        example: "F22-order-002 阶段 2 第 234 行"
      active_task:
        type: string | null
        example: "F22-order-002"

  # ── 依赖阻塞（来自 progress.md + Task artifact dependencies） ──
  blocked_tasks:
    description: "因为依赖未完成而无法开始的任务"
    type: array
    source: "progress.md + Task artifact dependencies"
    items:
      task_id: "F22-order-003"
      blocked_by: ["F22-order-001"]  # 等待这些任务完成

  # ── 验证结果（来自 Verify Report） ──
  verify_results:
    description: "最近一次验证的结果"
    type: object | null
    source: "Verify Report（如有）"
    properties:
      overall_status: passing | failing | warning
      iteration: 1  # 验证轮次
      coverage:
        requirement_coverage: 0.92
        acceptance_coverage: 0.88
        constraint_coverage: 0.75
        validation_coverage: 1.0

  # ── 项目初始化状态（来自 project.yaml + 文件系统） ──
  initialization:
    description: "项目骨架是否就绪"
    type: object
    source: "project.yaml + 文件系统"
    properties:
      project_yaml_exists: true | false
      meta_files_exist: true | false      # AGENTS.md, ARCHITECTURE.md, progress.md, etc.
      feature_list_exists: true | false
      specs_dir_exists: true | false
      architecture_dir_exists: true | false
      orders_dir_exists: true | false
```

---

## 3. 状态来源映射

| 状态字段 | 来源文件 | Frozen Schema 引用 |
|---------|---------|-------------------|
| `mode` | 文件系统扫描 | 无（运行时判断） |
| `features[].status` | `feature_list.json` + `progress.md` | 无（meta 文件） |
| `tasks[].status` | `progress.md` | 无（meta 文件） |
| `tasks[].current_phase` | `session-handoff.md` | 无（meta 文件） |
| `artifacts.*` | 文件系统 + Artifact front matter | Artifact Meta Schema v1.0-frozen（`artifact.id`、`artifact.type`、`artifact.status`） |
| `session.last_skill` | `session-handoff.md` | Context Contract v1.0-frozen（`session.next_step`） |
| `blocked_tasks` | `progress.md` + Task dependencies | Task Schema v1.0-frozen（`task.requirement_refs`、`task.constraints`） |
| `verify_results` | Verify Report | Verify Schema v1.0-frozen（`coverage.*`、`overall_status`） |
| `initialization` | `project.yaml` + 文件系统 | 无（文件存在性检查） |

---

## 4. 状态采集流程

Planner 启动时的状态采集：

```
1. 扫描文件系统
   ├── project.yaml 存在？ → mode = brownfield/adopt/greenfield
   ├── feature_list.json 存在？ → 解析功能状态
   ├── progress.md 存在？ → 解析任务状态 + 阻塞关系
   ├── session-handoff.md 存在？ → 解析会话状态
   ├── docs/specs/ 存在？ → 解析 Spec artifacts
   ├── docs/architecture/ 存在？ → 解析 Architecture artifacts
   ├── orders/ 存在？ → 解析 Task artifacts
   └── docs/verify/ 存在？ → 解析 Verify Reports

2. 构建状态向量
   ├── mode（从初始化状态推断）
   ├── features（从 feature_list.json + progress.md）
   ├── tasks（从 progress.md）
   ├── artifacts（从文件系统扫描）
   ├── session（从 session-handoff.md）
   ├── blocked_tasks（从 progress.md + Task dependencies）
   ├── verify_results（从 Verify Report）
   └── initialization（从文件存在性）

3. 输入 Planner 路由引擎 → 输出 next_skill 或 execution_plan
```

---

## 5. 状态有效性校验

Planner 在路由前检查状态是否一致：

| 校验规则 | 不满足时的行为 |
|---------|-------------|
| `feature_list.json` 中的状态与 `progress.md` 一致 | 以 `progress.md` 为准，warn |
| Task 的 `status=active` 但 `session.active_task != task.id` | 以 `session-handoff.md` 为准 |
| Task 的 `status=passing` 但没有对应的 Verify Report | warn（可能漏了验证） |
| Session 的 `last_skill` 与 `progress.md` 记录不一致 | 以 `session-handoff.md` 为准 |

---

## 6. 与 Frozen Schema 的关系

```
Context Contract v1.0-frozen
    └── session.next_step →  Planner 读取"用户意图"

Artifact Meta Schema v1.0-frozen
    └── artifact.status →  Planner 读取"产物状态"

Task Schema v1.0-frozen
    └── task.requirement_refs →  Planner 读取"追踪关系"（判断依赖）

Verify Schema v1.0-frozen
    └── coverage.* →  Planner 读取"验证结果"（判断是否可归档）
```

**Planner 不定义任何新 Schema**。所有状态字段引用已冻结的协议。

---

> **v1.0-draft（2026-06-25）**：初始版本，定义 Planner 的完整状态向量和采集流程。
