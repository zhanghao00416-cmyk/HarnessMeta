# AI 会话协议与 Agent 体系

> 所有 AI 助手在操作本项目时必须遵守此协议。
> 不绑定特定 AI 工具，任何 LLM 均可使用。
> 本协议同时定义了 Skill 编排器与 Agent 的协作方式。

---

## 0. 启动顺序

每次新会话开始时，按以下顺序读取上下文：

1. 读取本文件（`AGENTS.md`）
2. 读取 `QUICK_REFERENCE.md`（速查卡）
3. 读取 `ARCHITECTURE.md`（架构约束）
4. 读取 `progress.md`（当前进度）
5. 读取 `session-handoff.md`（会话交接）
6. 读取 `templates/context-schema.yaml`（统一上下文协议）

读取完毕后，输出：
- 当前活跃工单（如有）
- 上次会话的暂停点（如有）
- 建议的下一步操作

---

## Context Contract（统一上下文协议）

### 什么是 Context Contract

所有 Skill 和 Agent 在操作本项目时，必须使用**统一的上下文协议**访问项目信息。

`templates/context-schema.yaml` 定义了标准化的变量层级结构：

```yaml
context:
  project:      # 项目级信息（名称、技术栈、部署配置）
  feature:      # 功能级信息（ID、名称、域、依赖）
  task:         # 任务级信息（工单 ID、描述、状态）
  architecture: # 架构级信息（原则、规则、分层）
  constraints:  # 约束级信息（错误码、API 契约、域映射）
  memory:       # 记忆级信息（架构决策、项目约定、经验教训）
  session:      # 会话级信息（活跃工单、暂停点、下一步）
  change_management: # 变更管理配置
```

### 使用规则

| 规则 | 说明 | 示例 |
|------|------|------|
| **必须使用 context 路径** | 禁止直接使用旧变量名 | ✅ `{{context.project.name}}` ❌ `{{project_name}}` |
| **先注册后使用** | 新增变量必须在 `context-schema.yaml` 注册 | 见文件注释 |
| **按层级访问** | 变量必须按层级访问，禁止跳跃 | ✅ `{{context.project.stack.database}}` ❌ `{{database}}` |
| **来源可追溯** | 每个变量都有 source 字段标明数据来源 | 便于 Context Builder 自动填充 |
| **禁止使用已废弃字段** | 标记 `deprecated: true` 的字段不可使用 | ❌ `{{context.feature.title}}` → ✅ `{{context.feature.name}}` |

### 旧变量迁移对照

| 旧变量（禁止） | 新路径（推荐） | 说明 |
|----------------|----------------|------|
| `{{project_name}}` | `{{context.project.name}}` | 项目名称 |
| `{{project_description}}` | `{{context.project.description}}` | 项目描述 |
| `{{feature_name}}` | `{{context.feature.name}}` | 功能名称 |
| `{{feature_id}}` | `{{context.feature.id}}` | 功能编号 |
| `{{domain}}` | `{{context.feature.domain}}` | 业务域 |
| `{{task_id}}` | `{{context.task.id}}` | 工单编号 |
| `{{task_description}}` | `{{context.task.description}}` | 任务描述 |
| `{{verify_command}}` | `{{context.project.verify_commands.health_check}}` | 验证命令 |
| `{{health_check_command}}` | `{{context.project.verify_commands.health_check}}` | 健康检查 |
| `{{architecture_rules}}` | `{{context.architecture.rules}}` | 架构规则 |
| `{{active_orders}}` | `{{context.session.active_orders}}` | 活跃工单 |
| `{{next_step}}` | `{{context.session.next_step}}` | 下一步操作 |
| `{{feature_title}}` | `{{context.feature.name}}` | 功能标题 → 统一使用 `name` |

> **注意**：模板文件（`templates/` 下的 `.md` 文件）中的旧变量将逐步迁移。在迁移完成前，Skill 调用模板时应通过 Context Builder 自动映射。

---

## Frozen Schema 与 Schema Change Policy

### 什么是 Frozen Schema

Phase 2 已于 2026-06-24 完成 Schema 冻结，Phase 2.5 已于 2026-06-24 完成 Verify Schema 冻结：

| Schema | 文件路径 | 版本 | 阶段 |
|--------|----------|------|------|
| Context Contract | `templates/context-schema.yaml` | v1.0-frozen | Phase 1 |
| Artifact Meta Schema | `templates/meta/artifact-meta-schema.yaml` | v1.0-frozen | Phase 2 |
| Spec Schema | `templates/meta/spec-schema.yaml` | v1.0-frozen | Phase 2 |
| Task Schema | `templates/meta/task-schema.yaml` | v1.0-frozen | Phase 2 |
| Architecture Schema | `templates/meta/architecture-schema.yaml` | v1.0-frozen | Phase 2 |
| **Verify Schema** | `templates/meta/verify-schema.yaml` | **v1.0-frozen** | **Phase 2.5** |

