# Runtime State Model

> **Phase**：5（Runtime Execution Layer）
> **版本**：v1.0-draft
> **依赖**：Planner State Model（Phase 4）、Context Engine（Phase 3）、Verify Schema v1.0-frozen
> **原则**：不新增 Schema。状态基于已有文件（session-handoff.md、progress.md、Verify Report）。
> **职责**：定义单个 Skill 执行的生命周期状态机。

---

## 1. 执行生命周期

```
                         ┌──────────┐
                         │ PENDING  │ ← Planner 输出 next_skill
                         └────┬─────┘
                              │ Runtime Executor 接管
                              ▼
                    ┌─────────────────┐
                    │ BUILDING_CONTEXT │ ← 调用 harness-context
                    └────────┬────────┘
                             │ context_bundle.yaml 生成
                             ▼
                    ┌──────────────┐
                    │ CONTEXT_READY │
                    └──────┬───────┘
                           │ 将 context_bundle 交给 Agent
                           ▼
                    ┌──────────┐
                    │ RUNNING  │ ← Agent 执行 Skill
                    └────┬─────┘
                         │
              ┌──────────┼──────────┐
              ▼                     ▼
       ┌──────────┐         ┌──────────┐
       │ COMPLETED│         │  FAILED  │
       └────┬─────┘         └────┬─────┘
            │                    │
            │              ┌─────▼──────┐
            │              │  RETRYING  │ ← Retry Policy 判断
            │              └─────┬──────┘
            │                    │ retry_count < max_retries
            │                    ▼
            │              ┌──────────┐
            │              │ RUNNING  │ (重新执行)
            │              └──────────┘
            │
            ▼
     ┌───────────┐
     │ VERIFYING │ ← 调用 harness-runtime-verify
     └─────┬─────┘
           │
    ┌──────┼──────┐
    ▼              ▼
┌──────────┐  ┌──────────────┐
│ VERIFIED │  │VERIFY_FAILED │
└──────────┘  └──────────────┘
     │              │
     │        ┌─────▼──────┐
     │        │  RETRYING  │ (retry_count < max_retries)
     │        └────────────┘
     ▼
  (Planner 接管，输出下一个 Skill)
```

## 2. 状态定义

```yaml
execution_state:
  # ── 元信息 ──
  task_id: "F22-order-001"
  skill: "harness-execute"
  started_at: "2026-06-25T15:00:00+08:00"
  updated_at: "2026-06-25T15:05:00+08:00"

  # ── 当前状态 ──
  status:
    type: enum
    values:
      - PENDING            # Planner 已选择，等待 Runtime 接管
      - BUILDING_CONTEXT   # 正在构建上下文
      - CONTEXT_READY      # 上下文就绪，等待 Agent 执行
      - RUNNING            # Agent 正在执行
      - COMPLETED          # Agent 执行完成（可能成功也可能需要验证）
      - FAILED             # Agent 执行失败（异常、超时、用户取消）
      - RETRYING           # 正在重试（等待冷却后重新 RUNNING）
      - VERIFYING          # 正在运行验证步骤
      - VERIFIED           # 验证通过
      - VERIFY_FAILED      # 验证失败

  # ── 重试信息 ──
  retry:
    count: 0               # 当前重试次数
    max_retries: 3         # 最大重试次数
    last_error: null       # 最后一次错误信息
    next_retry_at: null    # 下次重试时间（冷却后）

  # ── 上下文 ──
  context:
    bundle_path: "orders/F22-order-001/context_bundle.yaml"
    token_count: 7200
    generated_at: "2026-06-25T15:00:00+08:00"

  # ── 执行结果 ──
  result:
    exit_code: null        # Agent 执行退出码（0=成功）
    output_summary: null   # 执行摘要
    files_changed: []      # 修改的文件列表
    duration_seconds: null

  # ── 验证结果 ──
  verify:
    overall_status: null   # passing / failing
    validation_status_map: {}  # VAL-xxx → passed/failed/skipped/error
    coverage: {}           # Verify Schema 的 4 类 coverage
```

## 3. 状态转换规则

