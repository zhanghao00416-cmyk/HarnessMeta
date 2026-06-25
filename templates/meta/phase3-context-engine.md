# Phase 3：Context Engine

> **状态**：设计中（2026-06-24）
> **前置**：Phase 2.5 Verify Schema v1.0-frozen
> **核心命题**：协议层已完成。Phase 3 回答"协议如何被消费"。

---

## 1. 定位

### 1.1 问题

Phase 2.5 冻结后，harness-meta 有：

- 6 个 Frozen Schema（Context + Artifact Meta + Spec + Task + Architecture + Verify）
- 4 个 Consumer Skill（verify / runtime-verify / review-loop / analyze）
- 完整的引用追踪链路（REQ → AC → CON → VAL）

但 **Agent 仍然无法直接消费这些协议**。

harness-context 当前的工作方式：

```
用户 → 手工指定 file_list → harness-context → context.md → 交给 Agent
```

问题：Agent 不知道去哪里找 Spec、Architecture、Constraint。每次执行需要人工"喂"上下文。

### 1.2 目标

```
给定一个 Task ID
    ↓
Context Builder（自动遍历 Frozen Schema 引用链）
    ↓
Context Bundle（Agent 可直接消费的结构化上下文）
    ↓
Agent 执行
    ↓
Verify 成功
```

如果这条链路跑通，Phase 3 完成。

### 1.3 不做什么

| 范围 | 决策 |
|------|------|
| ❌ 设计新 Schema | 6 个 Frozen Schema 足够 |
| ❌ 新增大量 Skill | 升级 1 个现有 Skill（harness-context） |
| ❌ 统一状态 / 能力发现 / 并行执行 | 属于 Phase 3 后续，不是当前重点 |
| ✅ 自动遍历引用链 | P1 Resolver |
| ✅ 控制上下文大小 | P2 Budget |
| ✅ 生成结构化 Bundle | P0 Builder |

---

## 2. 架构

### 2.1 三组件关系

```
                    ┌──────────────────────┐
                    │   harness-context     │
                    │   (Context Builder)   │
                    │        v2.0           │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            ▼                  ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ P0 Builder   │  │ P1 Resolver  │  │ P2 Budget    │
    │ 结构化输出    │  │ 引用链追踪   │  │ 上下文裁剪   │
    └──────────────┘  └──────────────┘  └──────────────┘
```

三个组件不是三个 Skill。它们是一个 Skill 的三个内部阶段。

### 2.2 数据流

```
输入：task_id = "F22-order-001"
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│ P1 Resolver：遍历 Frozen Schema 引用链            │
│                                                   │
│  1. 读 Task artifact                             │
│     ├── requirement_refs[]                        │
│     │   └── → Spec.requirements[]  (V1 路径)      │
│     ├── validation_steps[].acceptance_criteria_ids│
│     │   └── → Spec.acceptance_criteria[] (V2 路径)│
│     └── constraints.constraint_refs[]              │
│         └── → Architecture.constraints[] (V3 路径) │
│                                                   │
│  2. 读 Spec artifact（从 dependency 找到路径）     │
│  3. 读 Architecture artifact（从 dependency 找到） │
│  4. 读 project.yaml / progress.md / session.md    │
│  5. 读 ADR / Memory（如有）                       │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ P2 Budget：控制上下文规模                           │
│                                                   │
│  max_tokens: 30000                                │
│  reserve_tokens: 5000 (给 Agent 响应)             │
│  available_tokens: 25000                          │
│                                                   │
│  策略：                                           │
│  1. P0 优先级最高（Task + 直接引用的内容）         │
│  2. P1 优先级（间接引用）                          │
│  3. P2 优先级（ADR / Memory / 项目状态）           │
│  4. 超出时：从 P2 开始裁减，向上逐级裁剪           │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────┐
│ P0 Builder：生成 context_bundle.yaml               │
│                                                   │
│  包含：                                           │
│  - task（完整）                                    │
│  - requirements（已解析，含嵌套 AC/场景）           │
│  - acceptance_criteria（已解析）                   │
│  - constraints（已解析，含 severity）               │
│  - validation_steps（从 Task 直接取）               │
│  - project_state（架构规则 + 活跃工单）             │
│  - memory（ADR + 约定）                            │
│  - budget（使用量 + 裁减清单）                      │
│  - resolve_trace（每条引用的解析结果）              │
└──────────────────────┬───────────────────────────┘
                       │
                       ▼
输出：context_bundle.yaml + context.md（人类可读版）
```

---

## 3. 核心数据结构

### 3.1 context_bundle.yaml（P0 输出）

