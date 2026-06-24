---
name: harness-specify
description: 规格文档生成。根据 project.yaml 中已澄清的功能信息，生成 docs/specs 下的规格文档。
---

# harness-specify：规格文档生成

## 触发条件

harness-clarify 完成后，用户要求生成规格文档时执行。

## 输入

- `project.yaml`（features 段已包含 behavior 和 docs 字段）

## 步骤

### 1. 读取功能规格

从 `project.yaml` 的 `features` 段读取每个功能的行为描述和文档需求。

跳过未澄清的功能（behavior 字段为空或包含 `[TBD: 待用户确认]`）。

### 2. 按域分组

将功能按业务域分组。域从 `docs` 字段的目录名推断：

```yaml
docs:
  - docs/specs/auth/spec.md      # 域 = auth
  - docs/specs/payment/spec.md   # 域 = payment
```

### 3. 生成规格文档

对每个域，使用 `templates/specs/spec.md` 模板生成规格文件：

**生成规则**：

- 每个功能的行为描述填入对应的"需求"段
- 边界条件转化为"场景"（前置/当/则格式）
- 每个需求至少一个场景
- 禁止写实现细节（只写行为契约）

**文件路径**：`docs/specs/{{domain}}/spec.md`

### 4. 输出规格报告

```
## 域规格生成完成

已生成：{{domain_count}} 个域规格文件

| 域 | 规格文件 | 需求数 | 场景数 |
|----|---------|-------|-------|
| auth | docs/specs/auth/spec.md | 3 | 7 |
| chat | docs/specs/chat/spec.md | 2 | 5 |

跳过：{{skipped_count}} 个未澄清功能

下一步：执行 /harness-specify-arch 生成架构规格（建议新会话）
```

## 约束

- 不修改 project.yaml
- 不生成工单文件
- 不写代码
- 规格文档中禁止出现实现细节
