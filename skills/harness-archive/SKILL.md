---
name: harness-archive
description: 归档变更。将增量规格合并到主规格，移动变更文件夹到 archive。
---

# harness-archive：变更归档

## 触发条件

harness-verify 通过后，用户要求归档变更时执行。

**执行顺序**：
1. harness-verify 通过（无 CRITICAL）
2. harness-project-memory（可选，积累本次经验）
3. harness-archive（本 Skill）

支持两种模式：
- **单个归档**：归档一个变更文件夹
- **批量归档**：归档多个已完成的变更，自动检测规格冲突

## 输入

- 变更名称（可选，省略时列出所有可选）
- `--bulk` 标志（可选，启用批量模式）
- `changes/`（变更目录）
- `docs/specs/`（主规格目录）

## 步骤

### 1. 选择变更

如果未指定，自动选择或提示用户选择。

**批量模式**：扫描 `changes/` 下所有未归档的变更文件夹，列出已完成全部任务的变更：

```
发现 3 个可归档变更：
- add-dark-mode（全部任务完成）
- fix-login-redirect（全部任务完成）
- update-footer（全部任务完成）

检查规格冲突...
⚠ add-dark-mode 和 update-footer 都涉及 docs/specs/ui/spec.md

将按时间顺序合并，冲突项以时间较晚者为准。
确认归档这 3 个变更吗？
```

用户确认后，按时间顺序逐个执行步骤 2–5。

**时间顺序判定**：以每个变更文件夹内 `proposal.md` frontmatter 中的 `created` 字段（ISO 8601 时间戳）为准。**禁止使用文件系统 ctime**——git checkout、跨设备复制、重命名都会重置 ctime，导致归档顺序错乱。

读取顺序：
1. 尝试解析 `proposal.md` 顶部的 YAML frontmatter 中的 `created` 字段
2. 字段缺失或格式错误 → 警告用户（该变更需要重新走 harness-change 以写入 created 字段）
3. frontmatter 解析失败 → 按目录名字母序回退

### 2. 检查完成状态

**任务完成检查**：

- 读取 `tasks.md`，统计未完成任务
- 有未完成 → 警告，询问用户是否继续

**验证状态检查**：

- 如已执行 harness-verify，检查是否有 CRITICAL 问题
- 有 CRITICAL → 警告，建议先修复

### 3. 合并增量规格

如果存在 `delta-spec.md`，执行合并：

**合并规则**：

| Delta 操作 | 合并动作 |
|------------|---------|
| 新增需求 | 追加到主规格的"需求"段末尾 |
| 修改需求 | 替换主规格中的同名需求（完整替换） |
| 移除需求 | 从主规格中删除同名需求 |
| 重命名需求 | 修改主规格中的需求标题 |

**合并流程**：

1. 读取 `changes/{{change_name}}/delta-spec.md`
2. 读取对应的 `docs/specs/{{domain}}/spec.md`
3. 按上述规则执行合并
4. 写回主规格文件
5. 报告合并结果

```
增量规格合并：
✓ 新增：{{requirement_name}}（2 个场景）
✓ 修改：{{requirement_name}}（替换完整内容）
✓ 移除：{{requirement_name}}
```

### 4. 移动到归档

```
changes/{{change_name}}/  →  changes/archive/YYYY-MM-DD-{{change_name}}/
```

归档目录名格式：`YYYY-MM-DD-{{change_name}}`

检查目标是否已存在：
- 已存在 → 报告错误，建议重命名或等待
- 不存在 → 执行移动

### 5. 更新项目状态

- 更新 `progress.md`：记录变更完成
  - **恢复主线**：将「变更暂停点」段的 `task_mode` 改回 `linear`，清空 `resume_feature_id` / `resume_ticket` / `change_name` 字段
  - 读取清空前的 `resume_ticket` / `resume_feature_id`，作为恢复后的 active 工单/功能

  > 清空后状态：`task_mode = linear`，其余三个字段均为 `-`（与初始化时一致）
- 更新 `session-handoff.md`：记录归档信息 + 恢复主线后的开场白
- 更新 `QUICK_REFERENCE.md`：更新当前状态

### 6. 输出归档报告

**单个模式**：

```
## 归档完成

变更：{{change_name}}
Schema：{{schema_name}}
归档位置：changes/archive/{{date}}-{{change_name}}/
规格合并：✓ 已合并到 docs/specs/

全部 artifact 完成。全部任务完成。
```

**批量模式**：

```
## 批量归档完成

已归档 3 个变更：
✓ add-dark-mode → changes/archive/{{date}}-add-dark-mode/
✓ fix-login-redirect → changes/archive/{{date}}-fix-login-redirect/
✓ update-footer → changes/archive/{{date}}-update-footer/

规格合并顺序：add-dark-mode → update-footer（冲突项以较晚者为准）
全部变更已归档。
```

## 约束

- 不修改变更文件夹的内容（只移动）
- 合并增量规格时不改动未被 delta 影响的需求
- 归档目录保留完整变更上下文（proposal + specs + design + tasks）
- WARNING 不阻塞归档（只 CRITICAL 阻塞）