```yaml
context_bundle:
  meta:
    task_id: "F22-order-001"
    generated_at: "2026-06-24T18:00:00+08:00"
    version: "2.0"
    source_skill: "harness-context"
    source_task: "orders/F22-order-001/order.md"

  # ── P1 解析结果 ──

  task:
    id: "F22-order-001"
    title: "邮件通知发送"
    description: "实现 SMTP 邮件发送功能"
    status: "active"
    feature_id: "F22"
    domain: "notification"
    dependencies: ["F22-specs", "notification-architecture"]

  requirements:
    - id: "REQ-NOT-001"
      title: "用户可接收邮件通知"
      description: "系统应支持通过 SMTP 向用户发送邮件通知"
      source:
        artifact_id: "F22-specs"
        field_path: "spec.requirements[0]"
      scenarios:
        - id: "SC-NOT-001"
          description: "用户触发通知后收到邮件"
          acceptance_criteria:
            - id: "AC-NOT-001"
              description: "邮件在 5 秒内送达"
            - id: "AC-NOT-002"
              description: "邮件包含正确的标题和正文"

    - id: "REQ-NOT-002"
      title: "邮件发送失败时重试"
      description: "SMTP 发送失败时应自动重试 3 次"
      source:
        artifact_id: "F22-specs"
        field_path: "spec.requirements[1]"
      scenarios: []

  acceptance_criteria:
    - id: "AC-NOT-001"
      description: "邮件在 5 秒内送达"
      source:
        artifact_id: "F22-specs"
        field_path: "spec.acceptance_criteria[0]"
      covered_by_steps: ["VAL-F22-001-001"]

    - id: "AC-NOT-002"
      description: "邮件包含正确的标题和正文"
      source:
        artifact_id: "F22-specs"
        field_path: "spec.acceptance_criteria[1]"
      covered_by_steps: ["VAL-F22-001-002"]

  constraints:
    - id: "CON-NOT-001"
      description: "Service 层不得直接访问数据库"
      severity: "must"
      source:
        artifact_id: "notification-architecture"
        field_path: "architecture.constraints[0]"

  validation_steps:
    - id: "VAL-F22-001-001"
      type: "unit_test"
      description: "测试邮件发送速度"
      command: "pytest tests/test_notification.py::test_send_email_speed -v"
      acceptance_criteria_ids: ["AC-NOT-001"]

    - id: "VAL-F22-001-002"
      type: "unit_test"
      description: "测试邮件内容正确性"
      command: "pytest tests/test_notification.py::test_email_content -v"
      acceptance_criteria_ids: ["AC-NOT-002"]

  # ── 项目状态 ──

  project_state:
    name: "通知推送系统"
    stack:
      backend: "FastAPI"
      database: "PostgreSQL"
    architecture_rules:
      - "Service 层负责业务逻辑，不得直接操作数据库"
      - "所有 API 返回标准 JSON 格式"
    active_orders: ["F22-order-001", "F22-order-002"]
    session:
      next_step: "继续执行 F22-order-001 阶段 2"

  # ── 记忆 ──

  memory:
    adr:
      - id: "ADR-001"
        title: "选择 SMTP 而非第三方 API"
        decision: "使用标准 SMTP 协议发送邮件，不依赖 SendGrid/AWS SES"
    conventions:
      - "使用 Repository Pattern 访问数据库"
      - "错误码必须注册到 ERROR_CODE.md"

  # ── P2 预算 ──

  budget:
    max_tokens: 30000
    used_tokens: 18500
    reserve_tokens: 5000
    available_tokens: 25000
    truncated: []

  # ── 解析追踪（审计） ──

  resolve_trace:
    - source: "task.requirement_refs[0].requirement_id"
      target: "spec.requirements.REQ-NOT-001"
      status: "resolved"
      artifact: "F22-specs"

    - source: "task.constraints.constraint_refs[0]"
      target: "architecture.constraints.CON-NOT-001"
      status: "resolved"
      artifact: "notification-architecture"

    - source: "task.validation_steps[0].acceptance_criteria_ids[0]"
      target: "spec.acceptance_criteria.AC-NOT-001"
      status: "resolved"
      artifact: "F22-specs"
```

### 3.2 字段与 Frozen Schema 的对应

| context_bundle 字段 | 来源 | Frozen Schema 引用 |
|---------------------|------|-------------------|
| `task` | 直接读取 Task artifact | Task Schema v1.0-frozen |
| `requirements` | `task.requirement_refs[]` → Spec | Spec Schema v1.0-frozen（V1 路径） |
| `acceptance_criteria` | `validation_steps.acceptance_criteria_ids[]` → Spec | Spec Schema v1.0-frozen（V2 路径） |
| `constraints` | `task.constraints.constraint_refs[]` → Architecture | Architecture Schema v1.0-frozen（V3 路径） |
| `validation_steps` | 直接读取 Task artifact | Task Schema v1.0-frozen |
| `project_state` | project.yaml + ARCHITECTURE.md | Context Contract v1.0-frozen |
| `memory` | `docs/memory/` + `harness-project-memory` 输出 | 无（运行时聚合） |
| `budget` | P2 计算 | 无（运行时控制） |
| `resolve_trace` | P1 解析日志 | 无（审计追踪） |

