---
name: harness-clarify
description: 需求澄清。与用户交互式澄清每个功能的行为规格和文档需求，回写到 project.yaml。
---

# harness-clarify：需求澄清

## 触发条件

harness-init-docs 完成后，用户要求澄清需求时执行。

## 输入

- `project.yaml`（已由 harness-init 验证）
- `docs/meta/` 目录（已由 harness-init-docs 生成工作流文件）

## 前置检查

读取项目根目录，确认以下条件：

- `project.yaml` 存在
- `docs/meta/DEPENDENCY_MAP.md` 存在（harness-init-docs 已执行）

如果缺失，提示用户先执行 `/harness-init-docs`。

## 步骤

### 1. 读取功能列表

从 `project.yaml` 的 `features` 段读取所有功能。按依赖顺序排列（无依赖的排前面）。

### 2. 逐个澄清

对每个功能，向用户提出澄清问题：

**必须澄清的内容**：

- **核心行为**：这个功能做什么？输入什么？输出什么？
- **边界条件**：异常情况怎么处理？
- **文档需求**：需要在哪些 docs 文件中记录？

**澄清规则**：

- 每个功能基础 3 问（行为、边界、文档各 1 个）
- 若用户回答模糊，每类可追加 1 次追问，仍模糊则标记为 `[TBD: 待用户确认]`
- 按优先级排序（行为 > 边界 > 文档）
- 问题要具体，不要开放式提问

### 3. 回写 project.yaml

将澄清结果回写到对应功能的字段：

```yaml
features:
  - id: F01
    title: 项目骨架
    dependencies: []
    behavior: |
      创建项目目录结构...
    docs:
      - docs/specs/core/spec.md
    verify_command: "pytest -x"
```

### 4. 输出澄清报告

```
## 需求澄清完成

已澄清：{{count}} / {{total}} 个功能

| 功能 | 行为 | 边界 | 文档 | 状态 |
|------|------|------|------|------|
| F01  | ✓   | ✓   | ✓   | 完整 |
| F02  | ✓   | ⚠   | ✓   | TBD |

下一步：执行 harness-specify 生成规格文档
```

## 约束

- 不生成任何文件（只回写 project.yaml）
- 不假设用户的意图（不明确的部分必须提问）
- 不写代码、不生成工单
