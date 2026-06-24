# harness-meta 使用说明

## 一句话理解

> 用自然语言描述你的项目，通过 15 个 Skill 链驱动 AI 帮你生成整套工程管理体系，后续改代码也有完整变更管控。

---

## 快速开始（3 分钟）

### 第 1 步：复制模板

把 `harness-meta/` 目录内的 `schemas/`、`skills/`、`templates/` 复制到你的新项目根目录（不要嵌套 harness-meta/ 文件夹）。`project.yaml` 不需要复制，由 `/harness-init` 交互式生成。

> 如需参考配置格式，可查看 `templates/reference/project.yaml.example`。

### 第 2 步：执行 /harness-init（AI 交互式引导）

```
/harness-init
```

采用**两轮自然语言对话**，你只需要随便说，AI 帮你整理：

---

**第 1 轮：你描述项目**

AI 会问你：

> 描述一下你想做的项目。包括：做什么、用什么技术、有哪些核心功能。随便说，我来帮你整理。

你用自然语言随便说就行：

```
你: 做一个智能客服系统，用 Python FastAPI，支持多轮对话、知识库检索、
    多 Agent 协作。数据库用 PostgreSQL，缓存用 Redis，向量库用 Qdrant。
```

---

**第 2 轮：AI 拆解 + 建议 + 确认**

AI 会从你的描述中提取项目名称、功能清单、架构原则、验证命令，并**参考内置的功能建议目录**检查你可能遗漏的功能：

```
AI: 根据你的描述，我整理出以下功能和架构原则：

    功能清单：
    F01 项目骨架
    F02 数据库模型 + Redis 缓存（依赖 F01）
    F03 错误中间件（依赖 F01）
    F04 LLM 网关（依赖 F01, F03）
    F05 上下文管理（依赖 F02）
    F06 对话功能（依赖 F04, F05）
    F07 知识库管理（依赖 F02, F04）
    F08 RAG 检索（依赖 F07）
    F09 多 Agent 协作（依赖 F04, F06）

    架构原则：
    1. 分层架构：api → domain → services → infra，禁止反向依赖
    2. 所有外部服务通过 Provider 抽象访问
    3. 配置全部从环境变量读取，禁止硬编码

    验证命令：python -m pytest -x

    🟡 根据你的项目类型，你可能还需要：
    - SSE 流式输出（实时返回 LLM 生成内容）
    - Prompt 管理（模板加载 + 版本管理）
    - 可观测性（OpenTelemetry 追踪 + Token 统计）
    - 认证与限流（JWT/API Key + 按用户限流）

    需要加入这些吗？或者有其他调整？确认后我就开始生成。
```

---

你确认后，AI 自动生成 `project.yaml`，然后继续生成项目骨架。

> 如果你已经有写好的 project.yaml，AI 会读取并验证，跳过提问。

### 第 3 步：继续执行 Skill 链

```
/harness-init-docs               # 5 个工作流文件 + 规格目录（建议新会话）
/harness-clarify                 # AI 逐功能提问，补全规格
/harness-specify                 # 生成域规格文件
/harness-specify-arch            # 生成架构规格 + 更新 FACT_REGISTRY（建议新会话）
/harness-order                   # 生成工单文件
/harness-analyze                 # 跨文档一致性审计（可选，建议执行前跑一次）
/harness-execute F01             # 逐个执行工单写代码
```

> 标注「建议新会话」的 Skill 上下文较重，详见下方「会话规划指南」。

项目建完后，后续改代码：

```
/harness-explore               # 需求不清时先探索（可选）
/harness-change                # 生成变更提案+任务清单
/harness-apply                 # 实现变更任务
/harness-verify                # 三维度检查
/harness-archive               # 归档变更，合并规格（支持批量）
```

已有代码接入：

```
/harness-adopt-scan            # 扫描代码库，反推 project.yaml + meta 文件
/harness-adopt-spec            # 从代码反推规格文档（建议新会话）
```

---

## 会话规划指南

LLM 会话上下文有限，以下 Skill 建议在新会话中执行，避免上下文累积导致生成质量下降：

| Skill | 原因 | 前置条件 |
|-------|------|--------|
| harness-init-docs | 读取 project.yaml 生成 5 个文件，输出量大 | harness-init 已完成 |
| harness-specify-arch | 生成 5 个架构规格 + 更新 FACT_REGISTRY | harness-specify 已完成 |
| harness-adopt-spec | 从代码反推规格文档，上下文较重 | harness-adopt-scan 已完成 |
| harness-order 后续批次 | 工单 >6 个时，每批在新会话生成 | 上一批已完成 |

**何时必须切换会话**：

