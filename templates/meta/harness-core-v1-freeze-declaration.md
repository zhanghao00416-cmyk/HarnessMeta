# Harness Core v1.0 Freeze Declaration

> **冻结日期**：2026-06-25
> **冻结执行人**：AI Agent（harness-meta 维护）
> **冻结范围**：Harness Core v1.0 全部协议层 + 全部已验证运行时组件
> **解冻条件**：触发 Core Change Policy 的 MAJOR 变更流程
> **状态**：✅ **Frozen**

---

## 1. 冻结声明

Harness Core v1.0 是 harness-meta 项目的核心运行时和协议层。自本声明发布之时起，以下组件进入 Frozen 状态：

### 1.1 Frozen Schemas（协议层）

| # | Schema | 文件 | 版本 | 冻结阶段 | 冻结依据 |
|---|--------|------|------|---------|---------|
| 1 | Context Contract | `templates/context-schema.yaml` | v1.0-frozen | Phase 1 | Phase 1.5 验证通过 |
| 2 | Artifact Meta Schema | `templates/meta/artifact-meta-schema.yaml` | v1.0-frozen | Phase 2 | Chain Review v2.0（9.25/10） |
| 3 | Spec Schema | `templates/meta/spec-schema.yaml` | v1.0-frozen | Phase 2 | Chain Review v2.0 |
| 4 | Task Schema | `templates/meta/task-schema.yaml` | v1.0-frozen | Phase 2 | Chain Review v2.0 |
| 5 | Architecture Schema | `templates/meta/architecture-schema.yaml` | v1.0-frozen | Phase 2 | Chain Review v2.0 |
| 6 | Verify Schema | `templates/meta/verify-schema.yaml` | v1.0-frozen | Phase 2.5 | Chain Review v2.5 + Consumer Review（4/4） |

### 1.2 Validated Runtime Components（运行时层）

| # | Component | 核心文件 | 验证结果 | 验证阶段 |
|---|-----------|---------|---------|---------|
| 1 | Context Engine | `skills/harness-context/SKILL.md` v2.0 | 8/8 resolved, Budget 93.2% | Phase 3 |
| 2 | Rule-Based Planner | `templates/meta/planner/` | 30/30 scenarios, 100% accuracy | Phase 4 |
| 3 | Runtime Executor | `templates/meta/runtime/` | 55/55 tests, 100% accuracy | Phase 5 |
| 4 | E2E Integration | `tests/e2e/` | 5/5 flows, all passing | Phase 5.5 |

### 1.3 Frozen Skills（已接入 Core 协议）

| Skill | 角色 | 接入的 Core 组件 |
|-------|------|----------------|
| harness-verify | 聚合消费者 | Verify Schema v1.0-frozen |
| harness-runtime-verify | 执行消费者 | Verify Schema + Runtime Executor |
| harness-review-loop | 约束消费者 | Verify Schema + Context Engine |
| harness-analyze | 预检消费者 | Verify Schema + Context Engine |
| harness-context | 上下文构建 | Context Engine（P0/P1/P2） |
| harness-execute | 工单执行 | Context Engine + Runtime + Planner |
| harness-apply | 变更实现 | Context Engine + Runtime + Planner |

---