---

## 4. P1 Context Resolver 详细设计

### 4.1 核心算法

```
输入：task_id
输出：requirements[], acceptance_criteria[], constraints[], resolve_trace[]

步骤：
  1. 读取 Task artifact
     ├── 定位文件：orders/{task_id}/order.md 或 tasks/{task_id}.yaml
     └── 提取：requirement_refs[], validation_steps[], constraints

  2. resolve_requirements(task):
     for each ref in task.requirement_refs:
       req_id = ref.requirement_id
       spec_artifact = 从 task.dependencies 找到 spec artifact
       加载 spec 文件
       定位 requirements[req_id]
       提取 requirement + 嵌套 scenarios + 嵌套 acceptance_criteria
       记录 resolve_trace

  3. resolve_acceptance(task):
     for each step in task.validation_steps:
       for each ac_id in step.acceptance_criteria_ids:
         spec_artifact = 从 task.dependencies 找到 spec artifact
         加载 spec 文件
         定位 acceptance_criteria[ac_id]
         提取 AC
         记录 resolve_trace

  4. resolve_constraints(task):
     for each con_id in task.constraints.constraint_refs:
       arch_artifact = 从 task.dependencies 找到 architecture artifact
       加载 architecture 文件
       定位 constraints[con_id]
       提取 constraint + severity
       记录 resolve_trace

  5. 去重（同一个 AC 可能被多个 validation_step 引用）
  6. 返回结构化结果
```

### 4.2 解析失败处理

| 失败类型 | 状态 | 处理 |
|---------|------|------|
| Task artifact 不存在 | `unresolved` | 报错，返回空 bundle |
| requirement_ref 指向不存在的 REQ ID | `broken_ref` | 记录到 resolve_trace，跳过该条 |
| Spec artifact 未在 dependency 中声明 | `missing_dep` | 记录到 resolve_trace，尝试推断路径 |
| Architecture artifact 路径错误 | `path_error` | 记录到 resolve_trace，尝试搜索 |

### 4.3 解析追踪格式

```yaml
resolve_trace:
  - source: "task.requirement_refs[0].requirement_id"
    target: "spec.requirements.REQ-NOT-001"
    status: "resolved"        # resolved | broken_ref | missing_dep | path_error
    artifact: "F22-specs"
    file: "docs/specs/notification/spec.md"
    line: 234
    resolved_at: "2026-06-24T18:00:00+08:00"
```

---

## 5. P2 Context Budget 详细设计

### 5.1 预算模型

```yaml
budget:
  # 硬限制
  max_tokens: 30000         # context_bundle 总 token 上限
  reserve_tokens: 5000      # 留给 Agent 响应的 token
  available_tokens: 25000   # = max_tokens - reserve_tokens

  # 使用量
  used_tokens: 18500
  utilization: 0.74          # used / available

  # 裁减
  truncated:
    - section: "memory.adr"
      item: "ADR-003"
      reason: "超出预算（P2 优先级）"
```

### 5.2 优先级与裁减顺序

| 优先级 | 内容 | 理由 | 裁减顺序 |
|--------|------|------|---------|
| **P0（不可裁）** | task.description, requirements[].description | Agent 执行必须知道"做什么" | 最后裁 |
| **P1（尽量保留）** | acceptance_criteria[], constraints[], validation_steps[] | Agent 验证必须知道"标准" | 倒数第二裁 |
| **P2（优先裁）** | project_state.architecture_rules, memory.adr, memory.conventions | 有帮助但不是必须 | 最先裁 |

### 5.3 裁减算法

```
输入：context_bundle（已填充）, max_tokens
输出：context_bundle（已裁减）

步骤：
  1. 计算当前 token 数
  2. 如果 < max_tokens：直接返回
  3. 按优先级从低到高裁减：
     a. P2：从 memory 开始，逐条删除（保留最近的 ADR）
     b. P2：裁减 project_state（保留 name + stack，删除 rules）
     c. P1：裁减 acceptance_criteria.description（保留 id + key）
     d. P0：截断 requirements[].description（保留前 200 字）
  4. 每裁减一条，检查是否满足 max_tokens
  5. 记录裁减清单到 budget.truncated
```

### 5.4 Token 估算

context_bundle 主要是 YAML 文本，token 估算公式：

```
estimated_tokens ≈ byte_count / 4   (中文约 1.5-2 token/字，保守取 2)
```