- AI 开始重复之前的内容或“忘记”前面的指令
- 生成质量明显下降（格式混乱、省略内容）
- 工单分批执行时，每批完成后切换到新会话

**切换后如何恢复**：

每个 Skill 启动时自动扫描磁盘文件判断状态（断点续跑）。也可以读 `session-handoff.md` 和 `progress.md`，对 AI 说“继续上次的工作”即可。

---

## 两套流程说明

### 流程 A：首次建项目（Greenfield）

适用场景：从零开始的新项目。

```
harness-init → harness-init-docs → harness-clarify → harness-specify → harness-specify-arch → harness-order → [harness-analyze] → harness-execute
```

| Skill | 做什么 | 产出 |
|-------|--------|------|
| **harness-init** | 交互式创建 project.yaml，生成项目目录 + 6 个核心 meta 文件 + 1 个状态文件 | project.yaml + 目录结构 + 6 个 meta（AGENTS/ARCHITECTURE/QUICK_REFERENCE/progress/session-handoff/evaluator-rubric）+ feature_list.json（状态文件） |
| **harness-init-docs** | 生成 5 个工作流 meta 文件 + 规格目录（建议新会话） | docs/meta/ 下 5 个文件 + docs/specs/ 域目录 |
| **harness-clarify** | 逐功能向你提问，补全行为规格 | project.yaml 中的 behavior/docs/verify_command 字段 |
| **harness-specify** | 根据澄清结果生成域规格文件 | docs/specs/ 下按业务域分组的 spec.md |
| **harness-specify-arch** | 生成 5 个架构规格 + 更新 FACT_REGISTRY（建议新会话） | docs/specs/_architecture/ 下 5 个文件 + FACT_REGISTRY 更新 |
| **harness-order** | 根据依赖图生成工单文件（分批生成） | orders/ 下的工单文件（含三段式执行指令） |
| **harness-analyze** | 跨文档一致性审计（只读不改文件，6 维度检测） | 审计报告（覆盖缺口/术语漂移/路径冲突/架构合规/错误码/依赖完整性） |
| **harness-execute** | 按三段式执行工单 | 代码实现 + progress.md/session-handoff.md 更新 |

### 流程 B：后续改代码（Brownfield）

适用场景：项目已建好，需要迭代、修 bug、加功能。

```
[harness-explore] → harness-change → harness-apply → harness-verify → harness-archive
```

| Skill | 做什么 | 产出 |
|-------|--------|------|
| **harness-explore** | 需求不清时先调查代码库、分析瓶颈、对比方案 | 探索报告（只读，不修改代码） |
| **harness-change** | 根据变更复杂度选 schema，生成变更文件夹 | changes/<name>/ 下的 proposal + delta-spec + design + tasks（proposal 含 created 时间戳 frontmatter） |
| **harness-apply** | 按轻量三段式（只读分析→写码→自审）实现 tasks.md 中的任务 | 阶段 1 差异清单 + 阶段 2 代码变更（含 handoff 快照）+ 阶段 3 自审报告 + tasks.md checkbox 标记 |
| **harness-verify** | 三维度检查（完整性/正确性/一致性） | 验证报告（每项含严重度 + 修复路径） |
| **harness-archive** | 合并增量规格到主规格，归档变更文件夹（支持批量） | docs/specs/ 更新 + changes/archive/ 归档（按 proposal frontmatter 的 created 排序） |

### 流程 C：已有代码接入（Adopt）

适用场景：已有代码库，想纳入 harness 管理体系。

```
harness-adopt-scan → harness-adopt-spec（建议新会话） → 后续改代码走 Flow B
```

| Skill | 做什么 | 产出 |
|-------|--------|------|
| **harness-adopt-scan** | 扫描代码库，反推功能清单 + 架构原则，生成 project.yaml + meta 文件 | project.yaml + 6 个 meta + feature_list.json（全部 passing） |
| **harness-adopt-spec** | 从代码反推域规格 + 架构规格 + 工作流 meta 文件 | docs/specs/ 域规格 + 5 个架构规格 + 5 个工作流 meta 文件（docs/meta/） |

接入后所有功能标记为 `passing`，后续改代码直接走 Flow B。

---

## 工单结构说明

每个工单文件包含以下核心部分：