详见 `docs/governance/phase2-freeze-declaration.md` 与 `docs/governance/phase2.5-freeze-declaration.md`（harness-meta 仓库内，不复制到用户项目）。

### 严禁直接修改 Frozen Schema

| 行为 | 状态 | 处理方式 |
|------|------|----------|
| 修改 Frozen Schema 字段定义 | ❌ 严禁 | 走 Schema Change Policy |
| 修改字段语义但不升级版本号 | ❌ 严禁（语义漂移） | 视为 MAJOR 违规 |
| 修改 ID 格式（如 `REQ-NTO-001`） | ❌ 严禁 | 视为破坏性变更 |
| 绕过 Schema 校验机制 | ❌ 严禁 | 视为破坏性变更 |
| 在 Skill 中使用未注册的 `context.*` 变量 | ❌ 严禁 | 必须先在 Context Schema 注册 |

### Schema 变更必须遵循的流程

任何 Schema 修改必须遵循 `templates/meta/schema-change-policy.md`：

```
需要修改 Schema 字段
    ↓
是否修改字段的 type / format / required / enum 含义？
    ├── 否 → PATCH（v1.0.x）
    │         单人 review 即可
    │
    └── 是 → 是否删除字段或破坏既有 Artifact？
              ├── 否 → MINOR（v1.x.0）
              │         提交提案 + 维护者 review
              │
              └── 是 → MAJOR（vx.0.0）
                        RFC + 社区讨论（≥7 天）+ 投票
```

### Skill 与 Frozen Schema 的关系

所有 Skill 必须：

- **只使用 Frozen Schema 中已定义的字段**
- **不依赖字段的具体顺序**
- **容忍可选字段缺失**
- **对未知字段采取忽略策略**（forward compatibility）

### Schema 变更后 Skill 更新责任

| 变更类型 | Skill 更新要求 |
|----------|----------------|
| PATCH（v1.0.x） | 不强制 |
| MINOR（v1.x.0） | 建议更新（但不强制） |
| MAJOR（vx.0.0） | **必须更新**，否则视为不兼容 |

### 例外情况

紧急安全修复（如发现 ID 校验漏洞）可走快速通道：

1. 维护者直接发布 PATCH 版本
2. 在 CHANGELOG 中标注 `[SECURITY]`
3. 24 小时内通知所有依赖方

---

## Artifact Chain 引用规则

所有 Skill 生成的 Artifact 必须遵守以下引用规则：

### 引用完整性

跨 Artifact 引用必须通过**结构化 ID**实现，禁止使用自由文本关联：

| 引用关系 | 引用字段 | 目标 |
|----------|----------|------|
| Task → Spec 需求 | `requirement_refs[].requirement_id` | `Spec.requirements[].id` |
| Task → Spec 场景 | `requirement_refs[].scenario_ids[]` | `Spec.scenarios[].id` |
| Task → Spec 验收标准 | `validation_steps[].acceptance_criteria_ids[]` | `Spec.acceptance_criteria[].id` |
| Task → Architecture 约束 | `constraints.constraint_refs[]` | `Architecture.constraints[].id` |
| Architecture → Spec 需求 | `constraints[].related_requirements[]` | `Spec.requirements[].id` |

### 禁止的引用方式

- ❌ 自由文本：`architecture_rules: ["Service 层不得直接访问数据库"]`
- ✅ 结构化 ID：`constraint_refs: ["CON-NOT-001"]`

### ID 格式规范

所有 ID 必须符合 Artifact Meta Schema Rules 7 的格式：

| 类型 | 格式 | 示例 |
|------|------|------|
| Requirement | `REQ-{domain}-{seq:03d}` | REQ-NOT-001 |
| Acceptance Criteria | `AC-{domain}-{seq:03d}` | AC-NOT-001 |
| Constraint | `CON-{domain}-{seq:03d}` | CON-NOT-001 |
| Module | `MOD-{domain}-{seq:03d}` | MOD-NOT-001 |

详见 `templates/meta/artifact-meta-schema.yaml` Rules 6/7/8。

---

## Verify Schema 字段命名约定（Phase 2.5 Frozen）

所有 Skill 在生成或消费 Verify Report 时，**必须**使用 Verify Schema v1.0-frozen 中定义的字段命名。

### 冻结字段命名（6 项）