**典型场景估算**：

| 内容 | 中文字数 | 估算 token |
|------|---------|-----------|
| task（描述 200 字） | 200 | 400 |
| requirements（3 条 × 300 字） | 900 | 1800 |
| acceptance_criteria（5 条 × 100 字） | 500 | 1000 |
| constraints（3 条 × 80 字） | 240 | 480 |
| validation_steps（5 条 × 60 字） | 300 | 600 |
| project_state | 400 | 800 |
| memory（2 ADR + 3 conventions） | 600 | 1200 |
| **合计** | **3140** | **~6280** |

> 结论：典型 Task 的 context_bundle 约 6000-8000 token，远低于 25000 上限。预算机制主要防止极端情况（如 20+ 条 requirement 的项目）。

---

## 6. 实施计划

### 6.1 实施策略

```
Phase 3.1：升级 harness-context v2.0
  ├── 新增 Step 1-5：P1 Resolver（引用链自动追踪）
  ├── 新增 Step 8：P0 Builder（context_bundle.yaml 生成）
  ├── 新增 Step 9：P2 Budget（上下文大小控制）
  └── 保留现有 context.md 生成（人类可读）

Phase 3.2：验证
  ├── 找一个真实项目（如 harness-meta 自身）
  ├── 用 Context Builder 为一个 Task 生成 context_bundle
  ├── 将 context_bundle 交给 Agent
  └── 验证 Agent 能否完成任务
```

### 6.2 harness-context v2.0 变更概要

| 变更项 | v1.x | v2.0 |
|--------|------|------|
| 输入 | 手工指定 file_list | 精确 task_id |
| 规格定位 | 按 domain 搜索 | 自动遍历 requirement_refs（V1） |
| AC 定位 | 不定位 | 自动遍历 acceptance_criteria_ids（V2） |
| 约束定位 | 按文件类型匹配 | 自动遍历 constraint_refs（V3） |
| 输出 | context.md（纯文本） | context_bundle.yaml + context.md |
| 预算 | 硬编码 30000 token | P2 Budget 模型（优先级裁减） |
| 审计 | 无 | resolve_trace（每条引用的解析结果） |

### 6.3 与现有 Skill 的关系

```
harness-execute（不变）
    ↓ 调用
harness-context v2.0（升级）
    ├── P1 Resolver：自动追踪引用链
    ├── P0 Builder：生成 context_bundle.yaml
    ├── P2 Budget：控制上下文大小
    └── 输出 context.md（人类可读版）
    ↓ 上下文交给
Agent（不变）
    ↓ 执行
harness-runtime-verify（不变）
    ↓ 填充
harness-verify（不变）
```

---

## 7. 验收标准

> **不以文档数量为验收标准**。以"真实链路跑通"为标准。

### 7.1 核心验收

```
真实 Task（如 harness-meta 项目的某个工单）
    ↓
harness-context v2.0 生成 context_bundle.yaml
    ↓
将 context_bundle 交给 Agent
    ↓
Agent 完成任务（写代码 / 修复 bug / 实现功能）
    ↓
harness-verify 验证通过（checks 全 pass）
```

### 7.2 技术验收

- [ ] P1 Resolver 正确解析所有 requirement_refs（V1 路径）
- [ ] P1 Resolver 正确解析所有 acceptance_criteria_ids（V2 路径）
- [ ] P1 Resolver 正确解析所有 constraint_refs（V3 路径）
- [ ] 引用断裂时 resolve_trace 记录 broken_ref（不崩溃）
- [ ] P0 Builder 生成有效的 context_bundle.yaml
- [ ] context_bundle 字段命名与 Verify Schema v1.0-frozen 一致
- [ ] P2 Budget 在超限时正确裁减（从 P2 优先开始）
- [ ] budget.truncated 记录所有裁减项
- [ ] context_bundle token 数 ≤ max_tokens
- [ ] 不修改任何 Frozen Schema

### 7.3 不强制验收（Phase 3 后续）

- [ ] 多个 Task 并行生成 context_bundle
- [ ] Capability Discovery
- [ ] Unified State
- [ ] Verify Runtime 自动执行

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| Task artifact 格式不统一 | P1 解析失败 | 优先支持 Task Schema v1.0-frozen，旧格式降级为手工模式 |
| 引用链断裂（broken_ref） | Agent 缺少上下文 | resolve_trace 记录断点，Agent 可据此判断 |
| context_bundle 过大 | Agent 无法消费 | P2 Budget 自动裁减 |
| Spec 文件路径不确定 | 找不到文件 | 从 task.dependencies 推断，失败时搜索 docs/specs/ |

---

## 9. 与 Phase 2.5 的关系

Phase 2.5 定义了"协议长什么样"。Phase 3 回答"协议怎么被用"。