| 部分 | 作用 |
|------|------|
| **元数据** | id、state、dependencies + patches/supersedes/superseded-by（变更追溯，首次工单恒为“无”） |
| **功能三元组** | 行为/验证/状态，一行一个的紧凑格式 |
| **验收标准** | checkbox 列表，全部通过才能标 passing |
| **关键约束** | 引用 ARCHITECTURE.md、ERROR_CODE.md、API_CONTRACT.md、DOMAIN_MAP.md |
| **不做范围** | 显式声明不做的事，防止 AI 扩大范围 |
| **阶段 1（只读）** | 读前序代码 + docs，输出差异清单和文件清单，禁止写代码 |
| **阶段 2（写码）** | 契约对齐 + 实现清单 + 验证命令 |
| **阶段 3（自审）** | 对照 evaluator-rubric 自审 + docs 同步 + 状态更新 |
| **执行指令块** | 底部可复制的指令文本，粘贴给 AI 即跑 |

**工单状态流转**：`not_started` → `active` → `passing`

**分批生成**：功能总数 > 6 时，按拓扑层级分批，每批最多 6 个，层间暂停让用户确认。

---

## Schema 类型说明

后续变更时，系统根据复杂度选择不同的 schema：

| Schema | 适用场景 | 生成的文档 |
|--------|---------|-----------|
| **hotfix** | 紧急修复，范围小 | proposal → tasks |
| **standard** | 常规变更，需改规格 | proposal → specs → tasks |
| **feature** | 复杂功能，跨模块 | proposal → specs → design → tasks |

判断规则：

- 只是修 bug、改配置 → hotfix
- 需要改行为契约、加小功能 → standard
- 跨多个模块、引入新依赖、改数据模型 → feature

可在 `project.yaml` 中设置默认值：

```yaml
change_management:
  default_schema: hotfix
```

---

## project.yaml 字段速查

| 字段 | 必填 | 说明 |
|------|------|------|
| `project.name` | 是 | 项目名称 |
| `project.description` | 是 | 项目描述 |
| `project.language` | 否 | 文档语言，默认 zh |
| `project.spec_lifecycle` | 否 | 规格生命周期模式（默认 living-spec）：<br>• `living-spec`：规格随项目演进，delta 归档时合并回主规格<br>• `flow-back`：规格只记录，不回写代码<br>• `flow-forward`：规格驱动代码，代码不回写规格 |
| `constitution.principles` | 是 | 架构原则列表（至少 1 条） |
| `constitution.rules` | 否 | 架构规则列表 |
| `features` | 是 | 功能清单（至少 1 个） |
| `features[].id` | 是 | 功能 ID（如 F01） |
| `features[].title` | 是 | 功能标题 |
| `features[].dependencies` | 是 | 依赖的功能 ID 列表 |
| `features[].schema` | 否 | 工单类型，默认 standard |
| `features[].behavior` | clarify 填 | 行为描述 |
| `features[].docs` | clarify 填 | 相关文档路径 |
| `features[].verify_command` | clarify 填 | 验证命令 |
| `change_management.default_schema` | 否 | 默认变更类型 |
| `change_management.specs_dir` | 否 | 主规格目录 |
| `change_management.changes_dir` | 否 | 变更目录 |
| `change_management.archive_dir` | 否 | 归档目录 |
| `verify_commands.health_check` | 否 | 健康检查命令 |
| `verify_commands.architecture_check` | 否 | 架构检查命令 |
| `context` | 否 | 项目技术上下文 |
| `deployment.type` | 否 | 部署方式，默认 `docker-compose`（可选：`k8s` / `standalone`） |
| `deployment.compose_file` | 否 | Compose 文件路径，默认 `docker-compose.yml` |
| `deployment.services` | 否 | 服务列表（name / port / healthcheck / depends_on） |
| `deployment.build` | 否 | 构建配置（context / dockerfile） |
| `rules` | 否 | artifact 生成规则（按类型分组） |

---

## 生成后的项目结构

执行完首次流程后，你的项目会变成：

```
your-project/
├── AGENTS.md                    # AI 会话协议
├── ARCHITECTURE.md              # 架构宪法
├── QUICK_REFERENCE.md           # 速查卡
├── progress.md                  # 进度日志
├── session-handoff.md           # 会话交接
├── evaluator-rubric.md          # 评估评分表
├── feature_list.json            # 功能状态追踪
├── docs/
│   ├── specs/                   # 规格文档（按业务域）
│   │   ├── _architecture/       # 全局架构规格
│   │   │   ├── API_CONTRACT.md  # API 契约
│   │   │   ├── DATA_MODEL.md    # 数据模型
│   │   │   ├── DEPLOYMENT.md    # 部署架构（Docker Compose）
│   │   │   ├── DOMAIN_MAP.md    # 域职责映射
│   │   │   └── ERROR_CODE.md    # 错误码体系
│   │   ├── auth/spec.md
│   │   └── payment/spec.md
│   └── meta/                    # 跨工单共享元文档
│       ├── DEPENDENCY_MAP.md    # 工单依赖速查
│       ├── FACT_REGISTRY.md     # 事实注册表（禁止凭记忆）
│       ├── CHANGE_WORKFLOW.md   # 变更工作流
│       ├── FEATURE_DEV_WORKFLOW.md # 功能开发流程
│       └── API_CHANGE_CHECKLIST.md # 接口变更检查清单
├── orders/                       # 工单文件
│   ├── F01_项目骨架.md
│   ├── F02_数据模型.md
│   └── ...
├── changes/                     # 后续变更
│   ├── _explorations/           # 探索报告（harness-explore 产出）
│   └── archive/                 # 已归档变更
└── src/                         # 你的源代码（工单执行产出）
```

