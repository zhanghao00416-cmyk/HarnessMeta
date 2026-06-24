---
name: harness-init-docs
description: 初始化工作流文档。读取已有的 project.yaml，生成 5 个工作流 meta 文件和规格目录骨架。建议在 harness-init 完成后，在新会话中执行。
---

# harness-init-docs：工作流文档初始化

## 触发条件

harness-init 完成后执行。建议在新会话中执行，以获得最佳生成质量。

## 输入

- `project.yaml`（必须存在且已通过 harness-init 验证）
- `docs/meta/` 目录（已由 harness-init 创建）
- `docs/specs/` 目录（已由 harness-init 创建）

## 前置检查

读取项目根目录，确认以下条件：

- `project.yaml` 存在
- `AGENTS.md` 存在（harness-init 已执行）
- `docs/meta/` 目录存在

如果缺失，提示用户先执行 `/harness-init`。

## 步骤

### 1. 读取 project.yaml

从 `project.yaml` 读取以下信息：

- `features` 段（功能列表和依赖关系）
- `change_management` 段（schema 配置和目录路径）
- `project.name`（项目名称）

### 2. 生成工作流 meta 文件（5 个）

从 `templates/meta/` 模板生成以下文件：

| 模板 | 输出路径 | 填充规则 |
|------|---------|--------|
| `DEPENDENCY_MAP.md` | `docs/meta/DEPENDENCY_MAP.md` | 复制模板（表 1、表 2 由 harness-order 填充） |
| `FACT_REGISTRY.md` | `docs/meta/FACT_REGISTRY.md` | 初始化框架，源文件索引由 harness-specify 补充 |
| `CHANGE_WORKFLOW.md` | `docs/meta/CHANGE_WORKFLOW.md` | 填入 `change_management` 段的 schema 和目录配置 |
| `FEATURE_DEV_WORKFLOW.md` | `docs/meta/FEATURE_DEV_WORKFLOW.md` | 直接复制模板，填入项目特定配置 |
| `API_CHANGE_CHECKLIST.md` | `docs/meta/API_CHANGE_CHECKLIST.md` | 直接复制模板 |

### 3. 创建规格目录骨架

根据 `features` 中涉及的业务域，在 `docs/specs/` 下创建域目录：

```
docs/specs/{{domain}}/
```

只创建目录，不生成文件。规格内容由 harness-specify 填充。

### 4. 输出完成报告

```
## harness-init-docs 完成

项目：{{project_name}}
工作流 meta 文件：5 个已生成
规格目录：{{domain_count}} 个域已创建

全部 11 个 meta 文件就绪。

下一步：执行 /harness-clarify 澄清需求
```

## 约束

- 不修改 harness-init 已生成的文件
- 不生成工单文件
- 不填写规格内容
- 所有 `{{variable}}` 占位符从 project.yaml 取值
