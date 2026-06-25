# harness-meta

> 用自然语言描述项目，通过 20 个 Skill 链驱动 AI 生成整套工程管理体系。

一套纯 Markdown/YAML 的元模板系统——不绑定任何 AI 工具，Qwen、GLM、Claude、GPT、Cursor、Copilot 均可使用。

---

## 核心理念

| 原则 | 说明 |
|------|------|
| 模板结构化 | 每个产出物有固定 section，AI 填充而非自由发挥 |
| 依赖图约束 | artifact 按 DAG 顺序生成，前驱不存在则阻塞 |
| 增量变更 | 变更只表达 delta，不重写全局 spec |
| 三段式执行 | 只读 → 写码 → 自审，防止跳步 |
| 断点续跑 | 每个 Skill 启动时扫描磁盘文件判断状态，支持新会话继续 |
| 工单三态流转 | not_started → active → passing，状态单一数据源 |
| LLM 无关 | 全部纯 Markdown/YAML，任何 AI 工具可用 |

---

## 快速开始

```
1. 把 harness-meta/ 目录内的文件复制到你的项目根目录（schemas/、skills/、templates/ 直接放在项目根目录，不要嵌套 harness-meta/ 文件夹）
2. 执行 /harness-init（AI 交互式引导，两轮对话生成 project.yaml + 项目骨架）
3. 继续执行 Skill 链
```

---

## 两套流程

### 流程 A：首次建项目（Greenfield）

```
harness-init → harness-init-docs → harness-clarify → harness-specify
    → harness-specify-arch → harness-order → [harness-analyze] → [harness-context] → harness-execute
    → [harness-review-loop] → [harness-runtime-verify] → harness-verify → [harness-project-memory] → harness-archive
```

| Skill | 做什么 |
|-------|--------|
| **harness-init** | 两轮对话创建 project.yaml + 项目目录 + 6 个核心 meta 文件 + feature_list.json |
| **harness-init-docs** | 生成 5 个工作流 meta 文件 + 规格目录骨架 |
| **harness-clarify** | 逐功能交互式提问，补全行为规格 |
| **harness-specify** | 按业务域生成规格文档 |
| **harness-specify-arch** | 生成 5 个架构规格 + 更新事实注册表 |
| **harness-order** | 按依赖图分批生成工单（>6 个自动分批） |
| **harness-analyze** | 跨文档一致性审计（6 维度，只读） |
| **harness-context** | 为工单打包执行上下文（规格+架构+文件+约束） |
| **harness-execute** | 按三段式执行工单写代码 |
| **harness-review-loop** | 迭代代码审查：审查 → Agent 修复 → 再审查（最多 3 轮） |
| **harness-runtime-verify** | 运行时验证：执行 lint/test/build 命令验证代码可运行（最多 3 轮修复） |
| **harness-verify** | 三维度验证（完整性/正确性/一致性），报告含修复路径 |

### 流程 B：后续改代码（Brownfield）

```
[harness-explore] → harness-change → harness-apply
    → [harness-review-loop] → [harness-runtime-verify] → harness-verify → harness-archive
```

| Skill | 做什么 |
|-------|--------|
| **harness-explore** | 需求不清时先探索（只读） |
| **harness-change** | 按 schema 类型生成变更文件夹（proposal 含 created frontmatter） |
| **harness-apply** | 按轻量三段式（只读分析→写码→自审）实现任务 |
| **harness-review-loop** | 迭代代码审查：审查 → Agent 修复 → 再审查（最多 3 轮） |
| **harness-runtime-verify** | 运行时验证：执行 lint/test/build 命令验证代码可运行 |
| **harness-verify** | 三维度验证（完整性/正确性/一致性），报告含修复路径 |
| **harness-project-memory** | 积累项目记忆：提取决策、约定、教训、技术画像（只追加，不删除历史） |
| **harness-archive** | 归档变更，合并增量规格到主规格（按 created 排序） |

### 流程 C：已有代码接入（Adopt）