## 2. Harness Core 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                    Harness Core v1.0                         │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Protocol Layer (Frozen)                  │  │
│  │                                                       │  │
│  │  Context Contract ─── 统一上下文变量协议               │  │
│  │  Artifact Meta     ─── 产物身份 + 引用完整性          │  │
│  │  Spec Schema       ─── 业务规格（What）               │  │
│  │  Task Schema       ─── 实现工单（How）                │  │
│  │  Architecture      ─── 架构约束（Constraints）        │  │
│  │  Verify Schema     ─── 闭环验证（V1-V6 规则）         │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Runtime Layer (Validated)                   │  │
│  │                                                       │  │
│  │  Context Engine  ─── 自动遍历 V1/V2/V3 引用链        │  │
│  │  Planner         ─── 确定性路由（Flow A/B/C）         │  │
│  │  Runtime         ─── 10 状态执行状态机               │  │
│  │  Retry Policy    ─── 相同错误检测 + 防循环           │  │
│  │  E2E Loop        ─── Planner→Context→Runtime→Verify   │  │
│  └──────────────────────────────────────────────────────┘  │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Skill Layer (20 Skills)                  │  │
│  │                                                       │  │
│  │  Flow A: init → clarify → specify → arch → order     │  │
│  │          → analyze → context → execute                │  │
│  │          → review → runtime-verify → verify           │  │
│  │          → project-memory → archive                   │  │
│  │                                                       │  │
│  │  Flow B: explore → change → apply → verify → archive  │  │
│  │  Flow C: adopt-scan → context-index → adopt-spec      │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 核心闭环链路

```
Feature (project.yaml)
    ↓
Spec (requirements → scenarios → acceptance_criteria)
    ↓ Task.requirement_refs + Task.validation_steps.acceptance_criteria_ids
Task (implementation_steps → validation_steps → DoD)
    ↓ Task.constraints.constraint_refs
Architecture (constraints → modules → interfaces)
    ↓
[Context Engine] → context_bundle.yaml
    ↓
[Planner] → next_skill
    ↓
[Runtime] → PENDING → BUILDING_CONTEXT → RUNNING → COMPLETED → VERIFYING → VERIFIED
    ↓
[Verify Schema] → coverage.* → checks → failures → recommendations
    ↓
Project State Update → Planner（下一轮）
```

---

## 3. 能力矩阵

### 3.1 协议能力（Protocol Capabilities）

| 能力 | 组件 | 状态 | 说明 |
|------|------|:--:|------|
| 统一上下文协议 | Context Contract | ✅ | 7 层变量层级，禁止直接使用旧变量名 |
| 产物身份标识 | Artifact Meta | ✅ | 全局唯一 ID + 类型限定 + 生命周期 |
| 需求规格定义 | Spec Schema | ✅ | REQ + Scenario + AC 三级结构 |
| 工单实现定义 | Task Schema | ✅ | requirement_refs + validation_steps + DoD |
| 架构约束定义 | Architecture Schema | ✅ | CON + MOD + ADR + traceability |
| 闭环验证 | Verify Schema | ✅ | V1-V6 规则 + 4 类 coverage |
| 结构化 ID 引用 | Artifact Meta Rules 6/7/8 | ✅ | REQ/AC/CON/MOD 四种 ID 格式 |
| 引用完整性校验 | V4 规则 | ✅ | 10 种跨 Artifact 引用验证 |
| 多轮验证迭代 | Verify Schema iteration | ✅ | N 轮 Verify → Fix → Re-verify |
| 验证失败追溯 | failures + fix_path | ✅ | 每个失败可追溯到根因和修复路径 |

### 3.2 运行时能力（Runtime Capabilities）

| 能力 | 组件 | 状态 | 说明 |
|------|------|:--:|------|
| 自动上下文构建 | Context Engine | ✅ | V1/V2/V3 路径自动解析 + Budget 控制 |
| 确定性路由 | Planner | ✅ | 3 种 Flow（A/B/C）+ 可选 Skill 推荐 |
| 执行状态机 | Runtime | ✅ | 10 状态生命周期 + 非法迁移拒绝 |
| 重试管理 | Retry Policy | ✅ | 可重试/不可重试分类 + 相同错误检测 |
| 死循环防护 | Retry Policy | ✅ | 连续 2 次相同错误 → 终止 |
| 端到端闭环 | E2E Integration | ✅ | Planner→Context→Runtime→Verify 自动循环 |
| 上下文预算控制 | P2 Budget | ✅ | P2→P1→P0 优先级裁减 |
| 审计追踪 | resolve_trace | ✅ | 每条引用的解析结果可追溯 |

### 3.3 工程化能力（Engineering Capabilities）