> harness-meta 模板本身还包含 `schemas/`（变更 schema 定义）和 `templates/reference/feature-catalog.md`（功能建议目录），这些在初始化时复制到项目中，日常不需修改。

---

## 常见问题

### Q：harness-analyze 检测什么？

6 个维度：覆盖缺口（需求无工单/工单无需求）、术语漂移、路径冲突、架构合规、错误码一致性、依赖完整性。每个发现分 4 级严重度（CRITICAL/HIGH/MEDIUM/LOW）。严格只读，不修改任何文件。建议在首次执行工单前跑一次。

### Q：可以用什么 AI 工具？

任何 LLM 都可以。Qwen、GLM、Claude、GPT、Cursor、Copilot 均可。所有模板和 Skill 都是纯 Markdown，不绑定特定工具。

### Q：中断了怎么办？

每个 Skill 启动时自动扫描磁盘文件判断当前状态（断点续跑）：
- harness-init/init-docs：检查 `project.yaml` 和 `docs/meta/` 是否已存在
- harness-order：扫描 `orders/` 目录，从缺失的第一批继续
- harness-execute：读 `progress.md` 找下一个 not_started 工单
- harness-apply：读 `tasks.md` 中未完成的 checkbox
- harness-adopt-scan：检查 `project.yaml` 和 `AGENTS.md` 是否已存在

也可以读 `session-handoff.md` 和 `progress.md` 手动恢复。对 AI 说“继续上次的工作”即可。

### Q：工单执行到一半发现范围不对？

阶段 1（只读）结束时可以调整范围。进入阶段 2 后不建议改范围，应新建变更。

### Q：已有代码怎么接入？

执行 `/harness-adopt-scan`，AI 会扫描你的代码库，反推功能清单和架构原则，交互确认后生成 project.yaml + meta 文件。然后在新会话执行 `/harness-adopt-spec` 生成规格文档。接入后所有功能标记为 passing，后续改代码直接走 Flow B。

### Q：后续变更和首次工单的区别？

| | 首次工单 | 后续变更 |
|--|---------|---------|
| 目的 | 从零建设 | 迭代已有代码 |
| 流程 | 7+1 步 Skill 链（harness-analyze 可选） | 4–5 步变更链 |
| 规格 | 生成主规格 | 增量 delta（不直接改主规格） |
| 归档 | 无 | 归档后合并 delta 到主规格 |

### Q：如何跳过某些 Skill？

如果需求已经很清晰，可以跳过 `harness-clarify`，直接在 project.yaml 中填好 behavior/docs/verify_command 字段，然后从 `harness-specify` 开始。

### Q：AI 给的功能建议是怎么来的？

harness-init 内置了一份[功能建议目录](templates/reference/feature-catalog.md)，涵盖 AI 项目和通用前后端项目的 30 个常见能力，按 7 层架构组织。AI 在第 2 轮对话中会自动比对你的描述，提示你可能遗漏的功能（如 SSE 流式输出、可观测性、异步任务队列等）。你可以选择采纳或忽略。

---

## 设计原则（完整版）

> 核心 7 条见 README.md「核心理念」，以下为完整 9 条。

1. **模板结构化**：每个产出物有固定 section，AI 填充而非自由发挥
2. **依赖图约束**：artifact 按 DAG 顺序生成，前驱不存在则阻塞
3. **增量变更**：变更只表达 delta，不重写全局 spec
4. **三段式执行**：只读 → 写码 → 自审，防止跳步
5. **LLM 无关**：全部纯 Markdown/YAML，任何 AI 工具可用
6. **AI 主动建议**：初始化时参考内置功能目录，主动提醒用户可能遗漏的功能
7. **断点续跑**：每个 Skill 启动时扫描磁盘文件判断状态，支持新会话继续
8. **分批生成**：工单 >6 个时按拓扑层级分批，避免上下文溢出
9. **工单三态流转**：not_started → active → passing，状态单一数据源