```
harness-adopt-scan → harness-context-index → harness-adopt-spec → 后续改代码走 Flow B
```

| Skill | 做什么 |
|-------|--------|
| **harness-adopt-scan** | 扫描代码库，反推 project.yaml + meta 文件（全部 passing） |
| **harness-context-index** | 构建项目索引（文件索引 / 域映射 / 依赖图） |
| **harness-adopt-spec** | 从代码反推域规格 + 架构规格 + 工作流 meta 文件 |

---

## 工单结构

每个工单包含：

- **功能三元组**：行为 / 验证 / 状态（一行一个）
- **验收标准**：checkbox 列表，全部通过才能标 passing
- **不做范围**：显式声明不做的事，防止 AI 扩大范围
- **三段式执行**：阶段 1 只读 → 阶段 2 写码 → 阶段 3 自审
- **执行指令块**：底部可复制的指令文本，粘贴给 AI 即跑
- **变更追溯**：patches / supersedes / superseded-by

---

## 变更 Schema

后续变更按复杂度自动选择 schema：

| Schema | 适用场景 | 产出 |
|--------|---------|------|
| **hotfix** | 紧急修复 | proposal → tasks |
| **standard** | 常规变更 | proposal → specs → tasks |
| **feature** | 复杂功能 | proposal → specs → design → tasks |

---

## Context Contract（统一上下文协议）

> **状态：v1 已冻结（2026-06-24）**
>
> 经过 clarify → specify → order 全流程验证，Context Contract v1 已达到冻结条件。
> 冻结后，字段变更需走 RFC 流程。

所有 Skill 使用**统一的上下文协议**访问项目信息，避免变量命名混乱。

```yaml
context:
  project:      # 项目级信息（名称、技术栈、部署配置）
  feature:      # 功能级信息（ID、名称、域、依赖）
  task:         # 任务级信息（工单 ID、描述、状态）
  architecture: # 架构级信息（原则、规则、分层）
  constraints:  # 约束级信息（错误码、API 契约、域映射）
  memory:       # 记忆级信息（架构决策、项目约定、经验教训）
  session:      # 会话级信息（活跃工单、暂停点、下一步）
```

详见 `templates/context-schema.yaml` 和 `templates/meta/AGENTS.md`。

**核心规则**：
- 禁止直接使用旧变量名（如 `{{project_name}}`）
- 必须使用 `{{context.project.name}}` 等层级路径
- 新增变量先在 `context-schema.yaml` 注册
- **禁止使用已废弃字段**（如 `{{context.feature.title}}` → 使用 `{{context.feature.name}}`）

**已废弃字段**：

| 字段 | 替代方案 | 计划删除版本 |
|------|---------|------------|
| `context.feature.title` | `context.feature.name` | v2 |

---

## Phase 2 Status：Frozen ✅

> **冻结日期**：2026-06-24
> **冻结依据**：Artifact Chain Review v2.0 通过（总分 9.25/10）

Phase 2 已于 **2026-06-24** 正式冻结。所有 Schema 进入 Frozen 状态，受 Schema Change Policy 保护。

### 当前稳定协议

| 协议 | 版本 | 状态 |
|------|------|------|
| **Context Contract** | v1.0-frozen | ✅ Stable |
| **Artifact Schema** | v1.0-frozen | ✅ Stable |
| ├── Artifact Meta Schema | v1.0-frozen | ✅ Stable |
| ├── Spec Schema | v1.0-frozen | ✅ Stable |
| ├── Task Schema | v1.0-frozen | ✅ Stable |
| └── Architecture Schema | v1.0-frozen | ✅ Stable |

### Frozen Schema 文件位置

```
templates/
├── context-schema.yaml                       # Context Contract v1.0-frozen
└── meta/
    ├── artifact-meta-schema.yaml             # Artifact Meta Schema v1.0-frozen
    ├── spec-schema.yaml                       # Spec Schema v1.0-frozen
    ├── task-schema.yaml                       # Task Schema v1.0-frozen
    ├── architecture-schema.yaml               # Architecture Schema v1.0-frozen
    ├── schema-change-policy.md                # Schema 变更政策
    ├── phase2-freeze-declaration.md           # Phase 2 冻结声明
    └── artifact-chain-review.md               # 链路审查报告
```

