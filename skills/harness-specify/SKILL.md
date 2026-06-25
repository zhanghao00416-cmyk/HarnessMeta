---
name: harness-specify
description: 规格文档生成。根据 project.yaml 中已澄清的功能信息，调研现有代码（如适用），生成 docs/specs 下的规格文档。
---

# harness-specify：规格文档生成

## 触发条件

harness-clarify 完成后，用户要求生成规格文档时执行。

## 输入

- `project.yaml`（features 段已包含 behavior 和 docs 字段）
- 现有代码（可选，Adopt 流程或已有项目时）

## 步骤

### 0. 检查已有规格（断点恢复）

扫描 `docs/specs/` 目录：

- **全部已生成**：报告"所有域规格已存在"，跳到步骤 5
- **部分已生成**：识别缺失的域，从缺失的第一个域继续
- **无规格**：从头开始

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

### 3. 调研现有代码（可选）

如果项目已有代码（Adopt 流程或 Brownfield 场景），执行代码调研：

**3a. 扫描源码目录**

根据 `project.yaml` 的 `tech_stack` 推断源码位置：

| 项目类型 | 后端源码目录 | 前端源码目录 |
|----------|-------------|-------------|
| 纯后端 | `src/` 或 `app/` | 无 |
| 纯前端 | 无 | `src/` 或 `frontend/src/` |
| 全栈 | `backend/src/` 或 `src/` | `frontend/src/` 或 `src/` |

**3b. 提取已有实现**

对每个域，扫描对应源码目录，提取：

| 提取项 | 来源 | 用途 |
|--------|------|------|
| 已有 API 端点 | `router/`、`controller/`、`views/` | 与规格中的接口定义对比 |
| 已有数据模型 | `models/`、`schemas/`、`entities/` | 与规格中的数据模型对比 |
| 已有业务逻辑 | `services/`、`usecases/` | 识别已实现的功能和缺失的功能 |
| 已有组件 | `components/`、`views/` | 与规格中的 UI 需求对比 |

**3c. 对比分析**

将已有实现与 `project.yaml` 中的功能需求对比：

```
功能需求（project.yaml）    已有实现（代码）
─────────────────────────────────────────────────
F01: 用户注册                ✅ 已实现（auth/register.py）
F02: 用户登录                ✅ 已实现（auth/login.py）
F03: 密码重置                ⚠️ 部分实现（缺少邮件发送）
F04: 用户资料管理             ❌ 未实现
```

**3d. 记录调研结果**

将调研结果写入 `docs/specs/_research/research-notes.md`：

```markdown
## 代码调研报告

### 调研范围

- 后端源码：`{{context.project.stack.backend}}`
- 前端源码：`{{context.project.stack.frontend}}`
- 调研日期：`{{context.session.date}}`

### 功能覆盖度

| 功能 ID | 需求 | 实现状态 | 已有文件 | 差距说明 |
|---------|------|----------|----------|----------|
| F01 | 用户注册 | 已完成 | `auth/register.py` | 无 |
| F02 | 用户登录 | 已完成 | `auth/login.py` | 无 |
| F03 | 密码重置 | 部分完成 | `auth/reset.py` | 缺少邮件发送逻辑 |
| F04 | 用户资料 | 未实现 | - | 需全新开发 |

### 接口对比

| 规格端点 | 已有端点 | 一致性 | 备注 |
|----------|----------|--------|------|
| POST /api/v1/users | POST /api/users | ⚠️ 版本号缺失 | 需添加 v1 前缀 |

### 数据模型对比

| 规格模型 | 已有模型 | 一致性 | 备注 |
|----------|----------|--------|------|
| User（含 email_verified） | User（不含 email_verified） | ⚠️ 字段缺失 | 需添加字段 |

### 建议

1. **优先实现**：F04（用户资料管理），完全缺失
2. **补充完善**：F03 的邮件发送逻辑
3. **接口对齐**：统一添加 `/api/v1` 前缀
```

> **约束**：调研只读不写，不修改任何源码文件。

### 4. 生成规格文档

对每个域，使用 `templates/specs/spec.md` 模板生成规格文件：

**生成规则**：

- 每个功能的行为描述填入对应的"需求"段
- 边界条件转化为"场景"（前置/当/则格式）
- 每个需求至少一个场景
- 禁止写实现细节（只写行为契约）
- **已有代码时**：在场景中添加"已有实现"备注，标注哪些场景已覆盖、哪些需新增

**文件路径**：`docs/specs/{{context.feature.domain}}/spec.md`

### 5. 输出规格报告

**无代码调研时**：

```
## 域规格生成完成

已生成：{{context.session.domain_count}} 个域规格文件

| 域 | 规格文件 | 需求数 | 场景数 |
|----|---------|-------|-------|
| auth | docs/specs/auth/spec.md | 3 | 7 |
| chat | docs/specs/chat/spec.md | 2 | 5 |

跳过：{{context.session.skipped_count}} 个未澄清功能

下一步：执行 /harness-specify-arch 生成架构规格（建议新会话）
```

**有代码调研时**：

```
## 域规格生成完成

已生成：{{context.session.domain_count}} 个域规格文件
已调研：{{context.session.researched_file_count}} 个源码文件

| 域 | 规格文件 | 需求数 | 场景数 | 已有实现覆盖 |
|----|---------|-------|-------|-------------|
| auth | docs/specs/auth/spec.md | 3 | 7 | 2/3（66%） |
| chat | docs/specs/chat/spec.md | 2 | 5 | 0/2（0%） |

调研报告：docs/specs/_research/research-notes.md

跳过：{{skipped_count}} 个未澄清功能

下一步：执行 /harness-specify-arch 生成架构规格（建议新会话）
```

## 约束

- 不修改 project.yaml
- 不生成工单文件
- 不写代码（调研阶段只读不写）
- 规格文档中禁止出现实现细节
- 调研报告只记录事实，不做主观判断

## 验证清单

- [ ] 每个澄清的功能都有对应的规格需求
- [ ] 每个需求至少一个场景
- [ ] 场景使用"前置/当/则"格式
- [ ] 无实现细节混入
- [ ] 有代码调研时，research-notes.md 已生成
