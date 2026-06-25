# Runtime Validation Plan

> **Phase**：5.1（Runtime Validation）
> **依赖**：runtime-state-model.md、runtime-executor.md、runtime-retry-policy.md
> **验证目标**：证明 Runtime 状态机正确管理执行生命周期
> **验证方式**：状态迁移表 + 场景模拟

---

## 1. 验证策略

### 1.1 不验证什么

| 范围 | 原因 |
|------|------|
| ❌ Agent 实际执行结果 | Runtime 管理生命周期，不执行 Skill |
| ❌ Context Engine 正确性 | 已在 Phase 3 验证 |
| ❌ Planner 路由正确性 | 已在 Phase 4 验证 |
| ❌ 真实 Agent 调用 | Phase 5 不涉及 Runtime Execution |

### 1.2 验证什么

| 验证项 | 标准 |
|--------|------|
| **状态迁移正确性** | 所有合法迁移按预期执行；非法迁移被拒绝 |
| **重试决策正确性** | 可重试/不可重试分类正确 |
| **终态识别** | VERIFIED / FAILED（终态）/ VERIFY_FAILED（终态）正确触发 |
| **相同错误检测** | 连续 2 次相同错误 → 终止 |
| **上下文构建集成** | BUILDING_CONTEXT → CONTEXT_READY 或 FAILED |
| **验证集成** | COMPLETED → VERIFYING → VERIFIED 或 VERIFY_FAILED |

---

## 2. 状态迁移测试

### 2.1 正常路径

| # | 场景 | 初始状态 | 事件 | 期望下一状态 |
|---|------|---------|------|------------|
| M-01 | 需要上下文的 Skill | PENDING | Runtime 接管 | BUILDING_CONTEXT |
| M-02 | 不需要上下文的 Skill | PENDING | Runtime 接管 | RUNNING |
| M-03 | 上下文构建成功 | BUILDING_CONTEXT | context_bundle 生成 | CONTEXT_READY |
| M-04 | Agent 开始执行 | CONTEXT_READY | Agent 启动 | RUNNING |
| M-05 | Agent 正常完成 | RUNNING | Agent 报告成功 | COMPLETED |
| M-06 | COMPLETED + 有 validation_steps | COMPLETED | 开始验证 | VERIFYING |
| M-07 | COMPLETED + 无 validation_steps | COMPLETED | 跳过验证 | VERIFIED |
| M-08 | 验证通过 | VERIFYING | overall_status=passing | VERIFIED |
| M-09 | 验证失败 | VERIFYING | overall_status=failing | VERIFY_FAILED |

### 2.2 异常路径

| # | 场景 | 初始状态 | 事件 | 期望下一状态 |
|---|------|---------|------|------------|
| M-10 | 上下文构建失败 | BUILDING_CONTEXT | harness-context 失败 | FAILED |
| M-11 | Agent 执行异常 | RUNNING | Agent 超时/异常 | FAILED |
| M-12 | 可重试失败 → 重试 | FAILED | retry_count=0, error=可重试 | RETRYING |
| M-13 | 重试冷却结束 | RETRYING | 冷却时间到 | RUNNING |
| M-14 | 不可重试失败 | FAILED | error=权限错误 | FAILED（终态） |
| M-15 | 重试耗尽 | FAILED | retry_count=3 | FAILED（终态） |
| M-16 | 验证失败后重试 | VERIFY_FAILED | retry_count=0 | RETRYING |
| M-17 | 验证重试耗尽 | VERIFY_FAILED | retry_count=2 | VERIFY_FAILED（终态） |

### 2.3 非法迁移（应被拒绝）

| # | 场景 | 非法迁移 | 期望行为 |
|---|------|---------|---------|
| M-18 | 跳过上下文直接执行 | BUILDING_CONTEXT → RUNNING | 拒绝（必须先 CONTEXT_READY） |
| M-19 | 未完成就验证 | RUNNING → VERIFYING | 拒绝（必须先 COMPLETED） |
| M-20 | 已验证再重试 | VERIFIED → RETRYING | 拒绝（终态不可迁移） |

---

## 3. 重试决策测试

### 3.1 可重试错误

| # | 错误类型 | retry_count | 期望决策 | 期望冷却 |
|---|---------|:----------:|---------|:------:|
| R-01 | 上下文构建失败 | 0/1 | RETRYING | 0s |
| R-02 | Agent 超时 | 0/3 | RETRYING | 0s |
| R-03 | 测试失败 | 1/3 | RETRYING | 0s |
| R-04 | Lint 失败 | 0/2 | RETRYING | 0s |
| R-05 | 验证失败 | 0/2 | RETRYING | 5s |

### 3.2 不可重试错误