| 能力 | 状态 | 说明 |
|------|:--:|------|
| Schema Change Policy | ✅ | SemVer（PATCH/MINOR/MAJOR）+ RFC 流程 |
| 分维度词汇表策略 | ✅ | 架构约束/运行时/问题严重度各自词汇表 |
| 验证框架（30+55+5=90 测试） | ✅ | Planner/Runtime/E2E 全覆盖 |
| 字节状态保证 | ✅ | 所有文件 UTF-8 干净，无 BOM 损坏 |
| 测试数据工厂 | ✅ | 300 REQ + 80 CON 的大规模合成数据 |

---

## 4. Core 与 Extension 边界

### 4.1 Core（冻结管理）

以下属于 Harness Core v1.0，任何修改需走 Core Change Policy：

| 层级 | 组件 | 理由 |
|------|------|------|
| 协议 | Context Contract v1.0-frozen | 所有 Skill 的基础契约 |
| 协议 | Artifact Meta Schema v1.0-frozen | 产物身份标识 |
| 协议 | Spec Schema v1.0-frozen | 需求定义 |
| 协议 | Task Schema v1.0-frozen | 工单定义 |
| 协议 | Architecture Schema v1.0-frozen | 约束定义 |
| 协议 | Verify Schema v1.0-frozen | 验证标准 |
| 运行时 | Context Engine（P0/P1/P2） | 上下文构建算法 |
| 运行时 | Planner（路由规则） | 确定性决策逻辑 |
| 运行时 | Runtime（状态机） | 执行生命周期 |
| 运行时 | Retry Policy | 重试决策逻辑 |
| 治理 | Core Change Policy | 修改流程 |
| 治理 | Core Freeze Declaration | 冻结范围 |

### 4.2 Extension（Phase 6+ 可扩展）

以下不属于 Core，可以作为 Extension 在后续阶段开发：

| 组件 | 说明 | 优先级 |
|------|------|:----:|
| Project Memory Engine | 跨项目经验积累与复用 | P1 |
| Multi-Agent Orchestrator | 多 Agent 协作编排 | P1 |
| Runtime Auto-Execute | 自动执行 validation_steps 命令 | P2 |
| Capability Discovery | Skill 能力自动发现 | P2 |
| Unified State Dashboard | 统一项目状态可视化 | P3 |
| Plugin System | 第三方 Skill 接入框架 | P3 |
| Performance Profiler | 上下文构建性能分析 | P3 |

---

## 5. Core Change Policy

### 5.1 修改分类

| 类型 | 场景 | 版本号 | 审批 | 示例 |
|------|------|--------|------|------|
| **PATCH** | 兼容性修复 | v1.0.x | 单人 review | 修正注释/拼写/示例 |
| **MINOR** | 新增可选字段/Skill/路由规则 | v1.x.0 | 维护者 review | 新增 Flow D、新增 coverage 字段 |
| **MAJOR** | 删除字段/修改语义/修改状态机 | vx.0.0 | RFC + 7天讨论 + 投票 | 删除 V1 规则、修改 ID 格式 |

### 5.2 修改 Core 的流程

```
提交变更提案
    ↓
分类（PATCH / MINOR / MAJOR）
    ↓
PATCH → 单人 review → 合并
MINOR → 维护者 review → 更新 CHANGELOG → 合并
MAJOR → RFC 文档 → 7 天社区讨论 → 投票 → 迁移指南 → 合并
    ↓
更新 Freeze Declaration
    ↓
如果涉及 Runtime：重新运行全部验证（Planner 30 + Runtime 55 + E2E 5）
```

### 5.3 修改 Extension 的流程

Extension 不受 Core Change Policy 约束。可自由迭代，但必须满足：

- 不修改任何 Core 组件
- 不新增 Frozen Schema（除非走 Core MINOR/MAJOR 流程）
- 通过自身验证（Validation Plan）

---

## 6. 缺口分析

### 6.1 架构缺口