```
Phase 2.5（协议层，已冻结）：
  Spec Schema    ─┐
  Task Schema    ─┼── 定义字段、引用格式、追踪路径
  Architecture   ─┤
  Verify Schema  ─┘

Phase 3（运行时层，本文档）：
  Context Builder ─── 遍历上述协议定义的引用链，生成可消费的上下文
```

**Phase 3 是 Phase 2.5 的第一个真实消费者**。

---

> **Phase 3 已于 2026-06-24 启动设计。**
> **核心原则：不增加新协议，只解决消费问题。**
# Phase 3：Context Engine

> **阶段**：规划中（2026-06-24 启动）
> **前序阶段**：Phase 2.5 Verify Schema v1.0-frozen
> **核心目标**：将 harness-meta 的能力从"协议层"扩展到"运行时能力层"
> **设计原则**：**不修改任何 Frozen Schema**，所有新增能力作为运行时层

---

## 1. Phase 3 定位

### 1.1 从协议层到运行时层

harness-meta 经历了三个发展阶段：

| 阶段 | 重点 | 产物 |
|------|------|------|
| **Phase 1** | Context Contract | 统一上下文协议（v1.0-frozen） |
| **Phase 2** | Artifact Schema 分层 | 4 层 Schema + 引用完整性（v1.0-frozen） |
| **Phase 2.5** | Verify Schema | 闭环验证 + 4 类 coverage（v1.0-frozen） |
| **Phase 3** | **Runtime Engine** | **运行时能力（不冻结）** |

### 1.2 为什么需要 Phase 3

Phase 2.5 完成了"协议层"的全部设计，但实际使用中仍存在以下痛点：

| 痛点 | 现状 | Phase 3 解决方式 |
|------|------|-----------------|
| **验证靠人工** | V6 规则需要人工运行 lint/test/build | Context Engine 自动执行 |
| **上下文靠手工** | harness-context 需手工指定 file_list | Context Engine 自动打包 |
| **能力靠记忆** | Skill 编排器需知道哪个 Skill 做什么 | Capability Discovery 自动发现 |
| **状态分散** | 工单状态、Verify 状态、Context 状态分散 | Unified State 统一追踪 |

### 1.3 Phase 3 的核心承诺

> **不修改任何 Frozen Schema**。Phase 3 引入的所有新能力作为**运行时层**叠加在 Frozen Schema 之上。

---

## 2. Phase 3 范围

### 2.1 四大组件

```
┌─────────────────────────────────────────────────────────┐
│                    Phase 3 Runtime Layer                  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Context    │  │   Verify     │  │  Capability  │ │
│  │   Engine     │  │   Runtime    │  │  Discovery   │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                  │                  │         │
│         └──────────────────┼──────────────────┘         │
│                            ↓                            │
│                  ┌──────────────────┐                   │
│                  │  Unified State   │                   │
│                  └──────────────────┘                   │
└─────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────┐
        │   Phase 2.5 Frozen Schema Layer    │
        │  (Verify Schema v1.0-frozen)      │
        └───────────────────────────────────┘
```

#### 2.1.1 Context Engine（上下文引擎）

**职责**：自动化上下文打包、跨 Skill 数据流。

**当前状态**：harness-context 需要手工指定 `file_list`、`api_contract`、`reference_module` 等参数。

**Phase 3 改进**：

- 自动扫描 Task 的 `requirement_refs`、`acceptance_criteria_ids`、`constraint_refs`
- 自动加载相关 Spec / Architecture / Memory 片段
- 自动计算"上下文最小集"（Minimal Viable Context）
- 输出统一的 `context_bundle.yaml`

**Frozen Schema 影响**：✅ 零影响（仅读取 Schema，不修改）

#### 2.1.2 Verify Runtime（验证运行时）

**职责**：自动化执行 V6 规则。

**当前状态**：harness-runtime-verify 需人工运行 lint/test/build 命令。

**Phase 3 改进**：

- 从 `task.validation_steps[]` 自动推断执行命令
- 实时填充 `context.validation_status_map`
- 支持并行执行（按 task_id 分组）
- 输出标准 `runtime-report.yaml`

**Frozen Schema 影响**：✅ 零影响（向 `context.validation_status_map` 写入，不修改 Schema）

#### 2.1.3 Capability Discovery（能力发现）

**职责**：自动发现 Skill 能力并支持组合。

**当前状态**：Skill 编排器需记住每个 Skill 的输入输出。

**Phase 3 改进**：

- 扫描 `skills/*/SKILL.md` 的 front matter（`name`、`description`、`inputs`、`outputs`）
- 构建 Skill Capability Graph（SCG）
- 支持"输入需求 → 自动推荐 Skill 组合"
- 输出 `capability-graph.yaml`

