# AB Test 指标采集表

> 每运行一组后填写。A 组与 B 组必须在**不同 Agent 会话**中运行。

---

## 执行环境

| 项目 | 值 |
|------|----|
| Agent 模型 | （填写：如 claude-sonnet-4 / gpt-4o / qwen-max） |
| 测试日期 | 2026-06-25 |
| 代码库 commit | （填写：git rev-parse HEAD） |
| 初始测试状态 | 6 failed（email.py 为空） |

---

## A 组结果（仅 Task）

### 一级指标

| 指标 | 值 |
|------|----|
| Test Pass Rate | ? / 6 |
| └ test_send_success | pass / fail |
| └ test_send_failure_with_retry | pass / fail |
| └ test_retry_recovery | pass / fail |
| └ test_get_status_default | pass / fail |
| └ test_no_direct_db_access | pass / fail |
| └ test_service_persist_order | pass / fail |

### 约束合规

| 约束 | 合规？ | 证据 |
|------|-------|------|
| CON-NOT-001（不直接访问数据库） | pass / fail | |
| CON-NOT-002（先持久化再确认） | pass / fail | N/A（Service 层已实现） |

### 需求覆盖

| 需求 | 覆盖？ | 证据 |
|------|-------|------|
| REQ-NOT-001（邮件发送） | pass / fail | |
| REQ-NOT-002（状态追踪） | pass / fail | |

### 效率指标

| 指标 | 值 |
|------|----|
| 返工次数（要求修改的次数） | ? |
| Agent 对话轮数 | ? |
| Prompt Token 消耗 | ? |
| Completion Token 消耗 | ? |

### 观察

```
（填写：Agent 是否自行搜索了 Spec 文件？是否询问了约束？
  是否实现了多余功能？代码风格如何？）
```

---

## B 组结果（Task + Context Bundle）

### 一级指标

| 指标 | 值 |
|------|----|
| Test Pass Rate | ? / 6 |
| └ test_send_success | pass / fail |
| └ test_send_failure_with_retry | pass / fail |
| └ test_retry_recovery | pass / fail |
| └ test_get_status_default | pass / fail |
| └ test_no_direct_db_access | pass / fail |
| └ test_service_persist_order | pass / fail |

### 约束合规

| 约束 | 合规？ | 证据 |
|------|-------|------|
| CON-NOT-001（不直接访问数据库） | pass / fail | |
| CON-NOT-002（先持久化再确认） | pass / fail | N/A（Service 层已实现） |

### 需求覆盖

| 需求 | 覆盖？ | 证据 |
|------|-------|------|
| REQ-NOT-001（邮件发送） | pass / fail | |
| REQ-NOT-002（状态追踪） | pass / fail | |

### 效率指标

| 指标 | 值 |
|------|----|
| 返工次数（要求修改的次数） | ? |
| Agent 对话轮数 | ? |
| Prompt Token 消耗 | ? |
| Completion Token 消耗 | ? |

### 观察

```
（填写：Agent 是否信任 Context Bundle 的信息？
  是否节省了探索代码库的时间？Context Bundle 是否有误导？）
```

---

## 对比汇总

| 指标 | A 组（仅 Task） | B 组（Task + Bundle） | Δ |
|------|:---:|:---:|:---:|
| Test Pass Rate | ?/6 | ?/6 | |
| Constraint Compliance | ?/2 | ?/2 | |
| Requirement Coverage | ?/3 | ?/3 | |
| 返工次数 | ? | ? | |
| Agent 轮数 | ? | ? | |
| Prompt Tokens | ? | ? | |
| Completion Tokens | ? | ? | |

---

## 判定

| 判定条件 | 结果 | 判定 |
|---------|------|------|
| B 组 Test Pass Rate > A 组 | | |
| B 组 Constraint Compliance > A 组 | | |
| B 组 返工次数 < A 组 | | |
| **综合判断** | | ✅ 有效 / ⚠️ 无效 / ❌ 有害 |