| 缺口 | 影响 | 严重度 |
|------|------|:----:|
| **无跨项目记忆** | 每个项目从零开始，不积累经验 | 中 |
| **无 Multi-Agent 编排** | 单 Agent 执行，无法并行 | 低 |
| **无自动命令执行** | Runtime Verify 仍需人工运行命令 | 中 |
| **无 Skill 能力发现** | Planner 依赖硬编码的 Skill 链 | 低 |
| **无项目状态可视化** | project_state 仅通过文件查看 | 低 |
| **无 Plugin/Extension 机制** | 第三方无法扩展 Skill | 低 |

### 6.2 工程化缺口

| 缺口 | 影响 | 严重度 |
|------|------|:----:|
| **无 CI/CD 集成** | 验证依赖手动运行 | 中 |
| **无性能基准** | 不知道大规模项目的 Context Builder 耗时 | 低 |
| **无真实项目验证** | 所有测试基于合成数据，未在真实项目上跑过 | 高 |
| **无版本兼容性矩阵** | Schema 版本升级后不知道哪些 Skill 受影响 | 中 |
| **无文档生成器** | 所有文档手工编写 | 低 |

---

## 7. 竞品对比

### 7.1 对比维度

| 维度 | harness-meta v1.0 | OpenSpec | Spec-Kit | Claude Code | Codex CLI |
|------|:---:|:---:|:---:|:---:|:---:|
| **结构化 Spec** | ✅ Spec Schema | ✅ | ✅ | ❌（prompt 驱动） | ❌ |
| **结构化 Task** | ✅ Task Schema | ❌（平铺） | ❌ | ❌ | ❌ |
| **引用完整性** | ✅ V4 规则 | ❌ | ❌ | ❌ | ❌ |
| **自动上下文构建** | ✅ Context Engine | ❌ | ❌ | ❌ | ❌ |
| **确定性路由（Planner）** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **执行状态机** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **闭环验证** | ✅ V1-V6 | ❌ | ❌ | ❌ | ❌ |
| **覆盖率计算** | ✅ 4 类 | ❌ | ❌ | ❌ | ❌ |
| **重试 + 防死循环** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Agent 集成** | ✅ Skill 链 | ❌（工具链） | ❌ | ✅（原生 Agent） | ✅（原生 Agent） |
| **多语言支持** | ✅（纯 Markdown/YAML） | ✅ | ✅ | ✅ | ✅ |
| **LLM 无关** | ✅ | ✅ | ✅ | ❌（绑定 Claude） | ❌（绑定 OpenAI） |
| **冻结治理** | ✅ Core Change Policy | ❌ | ❌ | ❌ | ❌ |
| **Schema 版本管理** | ✅ SemVer | ❌ | ❌ | ❌ | ❌ |

### 7.2 Harness Core 的差异化优势

1. **协议层冻结**：6 个 Frozen Schema，版本化治理。OpenSpec/Spec-Kit 无版本管理。
2. **引用完整性**：V4 规则校验 10 种跨 Artifact 引用。竞品无此能力。
3. **确定性路由**：Planner 基于 30 个验证场景的规则引擎。竞品靠 prompt 驱动。
4. **执行可观测**：resolve_trace 记录每条引用的解析结果。竞品执行过程黑盒。
5. **防死循环**：Retry Policy 的相同错误检测。竞品可能无限重试。
6. **LLM 无关**：纯 Markdown/YAML，Claude/GPT/Qwen/GLM 均可使用。Claude Code/Codex 绑定特定模型。

### 7.3 Harness Core 的劣势

1. **无原生 Agent 执行**：Planner 和 Runtime 是设计层的，不包含真实 Agent 调用。Claude Code/Codex 是原生 Agent。
2. **无实时反馈**：验证依赖人工运行命令。Claude Code 可以实时执行命令并看到结果。
3. **社区/生态**：OpenSpec 有 GitHub 生态，Spec-Kit 有 VS Code 插件。harness-meta 无。
4. **学习曲线**：6 个 Schema + 20 个 Skill 的概念密度高于竞品。