| # | 字段路径 | 类型 | 用途 |
|---|---------|------|------|
| 1 | `coverage.requirement_coverage` | object | 需求覆盖率（V1 输出） |
| 2 | `coverage.acceptance_coverage` | object | 验收标准覆盖率（V2 输出） |
| 3 | `coverage.constraint_coverage` | object | 约束引用覆盖率（V3 输出） |
| 4 | `coverage.validation_coverage` | object | 验证步骤执行率（V6 输出） |
| 5 | `context.validation_status_map` | object | validation_step 运行时状态映射 |
| 6 | `verify_output_mode` | enum | harness-analyze 输出模式参数 |

### 冻结枚举值（3 套分维度词汇表）

```yaml
# 1. 架构约束严重度（Architecture Constraint Severity）
severity_distribution:
  must:    # 必须（违反 = 阻塞）
  should:  # 推荐（违反 = 警告）
  may:     # 可选（违反 = 信息）

# 2. 运行时验证状态（Runtime Verify Status）
validation_status:
  passed:   # 通过
  failed:   # 失败
  skipped:  # 跳过（前置条件未满足）
  error:    # 异常（工具故障/超时/配置错误）

# 3. 问题严重度（Issue Severity）
issue_severity:
  block:    # 阻塞（必须修复）
  warning:  # 警告（建议修复）
  info:     # 信息（仅提示）
```

### Consumer Skill 必须遵守的规则

| 规则 | 说明 |
|------|------|
| **字段名必须一致** | 不允许使用 `req_coverage` / `ac_coverage` 等缩写 |
| **枚举值必须匹配** | 不允许使用 `pass` / `fail` / `success` 等替代值 |
| **新增字段必须走 MINOR 流程** | 不能直接添加新字段而不升级版本号 |
| **枚举语义稳定** | 不允许改变 `passed` 的含义（如增加"通过但有警告"） |

详见 `templates/meta/verify-schema.yaml` §4（权威定义）。

---

## Agent 体系说明

### 什么是 Agent

Agent 是**专注于特定技术领域的执行单元**，由 Skill 编排器调用，负责完成具体的代码开发或审查任务。

| 概念 | 职责 | 与用户的交互 |
|------|------|------------|
| **Skill 编排器** | 流程控制、任务分配、状态管理 | 直接与用户交互 |
| **Agent** | 代码实现、代码审查、技术决策 | 不直接与用户交互，仅与编排器通信 |

### 内置 Agent 列表

本项目预定义以下 Agent，位于 `templates/agents/` 目录：

| Agent | 文件 | 职责 | 被调用时机 |
|-------|------|------|------------|
| `backend-dev` | `templates/agents/backend-dev.md` | 后端代码开发 | `harness-execute` 阶段 2、`harness-apply` 阶段 2 |
| `frontend-dev` | `templates/agents/frontend-dev.md` | 前端代码开发 | `harness-execute` 阶段 2、`harness-apply` 阶段 2 |
| `code-reviewer` | `templates/agents/code-reviewer.md` | 代码审查 | `harness-execute` 阶段 3、`harness-verify` |
| `spec-validator` | `templates/agents/spec-validator.md` | 规格验证 | `harness-verify` |

### Agent 调用方式

Skill 编排器调用 Agent 时，传递以下信息：

```
任务描述：{{task_description}}
涉及文件：{{file_list}}
接口契约：{{api_contract}}（如有）
参照模块：{{reference_module}}（如有）
审查维度：{{review_dimensions}}（审查类 Agent）
```

Agent 完成后，返回结构化结果：

```
执行摘要：{{summary}}
文件变更清单：{{file_changes}}
关键决策：{{decisions}}
验证结果：{{verification}}
注意事项：{{notes}}
```

### 何时使用 Agent 模式

Agent 模式是**可选的增强能力**：

- **单会话模式**（默认）：Skill 编排器自行完成所有任务，不调用 Agent
- **多 Agent 模式**：Skill 编排器将具体任务分配给对应 Agent，实现专业化分工

选择依据：
- 项目规模较小、技术栈单一 → 单会话模式足够
- 项目规模较大、前后端分离、需要深度审查 → 启用多 Agent 模式

### Agent 与 Skill 的关系

```
用户 → Skill 编排器（harness-execute / harness-apply / harness-verify）
            ↓
    ┌───────┼───────┐
    ↓       ↓       ↓
backend-dev  frontend-dev  code-reviewer
    ↓       ↓       ↓
    └───────┴───────┘
            ↓
      返回结果给编排器
            ↓
      编排器更新项目状态 → 与用户交互
```

---

## 1. 工单执行规则

### 1.1 三段式执行

每个工单严格按三阶段执行：

| 阶段 | 目标 | 约束 |
|------|------|------|
| 阶段 1（只读） | 理解上下文，确认范围 | 禁止写代码 |
| 阶段 2（写码） | 实现文件清单 | 仅实现清单内路径 |
| 阶段 3（自审） | 验证完整性/正确性/一致性 | 逐项检查清单 |