| # | 错误类型 | 期望决策 | 期望终态 |
|---|---------|---------|---------|
| R-06 | Schema 违规 | 不可重试 | FAILED（终态） |
| R-07 | 依赖缺失 | 不可重试 | FAILED（终态） |
| R-08 | 权限错误 | 不可重试 | FAILED（终态） |
| R-09 | 配置错误 | 不可重试 | FAILED（终态） |
| R-10 | 用户取消 | 不可重试 | FAILED（终态） |

### 3.3 相同错误检测

| # | 场景 | 重试 1 错误 | 重试 2 错误 | 期望决策 |
|---|------|-----------|-----------|---------|
| R-11 | 不同错误 | "test_send failed" | "test_retry failed" | RETRYING |
| R-12 | 相同错误 | "assert status == SENT" | "assert status == SENT" | 不可重试 |
| R-13 | 相似但不相同 | "line 42: assert" | "line 42: assert status" | RETRYING（前 100 字符不同） |

---

## 4. Skill 差异化配置测试

| # | Skill | 期望 max_retries | 期望冷却 | 需要上下文？ |
|---|-------|:---------------:|:------:|:---------:|
| S-01 | harness-execute | 3 | 0s | ✅ |
| S-02 | harness-apply | 3 | 0s | ✅ |
| S-03 | harness-review-loop | 2 | 0s | ✅ |
| S-04 | harness-runtime-verify | 2 | 5s | ✅ |
| S-05 | harness-context | 1 | 0s | N/A（自身就是上下文构建） |
| S-06 | harness-init | N/A（直通） | - | ❌ |

---

## 5. 完整场景模拟

### 场景 1：正常执行（harness-execute）

```
项目状态：F22-order-001 status=active, phase=1
Planner 输出：next_skill=harness-execute

Runtime 执行：
  PENDING → BUILDING_CONTEXT → CONTEXT_READY → RUNNING → COMPLETED → VERIFYING → VERIFIED

期望：
  - progress.md：F22-order-001 status → passing
  - session-handoff.md：last_skill=harness-execute, runtime_state.status=VERIFIED
  - 下一步 Planner：harness-verify
```

### 场景 2：测试失败 → 修复 → 成功

```
项目状态：同上

Runtime 执行：
  PENDING → BUILDING_CONTEXT → CONTEXT_READY → RUNNING → COMPLETED
    → VERIFYING（pytest 4/6 通过）
    → VERIFY_FAILED（retry_count=0/3）
    → RETRYING → RUNNING（Agent 修复代码）
    → COMPLETED → VERIFYING（pytest 6/6 通过）
    → VERIFIED

期望：
  - retry_count 最终为 1
  - progress.md：F22-order-001 status → passing
```

### 场景 3：不可恢复错误

```
项目状态：同上

Runtime 执行：
  PENDING → BUILDING_CONTEXT → CONTEXT_READY → RUNNING
    → 错误："PermissionError: 无法写入 src/main.py"
    → FAILED（终态，retry_count=0）

期望：
  - reason："PermissionError: 无法写入 src/main.py"
  - requires_human：true
  - Planner 下一步：建议人工介入
```

### 场景 4：连续 2 次相同错误

```
项目状态：同上

Attempt 1：RUNNING → COMPLETED → VERIFYING → VERIFY_FAILED
  error："AssertionError: assert status == NotificationStatus.SENT"

Attempt 2：RETRYING → RUNNING → COMPLETED → VERIFYING → VERIFY_FAILED
  error："AssertionError: assert status == NotificationStatus.SENT"（前 100 字符相同）

→ FAILED（终态）
  reason："连续 2 次相同错误：AssertionError: assert status == NotificationStatus.SENT"
```

### 场景 5：不需要 Runtime 的 Skill（直通）

```
项目状态：F22 status=clarifying
Planner 输出：next_skill=harness-specify

Runtime 执行：
  PENDING → RUNNING（直通，不需要上下文）
  Agent 完成 → COMPLETED
  → VERIFIED（无 validation_steps，直接标记完成）

期望：
  - progress.md：F22 status → specifying
```

---

## 6. 验证执行

使用 Python 状态机测试：

```python
def test_state_machine():
    executor = RuntimeExecutor()
    
    # 正常路径
    state = executor.execute("harness-execute", "F22-order-001")
    assert state.status == "VERIFIED"
    
    # 异常路径（模拟失败）
    state = executor.execute("harness-execute", "F22-order-001", 
                             simulate_error="permission_denied")
    assert state.status == "FAILED"
    assert state.retry.last_error == "permission_denied"
```

---

## 7. 通过标准

| 指标 | 目标 |
|------|:----:|
| 状态迁移正确率 | 100%（20 个迁移测试） |
| 重试决策正确率 | 100%（13 个重试测试） |
| 相同错误检测率 | 100%（3 个检测测试） |
| Skill 配置正确率 | 100%（6 个配置测试） |
| 场景模拟通过率 | 100%（5 个完整场景） |
| **总计** | **47 个测试用例** |

---

> **v1.0-draft（2026-06-25）**：初始版本。定义 47 个测试用例覆盖状态迁移、重试决策、场景模拟。
