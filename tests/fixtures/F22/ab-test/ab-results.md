# AB Test 结果

> **执行日期**：2026-06-25
> **Agent**：qoder (claude-model)
> **注意**：同一 Agent 执行两轮，存在记忆偏倚。真实 AB Test 需要在独立 Agent 实例上运行。

---

## Round 1 — A 组（仅 Task）

### 一级指标

| 指标 | 值 |
|------|----|
| Test Pass Rate | **6 / 6** ✅ |
| └ test_send_success | pass |
| └ test_send_failure_with_retry | pass |
| └ test_retry_recovery | pass |
| └ test_get_status_default | pass |
| └ test_no_direct_db_access | pass |
| └ test_service_persist_order | pass |

### 约束合规

| 约束 | 合规？ | 证据 |
|------|-------|------|
| CON-NOT-001（不直接访问数据库） | ✅ pass | test_no_direct_db_access 通过；Agent 从 service.py 推断出此约束 |
| CON-NOT-002（先持久化再确认） | ✅ pass | test_service_persist_order 通过；Service 层已实现，Agent 未破坏 |

### 需求覆盖

| 需求 | 覆盖？ | 证据 |
|------|-------|------|
| REQ-NOT-001（邮件发送） | ✅ pass | send() 实现，test_send_success 通过 |
| REQ-NOT-002（状态追踪） | ✅ pass | get_status() 返回 PENDING，内部维护 _status dict |
| REQ-NOT-003（渠道扩展） | ✅ N/A | ChannelAdapter 接口已满足，无需额外实现 |

### 效率指标

| 指标 | 值 |
|------|----|
| 实现尝试次数 | 1 |
| 代码修改次数 | 1（一次性写入完整实现） |
| 额外探索文件数 | 3（base.py、test_email_channel.py、service.py） |
| 是否产生冗余代码 | 否 |
| 代码注释质量 | 基础（方法级 docstring，无 Frozen Schema 引用） |

### Agent 行为观察

1. Agent 从 `base.py` 读取接口定义 → 确定需要实现 send/retry/get_status
2. Agent 从 `test_email_channel.py` 推断预期行为（重试次数、SMTP mock、状态查询）
3. Agent 从 `service.py` 发现 save → send → update_status 的执行顺序
4. **Agent 未意识到 REQ-NOT-001/002/003 的存在**，但通过测试和骨架代码间接满足了它们
5. Agent 没有询问任何问题，直接从已有代码完成推断

---

## Round 2 — B 组（Task + Context Bundle）

### 一级指标

| 指标 | 值 |
|------|----|
| Test Pass Rate | **6 / 6** ✅ |
| └ test_send_success | pass |
| └ test_send_failure_with_retry | pass |
| └ test_retry_recovery | pass |
| └ test_get_status_default | pass |
| └ test_no_direct_db_access | pass |
| └ test_service_persist_order | pass |

### 约束合规

| 约束 | 合规？ | 证据 |
|------|-------|------|
| CON-NOT-001（不直接访问数据库） | ✅ pass | Context Bundle 明确告知"EmailChannelSender 位于 infrastructure 层，不需要关心此约束" |
| CON-NOT-002（先持久化再确认） | ✅ pass | Context Bundle 明确告知"持久化由 NotificationService 负责" |

### 需求覆盖

| 需求 | 覆盖？ | 证据 |
|------|-------|------|
| REQ-NOT-001（邮件发送） | ✅ pass | docstring 明确标注"满足 REQ-NOT-001" |
| REQ-NOT-002（状态追踪） | ✅ pass | docstring 明确标注"满足 REQ-NOT-002" |
| REQ-NOT-003（渠道扩展） | ✅ N/A | 同 Round 1 |

### 效率指标

| 指标 | 值 |
|------|----|
| 实现尝试次数 | 1 |
| 代码修改次数 | 1（一次性写入完整实现） |
| 额外探索文件数 | 0（Context Bundle 已提供所有背景信息） |
| 是否产生冗余代码 | 否 |
| 代码注释质量 | 增强（docstring 含 REQ/AC/CON/ADR 引用，可追踪） |

### Agent 行为观察