**Frozen Schema 影响**：🆕 新增 Capability Schema（**不冻结**，作为运行时描述）

#### 2.1.4 Unified State（统一状态）

**职责**：跨 Skill 状态追踪。

**当前状态**：`progress.md` / `session-handoff.md` / `feature_list.json` 三处分散维护。

**Phase 3 改进**：

- 统一状态模型：`feature` / `task` / `order` / `verify` / `context`
- 自动从 Artifact 的 `artifact.status` 字段同步
- 支持断点续跑（基于 `session.next_step`）
- 输出 `unified-state.yaml`

**Frozen Schema 影响**：✅ 零影响（复用 Artifact Meta Schema 的 `status` 字段）

### 2.2 不在 Phase 3 范围内

| 范围 | 说明 |
|------|------|
| ❌ 修改 Frozen Schema | Phase 2.5 已冻结，Phase 3 不得修改 |
| ❌ 新增 Schema 类型（冻结） | Phase 3 新增的 Schema 不进入 Frozen 状态 |
| ❌ 替换现有 Skill | Phase 3 仅增强现有 Skill，不重写 |
| ❌ 改变 Skill 接口 | Skill 的 front matter、输入输出不变 |

---

## 3. Phase 3 详细设计

### 3.1 Context Engine 设计

```yaml
# context_bundle.yaml（运行时产物，不冻结）
context_bundle:
  feature_id: F22
  task_id: F22-order-001
  generated_at: "2026-06-24T18:00:00+08:00"
  
  # 自动加载的上下文
  specs:
    - F22-specs                        # task.requirement_refs 引用
    - F22-specs.scenarios.SC-NOT-001   # acceptance_criteria_ids 引用
  
  architecture:
    - notification-architecture         # task.constraints.constraint_refs 引用
  
  memory:
    - memory/decision-001.md            # 自动关联的架构决策
    - memory/convention-002.md          # 自动关联的项目约定
  
  files:
    - src/services/notification.py      # 自动从 requirement_refs 推断
    - tests/test_notification.py
  
  # 上下文完整性自检
  completeness_check:
    spec_coverage: 1.0
    arch_coverage: 1.0
    file_coverage: 0.95
```

**核心算法**：

```
输入：Task artifact（task_id）
步骤：
  1. 读取 task.requirement_refs → 找到相关 specs
  2. 读取 task.validation_steps[].acceptance_criteria_ids → 找到相关 AC
  3. 读取 task.constraints.constraint_refs → 找到相关 architecture
  4. 从 requirement_refs 反推 file_list（通过 git blame 或约定）
  5. 从 memory 索引中找到相关决策和约定
输出：context_bundle.yaml
```

### 3.2 Verify Runtime 设计

```yaml
# runtime-report.yaml（运行时产物，不冻结）
runtime_report:
  task_id: F22-order-001
  executed_at: "2026-06-24T18:00:00+08:00"
  
  # 从 validation_steps 自动派生的执行计划
  execution_plan:
    - step_id: VAL-F22-001-001
      command: "pytest tests/test_notification.py::test_send_email -v"
      timeout: 60s
    - step_id: VAL-F22-001-002
      command: "ruff check src/services/notification.py"
      timeout: 30s
  
  # 实时填充的 status_map
  results:
    VAL-F22-001-001:
      status: passed
      exit_code: 0
      stdout: "..."
      duration_ms: 1234
    VAL-F22-001-002:
      status: passed
      exit_code: 0
      duration_ms: 567
  
  # 写入 Verify Report 的 validation_status_map
  status_map:
    VAL-F22-001-001: passed
    VAL-F22-001-002: passed
```

**核心算法**：

```
输入：Task artifact（task_id）
步骤：
  1. 读取 task.validation_steps[]
  2. 对每个 step，根据 type 派生 command：
     - unit_test → pytest/jest 路径
     - lint → ruff/eslint 路径
     - build → npm run build / cargo build
  3. 并行执行 commands
  4. 收集 exit_code + stdout/stderr
  5. 填充 validation_status_map
输出：runtime-report.yaml + 更新 Verify Report 的 validation_status_map
```

### 3.3 Capability Discovery 设计

```yaml
# capability-graph.yaml（运行时产物，不冻结）
capability_graph:
  generated_at: "2026-06-24T18:00:00+08:00"
  
  skills:
    - id: harness-verify
      role: aggregator
      inputs: [spec, tasks, architecture]
      outputs: [verify-report]
      consumes: [coverage.*, validation_status_map]
      
    - id: harness-runtime-verify
      role: executor
      inputs: [tasks]
      outputs: [runtime-report]
      consumes: [validation_steps]
      writes: [validation_status_map]
      
    - id: harness-review-loop
      role: constraint-checker
      inputs: [tasks, architecture]
      outputs: [review-report]
      consumes: [constraint_refs]
      
    - id: harness-analyze
      role: auditor
      inputs: [spec, tasks, architecture]
      outputs: [audit-report]
      consumes: [coverage.*]
  
  # 推荐链路
  recommended_chains:
    - name: full-verify
      steps: [harness-runtime-verify, harness-verify]
    - name: pre-execute-audit
      steps: [harness-analyze]
```