### Schema Change Policy

冻结后，任何 Schema 修改必须遵循 SemVer 规范：

| 类型 | 场景 | 版本号 | 审批 |
|------|------|--------|------|
| **PATCH** | 兼容性修复（注释、示例、拼写） | v1.0.x | 单人 review |
| **MINOR** | 新增可选字段 | v1.x.0 | 维护者 review |
| **MAJOR** | 删除字段、修改语义、修改 ID 格式 | vx.0.0 | RFC + 投票 |

详见 `templates/meta/schema-change-policy.md`。

---

## Phase 2.5 Status：Frozen ✅

> **冻结日期**：2026-06-24
> **冻结依据**：Chain Review v2.5 + Consumer Review v2.5 双通过（总分 9.75/10）
> **新增协议**：Verify Schema v1.0-frozen（链路最终消费者）

Phase 2.5 已于 **2026-06-24** 正式冻结。Verify Schema 进入 Frozen 状态，闭环验证体系完成。

### Phase 2.5 新增稳定协议

| 协议 | 版本 | 状态 | 角色 |
|------|------|------|------|
| **Verify Schema** | v1.0-frozen | ✅ Stable | 链路最终消费者（V1-V6 规则 + 4 类 coverage） |

### Phase 2.5 Frozen 文档

```
templates/meta/
├── verify-schema.yaml                          # Verify Schema v1.0-frozen
├── phase2.5-freeze-declaration.md              # Phase 2.5 冻结声明
└── verify-consumer-review.md                   # Consumer Review 报告（4/4 一致）
```

### 闭环验证链路（已完成）

```
Requirement (Spec)        → V1 requirement_covered
    ↓
Acceptance Criteria (Spec) → V2 acceptance_covered
    ↓
Task (requirement_refs + acceptance_criteria_ids)
    ↓
Constraint (Architecture.constraint_refs)      → V3 constraint_referenced
    ↓
Validation (Task.validation_steps + status_map) → V6 validation_passed
    ↓
Verify Report (4 类 coverage + checks + failures + recommendations)
```

### Consumer Skill（已接入 Verify Schema）

| Skill | 角色 | 输出 |
|-------|------|------|
| **harness-verify** | 聚合消费者（V1-V6 规则执行） | Verify Schema 格式 |
| **harness-runtime-verify** | 执行消费者（V6 status_map 填充） | Verify Schema 格式 |
| **harness-review-loop** | 约束消费者（V3 + severity_distribution） | Verify Schema 格式 |
| **harness-analyze** | 预检消费者（4 类 coverage + 3 模式输出） | 按 verify_output_mode |

### Phase 2.5 冻结字段与词汇表

**冻结字段命名**（6 项）：

- `coverage.requirement_coverage`
- `coverage.acceptance_coverage`
- `coverage.constraint_coverage`
- `coverage.validation_coverage`
- `context.validation_status_map`
- `verify_output_mode`

**冻结枚举值**（3 套分维度词汇表）：

- 架构约束严重度：`must` / `should` / `may`
- 运行时验证状态：`passed` / `failed` / `skipped` / `error`
- 问题严重度：`block` / `warning` / `info`

详见 `templates/meta/verify-schema.yaml` §4 与 `templates/meta/phase2.5-freeze-declaration.md`。

---

## Artifact Schema（统一产物协议）

所有 Skill 输出（规格、工单、架构、报告）必须遵守统一的 Artifact Schema：

### 四层 Schema 架构

```
Context Contract v1
    ↓ 提供项目环境
Artifact Meta Schema v1.0-frozen
    ↓ 统一身份标识 + 引用完整性校验
    ├── Spec Schema v1.0-frozen（业务规格：What）
    ├── Task Schema v1.0-frozen（实现工单：How）
    └── Architecture Schema v1.0-frozen（约束结构：Constraints）
```

