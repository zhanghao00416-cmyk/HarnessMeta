# Runtime Executor

> **Phase**：5（Runtime Execution Layer）
> **依赖**：runtime-state-model.md、Context Engine（Phase 3）、Planner（Phase 4）
> **原则**：不新增 Schema。基于已验证的 Planner 和 Context Engine。
> **职责**：将 Planner 的 next_skill 决策转化为实际执行。

---

## 1. 定位

```
Planner（Phase 4）          Runtime Executor（Phase 5）
─────────────────          ─────────────────────────
输出：next_skill            输入：next_skill + task_id
                            ↓
                       1. 判断是否需要上下文
                       2. 构建上下文（Context Engine）
                       3. 交给 Agent 执行
                       4. 监控生命周期（状态机）
                       5. 处理失败（Retry Policy）
                       6. 验证结果（Runtime Verify）
                       7. 更新 project_state
                            ↓
                       输出：执行结果 → 交还 Planner
```

## 2. 执行流程

```
execute(skill, task_id):

  # Step 0：创建执行状态
  state = ExecutionState(
    task_id=task_id,
    skill=skill,
    status=PENDING
  )

  # Step 1：判断是否需要上下文
  if skill in CONTEXT_REQUIRED_SKILLS:
    state.status = BUILDING_CONTEXT
    state = build_context(state)      # 调用 Context Engine
    if not state.context_ready:
      return state（FAILED）

  # Step 2：交给 Agent 执行
  state.status = RUNNING
  state = agent_execute(state)        # Agent 执行 Skill

  # Step 3：处理结果
  if state.failed:
    state = retry_or_fail(state)      # Retry Policy
    if state.status == RETRYING:
      goto Step 2                    # 重试

  # Step 4：验证
  if skill_has_validation_steps(skill, task_id):
    state.status = VERIFYING
    state = runtime_verify(state)     # 调用 Runtime Verify
    if state.verify_failed:
      state = retry_or_fail(state)
      if state.status == RETRYING:
        goto Step 2

  # Step 5：更新 project_state
  update_progress(state)

  return state
```

## 3. 上下文构建（Step 1）

```
build_context(state):
  # 调用 Context Engine（harness-context v2.0）
  bundle = harness_context.build(task_id=state.task_id)

  if bundle.success:
    state.context.bundle_path = bundle.path
    state.context.token_count = bundle.token_count
    state.status = CONTEXT_READY
  else:
    state.status = FAILED
    state.retry.last_error = "Context 构建失败"

  return state
```

**需要上下文的 Skill**：

| Skill | 原因 |
|-------|------|
| harness-execute | Agent 需要 Spec/Architecture/Constraints 才能正确实现 |
| harness-apply | 同上，变更场景 |
| harness-review-loop | 需要约束列表来审查代码 |
| harness-runtime-verify | 需要 validation_steps 来运行验证 |

**不需要上下文的 Skill**（直接进入 RUNNING）：

| Skill | 原因 |
|-------|------|
| harness-init | 交互式，无预设上下文 |
| harness-init-docs | 基于已有结构生成 |
| harness-clarify | 交互式 |
| harness-specify | 基于 clarify 结果 |
| harness-specify-arch | 基于 specify 结果 |
| harness-order | 基于 spec + arch |
| harness-analyze | 自己读取文件 |
| harness-change | 交互式 |
| harness-archive | 文件操作 |

## 4. Agent 执行（Step 2）

```
agent_execute(state):
  # 准备 Agent 输入
  prompt = build_agent_prompt(
    skill=state.skill,
    task_id=state.task_id,
    context_bundle=state.context.bundle_path  # 如有
  )

  # 交给 Agent（Agent 是外部实体，Runtime 只负责传递和监控）
  result = invoke_agent(prompt)

  # 记录结果
  state.result.exit_code = result.exit_code
  state.result.output_summary = result.summary
  state.result.files_changed = result.files
  state.result.duration_seconds = result.duration

  if result.success:
    state.status = COMPLETED
  else:
    state.status = FAILED
    state.retry.last_error = result.error

  return state
```

**Agent Prompt 构建规则**：

```yaml
prompt_template:
  for: harness-execute
  structure:
    - "## 任务"：Task artifact 的 objective + implementation_steps
    - "## 上下文"：context_bundle.yaml 内容（如有）
    - "## 约束"：context_bundle 中的 constraints 列表
    - "## 验收标准"：validation_steps
    - "## 执行指令"：三段式执行（只读→写码→自审）

  for: harness-apply
  structure:
    - "## 变更任务"：变更 tasks.md
    - "## 上下文"：context_bundle.yaml（如有）
    - "## 执行指令"：轻量三段式
```

## 5. 验证（Step 4）

```
runtime_verify(state):
  # 读取 Task artifact 的 validation_steps
  steps = get_validation_steps(state.task_id)

  # 调用 harness-runtime-verify
  verify_result = harness_runtime_verify.run(
    task_id=state.task_id,
    steps=steps
  )

  # 记录结果
  state.verify.overall_status = verify_result.overall_status
  state.verify.validation_status_map = verify_result.status_map

  if verify_result.overall_status == "passing":
    state.status = VERIFIED
  else:
    state.status = VERIFY_FAILED
    state.retry.last_error = "验证失败"

  return state
```

**验证步骤来源**：

从 Task artifact 读取 `validation_steps[]`，复用 Verify Schema v1.0-frozen 的 V6 规则：

```yaml
# Task Schema v1.0-frozen
validation_steps:
  - id: "VAL-F22-001-001"
    type: "automated_test"
    command: "pytest tests/test_notification.py -v"
    expected_result: "所有测试通过"
```

## 6. 状态更新（Step 5）

```
update_progress(state):
  # 更新 progress.md
  if state.status == VERIFIED:
    # Task 完成
    progress.update_task(state.task_id, status="passing")
    progress.update_feature(state.feature_id, status="verifying")

  # 更新 session-handoff.md
  session.update({
    "last_skill": state.skill,
    "active_task": state.task_id if state.status in [RUNNING, RETRYING] else None,
    "next_step": get_next_step(state),
    "pause_point": null,
    "runtime_state": {
      "status": state.status,
      "retry_count": state.retry.count,
      "verify_status": state.verify.overall_status,
    }
  })
```

## 7. 与 Planner 的循环

```
┌──────────────────────────────────────────────┐
│                                              │
│  Planner                                     │
│    ↓ next_skill                              │
│  Runtime Executor                            │
│    ↓ PENDING → ... → VERIFIED/FAILED         │
│  update progress.md + session-handoff.md     │
│    ↓                                         │
│  Planner（重新读取 project_state）            │
│    ↓ next_skill                              │
│  ...                                         │
│                                              │
└──────────────────────────────────────────────┘
```

**关键原则**：Runtime 不调用 Planner。Runtime 更新 project_state 后，由外部循环（用户或编排器）重新调用 Planner。

## 8. 不需要 Runtime 的 Skill（直通模式）

对于不需要状态机的 Skill，Runtime 退化为简单的"调用-完成"：

```
execute_simple(skill):
  # 直接交给 Agent
  result = agent_execute_direct(skill)
  # 更新 progress.md
  update_progress_simple(skill, result)
  # 返回
  return result
```

---

> **v1.0-draft（2026-06-25）**：初始版本。定义 5 步执行流程，与 Context Engine 和 Planner 的集成接口。