**核心算法**：

```
输入：skills/*/SKILL.md
步骤：
  1. 扫描 front matter（name、description、inputs、outputs）
  2. 解析 SKILL.md 内容提取 consumes/writes 关系
  3. 构建有向图（skill → skill，依赖关系）
  4. 拓扑排序生成推荐链路
输出：capability-graph.yaml
```

### 3.4 Unified State 设计

```yaml
# unified-state.yaml（运行时产物，不冻结）
unified_state:
  generated_at: "2026-06-24T18:00:00+08:00"
  
  # Feature 状态
  features:
    - id: F22
      status: in_progress
      total_tasks: 12
      completed_tasks: 8
      completion_rate: 0.667
      
  # Task 状态
  tasks:
    - id: F22-order-001
      status: passing
      verified: true
      coverage:
        requirement: 1.0
        acceptance: 1.0
        constraint: 1.0
        validation: 1.0
        
    - id: F22-order-002
      status: active
      verified: false
      
  # Context 状态
  context:
    last_bundle: F22-order-001
    last_generated: "2026-06-24T17:00:00+08:00"
    
  # Session 状态（断点续跑）
  session:
    last_skill: harness-execute
    next_step: "继续执行 F22-order-002 阶段 2"
    pause_point: "F22-order-002 line 234"
```

**核心算法**：

```
输入：项目目录 + progress.md + feature_list.json + 已有 artifacts
步骤：
  1. 扫描所有 artifacts，提取 status 字段
  2. 聚合到 features / tasks / context / session 四个维度
  3. 计算 derived 指标（completion_rate 等）
  4. 检测异常（stale tasks、broken refs 等）
输出：unified-state.yaml
```

---

## 4. Phase 3 与 Frozen Schema 的关系

### 4.1 严格边界

| Frozen Schema | Phase 3 访问方式 |
|---------------|-----------------|
| Context Contract v1.0-frozen | ✅ 只读消费（生成 context_bundle） |
| Artifact Meta Schema v1.0-frozen | ✅ 只读消费（提取 status、source） |
| Spec Schema v1.0-frozen | ✅ 只读消费（加载 requirements/AC） |
| Task Schema v1.0-frozen | ✅ 只读消费（读取 validation_steps） |
| Architecture Schema v1.0-frozen | ✅ 只读消费（加载 constraints） |
| Verify Schema v1.0-frozen | ✅ 读写消费（写入 validation_status_map） |

### 4.2 Runtime Schema（新增，不冻结）

Phase 3 引入的新 Schema 类型：

| Schema | 用途 | 冻结状态 |
|--------|------|---------|
| Capability Schema | 描述 Skill 能力 | ❌ 不冻结（运行时描述） |
| Context Bundle Schema | 上下文打包 | ❌ 不冻结（运行时产物） |
| Runtime Report Schema | 验证运行时输出 | ❌ 不冻结（运行时产物） |
| Unified State Schema | 统一状态 | ❌ 不冻结（运行时产物） |

**为什么不冻结**：

- Runtime Schema 描述的是**当前执行状态**，不是稳定的协议
- 频繁变化（如新增字段不应走 RFC）
- 仅供 harness-meta 内部消费

### 4.3 兼容性保证

Phase 3 完成后：

- ✅ 所有 Frozen Schema 保持 v1.0-frozen（Phase 1 / 2 / 2.5）
- ✅ 现有 Skill 接口不变（front matter、inputs、outputs）
- ✅ 现有 Artifact 结构不变（spec / task / architecture / verify-report）
- 🆕 新增 Runtime Layer（独立运行，不影响现有流程）

---

## 5. Phase 3 实施路径

### 5.1 分阶段实施

```
Phase 3.1 - Context Engine MVP（1-2 周）
  ├── context_bundle.yaml 生成器
  ├── 集成到 harness-context（增强模式）
  └── 文档：context-engine.md

Phase 3.2 - Verify Runtime MVP（2-3 周）
  ├── 自动 command 派生器
  ├── 并行执行引擎
  ├── 集成到 harness-runtime-verify
  └── 文档：verify-runtime.md

Phase 3.3 - Capability Discovery MVP（1 周）
  ├── SKILL.md front matter 扫描器
  ├── Capability Graph 生成器
  ├── 集成到 Skill 编排器
  └── 文档：capability-discovery.md

Phase 3.4 - Unified State MVP（1-2 周）
  ├── 状态聚合器
  ├── 断点续跑支持
  ├── 集成到 session-handoff
  └── 文档：unified-state.md
```