### 1.2 工单依赖

- 执行前确认所有依赖工单已完成
- 依赖关系在工单元数据中标注

### 1.3 工单范围

- 不扩大工单范围（不添加额外功能）
- 不缩小工单范围（不跳过功能点）
- 发现范围问题时暂停并报告

---

## 2. TBD 占位符约定

项目文档中可能包含 TBD 占位符，统一使用 `[TBD: ...]` 格式：

| 格式 | 含义 | 写入时机 | 回填时机 |
|------|------|---------|--------|
| `[TBD: filled by Fxx]` | 待工单实现时回填 | harness-specify / harness-specify-arch | harness-execute 阶段 3（自审） |
| `[TBD: 待用户确认]` | 用户未澄清，待后续确认 | harness-clarify | harness-clarify 再次执行或用户手动补充 |

- 回填时用实际事实替换占位符，并删除 `[TBD: ...]` 标记
- 禁止在代码或工单中发明 TBD 的新格式

---

## 3. 生成前确认规则

每个 Skill 在写入文件之前，必须先向用户展示生成计划并获得明确确认：

| 阶段 | 必须展示 | 确认方式 |
|------|---------|----------|
| 生成文件前 | 即将生成的文件清单 + 每个文件的简要说明 | 用户明确回复"确认"后才开始写入 |
| 交互式对话后 | 结构化结果（功能清单/架构原则/部署配置等） | 用户确认后才生成 project.yaml 或其他文件 |
| 工单执行前 | 阶段 1 只读分析结果 + 文件清单 | 用户确认后才进入阶段 2 写码 |

**确认原则**：
- 每步单独确认，不合并多步为一次
- 用户回复"跳过确认"或"全部确认"时，可一次性执行

---

## 4. 禁止行为

- 禁止修改 `ARCHITECTURE.md`（除非工单明确要求）
- 禁止删除已完成的工单文件
- 禁止跳过阶段 1 直接写代码
- 禁止在未读取依赖代码的情况下开始实现
- 禁止修改不在工单范围内的文件
- 禁止在未获得用户确认的情况下写入任何文件
- **禁止直接修改 Frozen Schema**（见上文 Schema Change Policy）
- **禁止使用未注册的 `context.*` 变量**（必须先在 Context Schema 注册）
- **禁止绕过 Schema 引用完整性校验**（必须使用结构化 ID 引用）

---

## 5. 上下文管理

### 5.1 上下文窗口不足时

当上下文不足以容纳全部信息时：

1. 优先保留：当前工单 + 依赖文件
2. 可重新读取：`progress.md` + `session-handoff.md`
3. 可跳过：已完成工单的详细内容

### 5.2 会话中断恢复

如果会话中断，重新开始时：

1. 读取 `session-handoff.md` 获取暂停点
2. 读取 `progress.md` 获取整体进度
3. 从中断的工单继续执行

---

## 6. 变更流程

后续代码变更（非首次工单）遵循以下流程：

```
harness-change（创建变更提案）
    ↓
harness-apply（实现任务清单）
    ├── 阶段 0.5：任务分批与 Agent 分配（如启用 Agent 模式）
    │       ├── backend-dev Agent：后端任务批次
    │       └── frontend-dev Agent：前端任务批次
    ↓
harness-verify（三维度验证）
    ├── 阶段 3.5：code-reviewer Agent 深度审查（如启用 Agent 模式）
    ↓
harness-archive（归档，合并增量规格）
```

详见 `changes/` 目录下的变更管理流程。

### Agent 在变更流程中的角色

| 阶段 | Skill | Agent 参与 | 说明 |
|------|-------|-----------|------|
| 变更创建 | `harness-change` | 否 | 由编排器完成 |
| 任务实现 | `harness-apply` | 是 | 后端/前端 Agent 执行具体代码 |
| 自审 | `harness-apply` 阶段 3 | 可选 | 可由 code-reviewer 辅助 |
| 验证 | `harness-verify` | 是 | spec-validator 执行规格验证，code-reviewer 执行代码审查 |
| 归档 | `harness-archive` | 否 | 由编排器完成 |

---

## 7. 文件更新规则

以下文件在每次工单完成后必须更新：

| 文件 | 更新内容 |
|------|---------|
| `progress.md` | 标记工单状态、记录变更暂停点 |
| `session-handoff.md` | 记录已验证产出、下一步操作 |
| `feature_list.json` | 标记功能完成状态 |

---

## 8. 健康检查

运行以下命令验证项目状态：

```
{{health_check_command}}
```

架构约束检查：

```
{{architecture_check_command}}
```
