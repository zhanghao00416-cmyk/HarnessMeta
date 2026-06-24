---
name: harness-order
description: 工单生成。根据 project.yaml 和规格文档，生成首次工单文件，按依赖图排序。
---

# harness-order：首次工单生成

## 触发条件

harness-specify-arch 完成后，用户要求生成工单时执行。

## 输入

- `project.yaml`（features 段完整）
- `docs/specs/`（规格文档已生成）
- `templates/orders/order.md`（工单模板）

## 步骤

### 0. 检查已有工单（断点恢复）

扫描 `orders/` 目录，检查已生成的工单文件：

- **全部已生成**：报告“所有工单已存在”，跳过生成，跳到步骤 4
- **部分已生成**：识别缺失的功能 ID，从缺失的第一批继续生成
- **无工单**：从头开始

```
发现已生成工单：F01, F03, F05, F07, F08, F20（批次 1）
缺失工单：F02, F04, F06, F09, F10, F11, F12, F14, F15a, F15b, F15c, F13, F16, F17, F18, F19, F21
从批次 2 继续生成...
```

### 1. 构建依赖图

从 `project.yaml` 的 `features` 段构建依赖 DAG：

```
F01（无依赖）
  ↓
F02（依赖 F01）
F03（依赖 F01）
  ↓
F04（依赖 F02, F03）
```

### 2. 拓扑排序

按拓扑顺序排列工单。同一层的工单可并行（但执行时仍按顺序）。

### 3. 生成工单文件

**分批规则**：

- 功能总数 ≤ 6：一次性全部生成
- 功能总数 > 6：按拓扑层级分批，每批最多 6 个，层间暂停让用户确认

```
示例（21 个功能）：
批次 1：Layer 0（无依赖） → F01, F03, F05, F07, F08, F20（6个）
批次 2：Layer 1（依赖 L0）→ F02, F04, F06, F09, F10（5个）
批次 3：Layer 2（依赖 L1）→ F11, F12, F14, F16, F17（5个）
批次 4：Layer 3（依赖 L2）→ F13, F15a, F15b, F18, F19（5个）
```

每批完成后输出进度，下一批读取已生成的工单文件确保 code_deps 引用一致。

**每个工单的生成流程**：

使用 `templates/orders/order.md` 模板，按填充规则生成工单文件：

| 模板变量 | 数据来源 |
|---------|----------|
| `{{id}}` | `features[].id` |
| `{{title}}` | `features[].title` |
| `{{status}}` | 初始为 `not_started` |
| `{{dependencies}}` | `features[].dependencies` |
| `{{patches}}` | 初始为"无" |
| `{{supersedes}}` | 初始为"无" |
| `{{superseded_by}}` | 初始为"无" |
| `{{behavior_brief}}` | `features[].behavior` + 对应 `docs/specs/` 中的需求（一句话摘要） |
| `{{verify_command}}` | `features[].verify_command` 或 `verify_commands.health_check` |
| `{{code_deps}}` | 从依赖工单的产出推断文件路径（无依赖则填"无跨工单硬代码依赖"） |
| `{{required_docs}}` | `features[].docs` + 通用必读文档（ARCHITECTURE.md、AGENTS.md）+ 对应规格文档（步骤 3 已生成的域规格/架构规格） |
| `{{implementation_plan}}` | 从规格文档和架构规格推断的文件清单（路径 + 职责表格式），执行阶段可微调 |

**输出路径**：`orders/{{id}}_{{kebab_title}}.md`

### 4. 更新 DEPENDENCY_MAP.md

`docs/meta/DEPENDENCY_MAP.md` 是跨工单代码依赖和文档依赖的集中索引。本步骤必须填充 3 个表：

**4a. 填充工单执行顺序表**（追加到文件末尾）：

```markdown
## 工单执行顺序

| 顺序 | 工单 | 依赖 | 可并行 |
|------|------|------|--------|
| 1 | F01 | - | - |
| 2 | F02 | F01 | F03 |
| 3 | F03 | F01 | F02 |
| 4 | F04 | F02, F03 | - |
```

**4b. 填充表 1：跨工单代码依赖**（替换模板中的占位符行）：

遍历所有已生成工单，根据每个工单的 `implementation_plan`（阶段 1 计划实现的文件路径），填充其依赖的前序工单的核心文件路径。

数据源：每个工单的 `{{code_deps}}` 字段（步骤 3 已生成）。

示例填充结果：

```markdown
| 工单 | 依赖的前序代码文件 |
|------|------------------|
| F01 | （无前序依赖） |
| F02 | F01: app/core/config.py, app/db/base.py |
| F03 | F01: app/core/config.py |
| F04 | F02: app/models/session.py; F03: app/middleware/error.py |
```

**4c. 填充表 2：跨 docs 事实依赖**（替换模板中的占位符行）：

遍历所有已生成工单，根据每个工单的 `required_docs` 字段（步骤 3 已生成）+ 通用必读文档（ARCHITECTURE.md、AGENTS.md），填充其必读 docs。

数据源：每个工单的 `{{required_docs}}` 字段 + `AGENTS.md` + `ARCHITECTURE.md`（所有工单必读）。

示例填充结果：

```markdown
| 工单 | 必读 docs |
|------|----------|
| F01 | ARCHITECTURE.md, AGENTS.md |
| F02 | ARCHITECTURE.md, AGENTS.md, docs/specs/database/spec.md, docs/specs/_architecture/DATA_MODEL.md |
| F03 | ARCHITECTURE.md, AGENTS.md, docs/specs/_architecture/ERROR_CODE.md |
```

> **分批模式**：步骤 4 在每批工单生成后执行。每批只填该批工单对应的行（追加，不覆盖已填行）。

### 5. 更新进度

更新 `progress.md`：所有工单标记为"待执行"。
更新 `QUICK_REFERENCE.md`：填入下一步操作。

### 6. 输出生成报告

**分批模式**（每批完成后输出）：

```
## 批次 {{batch}}/{{total_batches}} 完成

已生成：{{batch_count}} 个工单（F{{start}}–F{{end}}）
累计：{{cumulative_count}} / {{total}} 个工单

| 工单 | 标题 | 依赖 | 验证命令 |
|------|------|------|----------|
| F01  | 项目骨架 | - | pytest -x |

继续生成下一批？（建议在新会话中执行下一批）
```

**全部完成后输出**：

```
## 工单生成完成

已生成：{{count}} 个工单（{{batch_count}} 批）
执行顺序：{{order_summary}}

下一步：按顺序执行工单（或使用 harness-execute）
```

## 约束

- 不修改规格文档
- 不修改 project.yaml
- 不写代码
- 工单中的 TBD 占位符保留不填（由执行阶段回填）
