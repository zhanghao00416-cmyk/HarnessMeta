# Runtime Retry Policy

> **Phase**：5（Runtime Execution Layer）
> **依赖**：runtime-state-model.md、runtime-executor.md
> **原则**：确定性策略（无随机退避），基于错误类型分类决策。
> **职责**：定义执行失败时的重试决策逻辑。

---

## 1. 核心决策

```
执行失败（FAILED 或 VERIFY_FAILED）
    │
    ▼
┌─────────────────────────────┐
│ retry_count < max_retries？  │
│ 否 → 终态（人工介入）         │
│ 是 → 继续判断                │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 错误是否可重试？              │
│ 否 → 终态（不可恢复错误）      │
│ 是 → 进入 RETRYING           │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ 应用冷却时间                  │
│ 冷却结束 → RUNNING           │
└─────────────────────────────┘
```

## 2. 错误分类

### 2.1 可重试错误

| 错误类型 | 示例 | 重试策略 |
|---------|------|---------|
| **上下文构建失败** | harness-context 读取文件超时 | 重试（文件系统暂时不可用） |
| **Agent 执行超时** | Agent 响应超时 | 重试（可能是临时负载） |
| **Agent 输出不完整** | 代码未完全生成 | 重试（提示 Agent 继续） |
| **测试失败** | pytest 2/6 失败 | 重试（Agent 修复代码） |
| **Lint 警告** | ruff 报告格式问题 | 重试（Agent 修复格式） |
| **网络临时故障** | API 调用临时失败 | 重试（冷却后重试） |

### 2.2 不可重试错误（立即终态）

| 错误类型 | 示例 | 原因 |
|---------|------|------|
| **Schema 违规** | 生成的代码引用了不存在的字段 | Agent 理解错误，重试无益 |
| **依赖缺失** | 需要的文件不存在 | 需要前置 Skill 完成 |
| **权限错误** | 无法写入目标文件 | 环境问题，需人工 |
| **配置错误** | project.yaml 格式错误 | 需人工修复 |
| **用户取消** | 用户主动中断 | 尊重用户意图 |
| **相同错误重复 2 次** | 连续 2 次相同错误信息 | 重试无益（Agent 陷入循环） |

## 3. 重试配置

### 3.1 默认配置

```yaml
retry:
  max_retries: 3           # 最多重试 3 次（共 4 次尝试）
  cooldown_seconds: 0       # 默认无冷却（立即重试）
  backoff: fixed            # 固定间隔（无指数退避）
  max_same_error: 2         # 相同错误最多连续出现 2 次
```

### 3.2 按 Skill 差异化配置

| Skill | max_retries | 冷却 | 理由 |
|-------|:-----------:|:----:|------|
| harness-execute | 3 | 0s | 代码修复通常不需要冷却 |
| harness-apply | 3 | 0s | 同上 |
| harness-review-loop | 2 | 0s | 审查本质上是"检查→修复→再检查"，2 轮足够 |
| harness-runtime-verify | 2 | 5s | 验证工具可能需要短暂冷却（如端口释放） |
| harness-context | 1 | 0s | 上下文构建失败通常不是暂时性的 |

## 4. 冷却策略

```
cooling:
  默认：无冷却（cooldown_seconds = 0）
  例外：harness-runtime-verify 冷却 5s（端口释放）

  无指数退避：
    原因：Agent 执行场景不需要"等待服务恢复"。
         指数退避适用于网络请求重试，不适用于 Agent 代码修复。
```

## 5. 重试时的上下文增强

每次重试时，Agent 会收到额外的上下文：

```
重试 1：
  "上次执行失败。错误信息：{last_error}。请修复以下问题后重新执行。"

重试 2：
  "第 2 次重试。上次仍然失败。错误信息：{last_error}。
   请重点关注以下失败的测试：{failed_tests}"

重试 3（最后一次）：
  "最后 1 次重试。前面 {retry_count} 次均失败。
   如果仍然失败，将标记为人工介入。
   请确保所有 validation_steps 通过。"
```

## 6. 相同错误检测

```
如果连续 2 次出现相同错误信息：
  判定为 Agent 陷入循环
  不再重试
  状态 → FAILED（终态）
  reason: "连续 {n} 次相同错误：{error_message}"
```

**相同判断规则**：错误信息的前 100 字符相同（忽略时间戳等动态部分）。

## 7. 重试决策表

| 错误类型 | 可重试？ | 最大重试 | 冷却 | 特殊处理 |
|---------|:------:|:-------:|:----:|---------|
| 上下文构建失败 | ✅ | 1 | 0s | - |
| Agent 超时 | ✅ | 3 | 0s | 提示 Agent 简化输出 |
| Agent 输出不完整 | ✅ | 3 | 0s | 提示 Agent 继续 |
| 测试失败 | ✅ | 3 | 0s | 传递失败测试列表 |
| Lint 失败 | ✅ | 2 | 0s | 传递 lint 输出 |
| 验证失败 | ✅ | 2 | 5s | 传递 validation_status_map |
| Schema 违规 | ❌ | 0 | - | 立即终态 |
| 依赖缺失 | ❌ | 0 | - | 立即终态 |
| 权限错误 | ❌ | 0 | - | 立即终态 |
| 配置错误 | ❌ | 0 | - | 立即终态 |
| 用户取消 | ❌ | 0 | - | 立即终态 |
| 连续 2 次相同错误 | ❌ | 0 | - | 防止循环 |

## 8. 示例

### 示例 1：测试失败 → 重试 → 成功

```
Attempt 1：Agent 实现 EmailChannelSender
  → pytest 4/6 通过（test_retry 相关 2 个失败）
  → VERIFY_FAILED
  → 错误类型：测试失败（可重试）
  → retry_count: 1/3

Attempt 2：Agent 修复重试逻辑
  → pytest 6/6 通过
  → VERIFIED
  → 返回 Planner
```

### 示例 2：相同错误循环 → 终止

```
Attempt 1：Agent 实现 → pytest 2/6 通过
  → 错误："assert status == NotificationStatus.SENT"（4 个测试均失败于此行）
  → VERIFY_FAILED，retry_count: 1/3

Attempt 2：Agent 修复 → pytest 2/6 通过
  → 相同错误："assert status == NotificationStatus.SENT"
  → 连续 2 次相同错误 → 不可重试
  → FAILED（终态），reason: "连续 2 次相同错误"
```

### 示例 3：依赖缺失 → 立即终态

```
Attempt 1：Agent 开始执行
  → 错误：FileNotFoundError: orders/F22-order-001/order.md
  → 错误类型：依赖缺失（不可重试）
  → FAILED（终态）
  → Planner 下一步：推荐 harness-order
```

## 9. 与 Planner 的接口

```
Runtime 达到终态后：

  if state.status == VERIFIED:
    return { "status": "success", "task_id": task_id }
    → Planner 继续 Flow 链

  if state.status == FAILED（终态）:
    return {
      "status": "failed",
      "task_id": task_id,
      "reason": state.retry.last_error,
      "retry_count": state.retry.count,
      "requires_human": true
    }
    → Planner 输出"建议人工介入"
```

---

> **v1.0-draft（2026-06-25）**：初始版本。分类 12 种错误类型，定义差异化重试策略，防止 Agent 循环。