| 当前状态 | 触发事件 | 下一状态 | 条件 |
|---------|---------|---------|------|
| PENDING | Runtime 接管 | BUILDING_CONTEXT | Skill 需要上下文（harness-execute / harness-apply） |
| PENDING | Runtime 接管 | RUNNING | Skill 不需要上下文（harness-init / harness-clarify 等） |
| BUILDING_CONTEXT | harness-context 完成 | CONTEXT_READY | context_bundle.yaml 存在 |
| BUILDING_CONTEXT | harness-context 失败 | FAILED | context 构建失败 |
| CONTEXT_READY | Agent 开始执行 | RUNNING | - |
| RUNNING | Agent 正常完成 | COMPLETED | Agent 报告成功 |
| RUNNING | Agent 异常/超时 | FAILED | 异常、超时、用户取消 |
| RUNNING | Retry Policy 触发 | RETRYING | retry_count < max_retries |
| FAILED | Retry Policy 允许 | RETRYING | retry_count < max_retries |
| FAILED | Retry Policy 拒绝 | PENDING（终态） | retry_count >= max_retries |
| RETRYING | 冷却结束 | RUNNING | 冷却时间到 |
| COMPLETED | 开始验证 | VERIFYING | Skill 有 validation_steps |
| COMPLETED | 跳过验证 | VERIFIED | Skill 无 validation_steps |
| VERIFYING | 验证通过 | VERIFIED | overall_status = passing |
| VERIFYING | 验证失败 | VERIFY_FAILED | overall_status = failing |
| VERIFY_FAILED | Retry Policy 允许 | RETRYING | retry_count < max_retries |
| VERIFY_FAILED | Retry Policy 拒绝 | PENDING（终态） | retry_count >= max_retries |

## 4. 终态

以下状态为终态（Runtime 不再管理，交还给 Planner）：

| 终态 | 含义 | Planner 下一步 |
|------|------|---------------|
| VERIFIED | 执行成功 + 验证通过 | 继续 Flow 链的下一个 Skill |
| FAILED（终态） | 重试耗尽，仍然失败 | 人工介入或跳过 |
| VERIFY_FAILED（终态） | 验证多次失败 | 人工介入 |

## 5. 状态持久化

状态写入 `session-handoff.md`（复用已有文件，不新增）：

```markdown
### Runtime Execution State

- **Task**: F22-order-001
- **Skill**: harness-execute
- **Status**: RUNNING
- **Started**: 2026-06-25T15:00:00+08:00
- **Retry**: 0/3
```

进度更新写入 `progress.md`：

```markdown
### F22-order-001
- Status: active → passing（after VERIFIED）
```

## 6. 与 Planner 的接口

```
Planner 输出：
  decision:
    next_skill: "harness-execute"
    reason: "F22-order-001 待执行"
    target_task: "F22-order-001"

Runtime 接收：
  → 创建 execution_state（PENDING）
  → 按状态机执行
  → 达到终态后，交还 Planner
  → Planner 读取新状态，输出下一个 decision
```

## 7. 不需要 Runtime 的 Skill

以下 Skill 不需要 Runtime 状态机管理（直接执行，无需状态跟踪）：

| Skill | 原因 |
|-------|------|
| harness-init | 一次性初始化 |
| harness-init-docs | 一次性生成 |
| harness-clarify | 交互式，无重试 |
| harness-analyze | 只读审计 |
| harness-explore | 只读探索 |

这些 Skill 的执行状态由 Planner 的 project_state 跟踪（features.status 等），不需要 Runtime 的 execution_state。

## 8. 需要的 Skill

以下 Skill 需要 Runtime 状态机管理：

| Skill | 原因 |
|-------|------|
| harness-execute | 核心执行，需重试 + 验证 |
| harness-apply | 变更实现，需重试 + 验证 |
| harness-review-loop | 审查循环，最多 3 轮 |
| harness-runtime-verify | 运行时验证，可能需要重试 |
| harness-context | 上下文构建，失败可重试 |

---

> **v1.0-draft（2026-06-25）**：初始版本。定义 10 状态执行状态机，与 Planner/Context Engine 的集成接口。
