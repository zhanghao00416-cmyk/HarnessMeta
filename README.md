# harness-meta

> 用自然语言描述项目，通过 15 个 Skill 链驱动 AI 生成整套工程管理体系。

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
    → harness-specify-arch → harness-order → [harness-analyze] → harness-execute
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
| **harness-execute** | 按三段式执行工单写代码 |

### 流程 B：后续改代码（Brownfield）

```
[harness-explore] → harness-change → harness-apply → harness-verify → harness-archive
```

| Skill | 做什么 |
|-------|--------|
| **harness-explore** | 需求不清时先探索（只读） |
| **harness-change** | 按 schema 类型生成变更文件夹（proposal 含 created frontmatter） |
| **harness-apply** | 按轻量三段式（只读分析→写码→自审）实现任务 |
| **harness-verify** | 三维度验证（完整性/正确性/一致性），报告含修复路径 |
| **harness-archive** | 归档变更，合并增量规格到主规格（按 created 排序） |

### 流程 C：已有代码接入（Adopt）

```
harness-adopt-scan → harness-adopt-spec → 后续改代码走 Flow B
```

| Skill | 做什么 |
|-------|--------|
| **harness-adopt-scan** | 扫描代码库，反推 project.yaml + meta 文件（全部 passing） |
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

## 目录结构

```
harness-meta/
├── USAGE.md                     # 详细使用说明
├── schemas/                     # 变更 schema 定义
│   ├── hotfix.yaml
│   ├── standard.yaml
│   └── feature.yaml
├── skills/                      # 15 个 Skill 定义
│   ├── harness-init/
│   ├── harness-init-docs/
│   ├── harness-clarify/
│   ├── harness-specify/
│   ├── harness-specify-arch/
│   ├── harness-order/
│   ├── harness-analyze/
│   ├── harness-execute/
│   ├── harness-explore/
│   ├── harness-change/
│   ├── harness-apply/
│   ├── harness-verify/
│   ├── harness-archive/
│   ├── harness-adopt-scan/
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