---

## 8. Phase 6 是否必要？

### 8.1 Phase 6 的目标（按原计划）

> Phase 6: Project Memory — 跨项目经验积累与复用。

### 8.2 评估

| 有利因素 | 不利因素 |
|---------|---------|
| Project Memory 是当前最明显的架构缺口 | Core 刚冻结，稳定期未到 |
| 已有 harness-project-memory Skill 基础 | 需要新增 Schema（Memory Schema），违反"不新增 Schema"原则 |
| 竞品无此能力，差异化空间大 | 真实项目验证不足（缺口分析中的"高"严重度项） |
| 积累经验后可显著提升 Agent 成功率 | 扩展 Memory 前应先证明 Core 在真实项目中有效 |

### 8.3 建议

**Phase 6 不是当前最高优先级。** 建议在进入 Phase 6 前，先完成：

1. **Core 稳定期**（1-2 个月）：不新增功能，只修 Bug
2. **真实项目验证**（2-3 个月）：找 2-3 个真实项目跑通 Core 全流程
3. **工程化补缺**（1 个月）：CI/CD、性能基准、兼容性矩阵

如果以上三项完成且 Core 被证明在真实项目中有效，再评估 Phase 6 的启动时机。

---

## 9. 未来 12 个月 Roadmap 建议

### Q1（2026 Q3）：Core 稳定期

```
目标：不新增功能。修复 Bug。完善文档。
├── 真实项目验证（2-3 个项目跑通完整 Flow A）
├── 修复验证中发现的 Bug
├── 性能基准（Context Builder 在 300+ REQ 项目中的表现）
├── 字节状态自动检测 CI
└── 用户文档（USAGE.md 更新为 Core v1.0 版本）
```

### Q2（2026 Q4）：工程化 + Extension 启动

```
目标：降低使用门槛。启动最优先的 Extension。
├── CI/CD 集成（GitHub Actions 自动运行验证）
├── 版本兼容性矩阵（Schema 升级影响分析工具）
├── Extension: Real-World Validation Toolkit
│   └── 自动检测项目是否符合 Schema 的工具
├── Extension: Performance Monitor
│   └── Context Builder 耗时追踪
└── 社区建设（GitHub Discussions + 示例项目）
```

### Q3（2027 Q1）：Extension 扩展

```
目标：证明 Core 的价值。准备 Phase 6。
├── Extension: Project Memory Engine (Phase 6 启动)
│   ├── Memory Schema 设计（作为 Extension，不进入 Core）
│   ├── Cross-Project Pattern Extraction
│   └── 验证（独立于 Core 的验证套件）
├── Extension: Multi-Agent Orchestrator（如需要）
└── 案例研究（真实项目的 before/after 对比）
```

### Q4（2027 Q2）：生态 + 标准化

```
目标：扩大影响。标准化协议。
├── Plugin/Extension API 设计
├── 第三方 Skill 市场（Community Skills）
├── Harness Protocol v1.0 标准化提案
└── 与 OpenSpec/Spec-Kit 的互操作方案
```

---

## 10. 冻结签核

**Harness Core v1.0 冻结范围确认**：

- [x] 6 个 Frozen Schema
- [x] 4 个 Validated Runtime Components
- [x] 90 个验证测试（30 Planner + 55 Runtime + 5 E2E）
- [x] 3 种 Flow（A/B/C）全链路验证
- [x] Core Change Policy 生效
- [x] Core/Extension 边界明确
- [x] 缺口分析完成
- [x] 竞品对比完成
- [x] 12 个月 Roadmap 建议

**冻结执行**：AI Agent（harness-meta 维护）
**冻结日期**：2026-06-25
**下一次审查**：2026-Q3 结束后（基于真实项目验证结果）

---

> **Harness Core v1.0 正式冻结。协议层（6 Schema）+ 运行时层（4 Component）已冻结。未来 3 个月聚焦稳定性和真实项目验证，不新增功能。**