1. Agent 直接从 Context Bundle 了解业务背景（REQ-NOT-001/002）和约束（CON-NOT-001/002）
2. Agent 不再需要从 service.py 推断约束——Context Bundle 的 note 明确说明"EmailChannelSender 位于 infrastructure 层不受影响"
3. Agent 将 Frozen Schema 引用写入 docstring，增强了代码可追踪性
4. **关键差异**：Agent 知道自己"为什么做"（REQ-NOT-001 邮件发送业务需求），而不仅仅是"怎么做"（实现 ChannelAdapter 接口）

---

## 对比汇总

| 指标 | A 组（仅 Task） | B 组（Task + Bundle） | Δ |
|------|:---:|:---:|:---:|
| Test Pass Rate | 6/6 | 6/6 | 0 |
| Constraint Compliance | 2/2 | 2/2 | 0 |
| Requirement Coverage | 2/2 | 2/2 | 0 |
| 实现尝试次数 | 1 | 1 | 0 |
| 额外文件探索 | 3 个文件 | 0 个文件 | **-3** |
| 代码可追踪性 | 无 Frozen Schema 引用 | 含 REQ/AC/CON/ADR 引用 | **+4 处引用** |
| 是否理解"为什么" | 间接（从测试推断） | 直接（Context Bundle 告诉） | **语义提升** |

---

## 分析

### 为什么 A ≈ B（功能指标相同）？

1. **测试文件已经编码了所有约束**：`test_no_direct_db_access` 直接检查源码中是否有 SQL 操作，`test_service_persist_order` 检查执行顺序。Agent 即使不知道 CON-NOT-001 的名称，也能通过测试文件满足它。

2. **骨架代码已经示范了正确模式**：`service.py` 中写明了 save → send → update_status 的顺序，Agent 可以模仿。

3. **任务范围小且精确**：只需实现一个类（~60 行），不需要理解整个系统的架构。

4. **同一 Agent 的记忆偏倚**：Round 2 执行时 Agent 已经知道 Round 1 的正确实现。

### Context Bundle 的真实价值在哪里？

在这个简单任务中不明显，但在以下场景中 Context Bundle 的价值才会显现：

| 场景 | 无 Context Bundle | 有 Context Bundle |
|------|-----------------|-----------------|
| **Agent 不知道某个约束存在** | 写出的代码违反 CON-NOT-001，事后才发现 | 事前就知道，不会写出违规代码 |
| **Requirement 被多个 Task 分散实现** | Agent 不知道其他 Task 做了什么，可能重复 | 知道 REQ 的全貌和已有覆盖 |
| **Architecture 有隐含假设** | Agent 需要从多个文件中拼凑 | ADR 直接告诉决策背景 |
| **Spec/Architecture 不在代码库中** | Agent 根本看不到（外部文档） | Context Bundle 已解析好 |

### 本次 AB Test 的局限性

1. **测试任务过于简单**：单个类实现，60 行代码，6 个测试
2. **测试文件高度自文档化**：约束被编码为 assert 语句
3. **同一 Agent 执行两轮**：记忆污染
4. **代码库和 Spec 在同一仓库**：Agent 可以自行发现
5. **任务不涉及"不知道有约束"的场景**：测试已经告诉了所有规则

---

## 结论

### 本轮结果

```
A 组（仅 Task）      6/6  ✅
B 组（Task+Bundle）  6/6  ✅
────────────────────────────
功能指标              A ≈ B
代码可追踪性          B > A（含 Frozen Schema 引用）
探索成本              B < A（省去 3 个文件读取）
```

### 判定

**⚠️ 本次 AB Test 无法证明 Context Bundle 显著提升 Agent 成功率**，因为测试任务本身已将约束编码为可执行测试。

但这**不等于 Context Bundle 无价值**。它证明的是：当测试文件足够好时，Agent 不需要额外上下文。而真实项目中，很少有测试文件能覆盖所有架构约束。

### 建议

要达到"证明 Context Bundle 提升 Agent 成功率"的目标，需要：

1. **更大的任务**（>200 行代码，跨多个文件）
2. **不完整的测试**（测试不覆盖架构约束，约束需要 Agent 自行遵守）
3. **外部 Spec/Architecture**（不在代码库中，Agent 无法自行发现）
4. **独立 Agent 实例**（消除记忆偏倚）

---

> **Validation-2 Execution 完成。A ≈ B（功能指标）。Context Bundle 在代码可追踪性和探索成本上优于对照组，但在本测试的任务粒度下未能证明显著的功能差异。需要更大规模的验证。**