### 5.2 与 Phase 2/2.5 的边界

| 边界 | Phase 2/2.5（已冻结） | Phase 3（运行时） |
|------|---------------------|------------------|
| 修改频率 | 低（PATCH 偶尔） | 高（迭代频繁） |
| 修改流程 | Schema Change Policy | 直接修改 Runtime Schema |
| 影响范围 | 全部 Skill | 仅 Phase 3 组件 |
| 文档位置 | templates/meta/ | templates/runtime/（新增目录） |
| 版本号 | v1.0-frozen | v0.x-draft（持续迭代） |

---

## 6. Phase 3 验收标准

### 6.1 Context Engine

- [ ] 给定 Task artifact，自动生成 context_bundle.yaml
- [ ] context_bundle 包含所有 requirement_refs / acceptance_criteria_ids / constraint_refs 相关的上下文
- [ ] 生成的 context_bundle 可被 harness-execute 直接使用
- [ ] 不修改任何 Frozen Schema

### 6.2 Verify Runtime

- [ ] 给定 Task artifact，自动执行所有 validation_steps
- [ ] 实时填充 validation_status_map
- [ ] 支持并行执行（至少 4 个 task 并发）
- [ ] 输出 runtime-report.yaml

### 6.3 Capability Discovery

- [ ] 扫描所有 SKILL.md，生成 capability-graph.yaml
- [ ] 推荐链路在简单场景下 100% 准确
- [ ] 不修改任何 Frozen Schema

### 6.4 Unified State

- [ ] 给定项目目录，生成 unified-state.yaml
- [ ] 状态与 progress.md / session-handoff.md / feature_list.json 一致
- [ ] 支持断点续跑（基于 session.next_step）

---

## 7. Phase 3 风险与缓解

| 风险 | 影响 | 缓解策略 |
|------|------|---------|
| **运行时状态污染 Frozen Schema** | 高（破坏兼容性） | 严格分层：Runtime 写入 `validation_status_map` 等明确字段 |
| **并行执行引入竞态** | 中 | 按 task_id 分桶，每桶串行 |
| **command 派生错误** | 中 | 提供手动覆盖（用户可指定 custom_command） |
| **Context 膨胀** | 低 | 设置 token 上限，自动截断最旧 context |
| **Capability Graph 漂移** | 低 | 每次生成时重新扫描 SKILL.md |

---

## 8. 后续阶段（Phase 4+）

Phase 3 完成后，harness-meta 将具备：

- 协议层 ✅（Phase 1 / 2 / 2.5 Frozen）
- 运行时层 ✅（Phase 3）
- 智能体层 🆕（Phase 4+）

**Phase 4+ 方向**：

- Multi-Agent 协作（基于 Capability Graph）
- 自动决策引擎（基于 Unified State）
- 自适应 Skill 组合（基于历史 context）
- 项目级学习（基于 Memory Schema）

但这些都在 Phase 3 之后才考虑。**Phase 3 本身聚焦"运行时能力"，不涉及智能体决策**。

---

## 9. 启动检查清单

在开始 Phase 3 实施前，确认以下条件：

- [x] Phase 2 Frozen（2026-06-24）
- [x] Phase 2.5 Verify Schema Frozen（2026-06-24）
- [x] 4 个 Consumer Skill 已接入 Verify Schema
- [x] Consumer Review 通过（4/4 一致）
- [x] 字节状态干净（所有 SKILL.md 字节无问题字符）
- [ ] Phase 3 设计审查通过
- [ ] Runtime Schema 草案评审
- [ ] 现有项目验证（找一个 harness-meta 用户项目跑通 Phase 3）

---

## 10. 文档维护

| 文档 | 位置 | 更新频率 |
|------|------|---------|
| Phase 3 启动文档 | `templates/meta/phase3-context-engine.md` | 仅设计阶段 |
| Context Engine 文档 | `templates/runtime/context-engine.md` | 随 Phase 3.1 实施更新 |
| Verify Runtime 文档 | `templates/runtime/verify-runtime.md` | 随 Phase 3.2 实施更新 |
| Capability Discovery 文档 | `templates/runtime/capability-discovery.md` | 随 Phase 3.3 实施更新 |
| Unified State 文档 | `templates/runtime/unified-state.md` | 随 Phase 3.4 实施更新 |

---

> **Phase 3 已于 2026-06-24 启动规划。**
> **核心原则：不修改任何 Frozen Schema，仅在运行时层叠加新能力。**