### 追踪链路

```
Feature (project.yaml)
    ↓
Spec (requirements → scenarios → acceptance_criteria)
    ↓ requirement_refs + acceptance_criteria_ids
Task (implementation_steps → validation_steps → DoD)
    ↓ constraint_refs
Architecture (constraints → modules → interfaces → decisions)
    ↓
[Verify Schema - Phase 2.5 待设计]
```

### 引用完整性规则

跨 Artifact 引用必须使用**结构化 ID**，禁止自由文本：

```yaml
# ❌ 错误：自由文本
architecture_rules:
  - "Service 层不得直接访问数据库"

# ✅ 正确：结构化 ID
constraints:
  constraint_refs:
    - "CON-NOT-001"
```

ID 格式：

| 类型 | 格式 | 示例 |
|------|------|------|
| Requirement | `REQ-{domain}-{seq:03d}` | `REQ-NOT-001` |
| Acceptance Criteria | `AC-{domain}-{seq:03d}` | `AC-NOT-001` |
| Constraint | `CON-{domain}-{seq:03d}` | `CON-NOT-001` |
| Module | `MOD-{domain}-{seq:03d}` | `MOD-NOT-001` |

详见 `templates/meta/artifact-meta-schema.yaml` Rules 6/7/8。

### Skill 与 Schema 的契约

所有 Skill 必须：

- 生成符合对应 Schema 的 Artifact（spec / task / architecture 等）
- 使用结构化 ID 引用其他 Artifact
- 在引用前验证目标存在性（Rules 8：评审时验证）
- 对 Frozen Schema 字段采用 forward compatibility（容忍未知字段）

---

## Phase 2.5 路线图

Phase 2 冻结后，进入 **Phase 2.5 Verify Schema** 设计：

```
Phase 2.5 Verify Schema（链路最终消费者）
    ↓
Requirement (Spec)
    ↓
Acceptance Criteria (Spec)
    ↓
Task (requirement_refs + acceptance_criteria_ids)
    ↓
Constraint (Architecture.constraint_refs)
    ↓
Validation (Task.validation_steps)
    ↓
Verify Report（覆盖率、通过率、缺陷率）
```

完成后将形成真正的闭环验证体系。

---

## 目录结构

```
harness-meta/
├── USAGE.md                     # 详细使用说明
├── schemas/                     # 变更 schema 定义
│   ├── hotfix.yaml
│   ├── standard.yaml
│   └── feature.yaml
├── skills/                      # 20 个 Skill 定义
│   ├── harness-init/
│   ├── harness-init-docs/
│   ├── harness-clarify/
│   ├── harness-specify/
│   ├── harness-specify-arch/
│   ├── harness-order/
│   ├── harness-analyze/
│   ├── harness-context/
│   ├── harness-execute/
│   ├── harness-review-loop/
│   ├── harness-runtime-verify/
│   ├── harness-explore/
│   ├── harness-change/
│   ├── harness-apply/
│   ├── harness-verify/
│   ├── harness-project-memory/
│   ├── harness-archive/
│   ├── harness-adopt-scan/
│   ├── harness-context-index/
│   └── harness-adopt-spec/
└── templates/                   # 模板文件
    ├── architecture/            # 架构规格模板（5 个）
    ├── changes/                 # 变更文档模板（4 个）
    ├── meta/                    # 元文档模板（11 个）
    ├── orders/                  # 工单模板
    ├── reference/               # 功能建议目录
    └── specs/                   # 域规格模板
```

---

## 设计参考

harness-meta 的设计融合了多个开源项目的最佳实践：

- **python-ai-template** — 工单三段式执行、功能三元组、验收标准、执行指令块
- **spec-kit** — 跨文档一致性审计、质量验证循环、严重度分级
- **OpenSpec** — Schema 驱动的 artifact 依赖图、变更管理流程

---

## 许可

MIT
