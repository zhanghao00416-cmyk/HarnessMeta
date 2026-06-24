---
name: harness-change
description: 创建后续变更。按 schema 类型生成变更文件夹（proposal + delta-spec + design + tasks）。
---

# harness-change：后续变更创建

## 触发条件

项目已完成首次工单，用户需要对已有代码进行变更时执行。

## 输入

- 用户描述（变更内容或变更名称）
- `project.yaml`（包含 `change_management` 配置）
- `schemas/` 目录（变更类型 schema 定义）

## 步骤

### 1. 确认变更名称

如果用户未提供名称，提问：

> 请描述你要做的变更。我会生成 kebab-case 名称。

从描述中推导名称（如"修复登录重定向" → `fix-login-redirect`）。

### 2. 确定 schema 类型

**判断规则**：

| 条件 | Schema |
|------|--------|
| 用户明确指定 | 使用指定 schema |
| 紧急修复、范围小 | `hotfix` |
| 需要改规格、中等复杂度 | `standard` |
| 跨模块、新依赖、复杂度高 | `feature` |

如果不确定，使用 `project.yaml` 的 `change_management.default_schema`。

### 3. 读取 schema 定义

读取 `schemas/{{schema_name}}.yaml`，解析 artifacts 依赖图。

### 4. 创建变更目录

```
changes/{{change_name}}/
```

### 4.5 暂停主线（更新 progress.md）

创建变更目录后，编辑 `progress.md` 的「变更暂停点」段，按 `docs/meta/CHANGE_WORKFLOW.md` 步骤 1 的字段填写：

| 字段 | 值 |
|------|-----|
| **task_mode** | `change` |
| **resume_feature_id** | 暂停前 active 的 feature_id（无则填 `-`） |
| **resume_ticket** | 暂停前 active 的工单 id（无则填 `-`） |
| **change_name** | 本步骤确定的变更目录名 |

> 字段名必须与 progress.md 模板一致，便于 harness-archive 恢复主线时读取。

### 5. 按依赖顺序生成 artifacts

按 schema 中的 `requires` 依赖关系，逐个生成 artifact：

**生成 proposal.md 时必须写入 frontmatter**：

```
---
change_name: {{change_name}}
schema: {{schema_name}}
# ISO 8601 时间戳，由 harness-change 在生成时写入
created: 2026-06-16T15:30:00+08:00
---
```

- `created` 字段使用 ISO 8601 格式（带时区），由 harness-change 在生成时刻写入
- 该字段供 harness-archive 判定变更时间顺序，**不可省略**
- 已有变更补救：该字段为后加的补丁，若 proposal.md 中没有该 frontmatter 字段，应手动补写或重跑 harness-change

**对每个 artifact**：

1. 读取 schema 中该 artifact 的 `instruction`
2. 读取已完成的依赖 artifact 作为上下文
3. 使用对应 `template` 文件结构
4. 填充内容，写入变更目录

**`requires_with_design` 处理**：feature schema 中 tasks 节点同时声明 `requires: [specs]` 和 `requires_with_design: [specs, design]`。若 design artifact 已生成，则 tasks 的上下文包含 specs + design；若 design 被跳过（optional: true），则 tasks 只依赖 specs。

**生成顺序示例（feature schema）**：

```
proposal（无依赖）
  ↓
specs（依赖 proposal）  +  design（依赖 proposal）
  ↓
tasks（依赖 specs + design）
```

### 6. 输出变更报告

```
## 变更创建完成

变更：{{change_name}}
Schema：{{schema_name}}
目录：changes/{{change_name}}/

已生成 artifacts：
- ✓ proposal.md
- ✓ delta-spec.md
- ✓ design.md（如适用）
- ✓ tasks.md

下一步：执行 harness-apply 实现任务
```

## 约束

- 不修改 `docs/specs/` 中的主规格（主规格由 archive 时合并）
- 不写代码
- 不修改已有工单
- artifact 内容必须遵守 schema 的 instruction 约束
