# 变更工作流

> 新建功能用 `orders/`；**修改已有功能/接口**用本流程。
> 目标：把「改什么、改哪些文件、按什么顺序、如何验证、如何恢复主线」**固定下来**，避免漏步骤。

---

## 1. 三种变更类型（先选型）

| 类型 | 代号 | 适用 | 是否改主规格 |
|------|------|------|-------------|
| **热修复** | `hotfix` | Bug、逻辑错误、单模块小改；**不改**对外契约 | 否 |
| **常规变更** | `standard` | 改行为契约、加小功能、改字段 | **是（必须先于代码）** |
| **复杂功能** | `feature` | 跨多模块、新行为、引入新依赖 | 是，且需设计文档 |

**选型不准时，按更严格的来：** 涉及 API 字段 → 至少走 `standard`。

---

## 2. 变更流程（对应 4 个 Skill）

```
/harness-change    → 生成变更文件夹（proposal + delta-spec + design + tasks）
/harness-apply     → 按 tasks.md 逐个实现
/harness-verify    → 三维度检查（完整性/正确性/一致性）
/harness-archive   → 归档变更，合并 delta 到主规格
```

### 步骤 1：暂停主线

编辑 `progress.md` 的「变更暂停点」段，填写以下字段（字段名须与本模板一致）：

```markdown
## 变更暂停点（task_mode=change 时填写）

| 字段 | 值 |
|------|-----|
| **task_mode** | `change` |
| **resume_feature_id** | （暂停前 active_feature_id） |
| **resume_ticket** | （暂停前 active 工单 id） |
| **change_name** | （待创建的变更目录名，kebab-case） |
```

> 变更追踪以 `changes/<change_name>/` 目录名 + `proposal.md` frontmatter 的 `created` 时间戳为准，**不使用单独的 CO-NNN 编号**（避免与目录名重复维护）。

### 步骤 2：执行 /harness-change

AI 根据复杂度选 schema，在 `changes/<name>/` 下生成：

| 文件 | 内容 |
|------|------|
| `proposal.md` | 变更动机、影响范围、预期行为 |
| `delta-spec.md` | 增量规格（ADDED/MODIFIED/REMOVED） |
| `design.md` | 技术设计（仅 feature schema） |
| `tasks.md` | 任务清单（checkbox） |

人类审阅 proposal 后确认继续。

### 步骤 3：执行 /harness-apply

AI 读取 `tasks.md`，逐个实现任务，完成后勾选 checkbox。

### 步骤 4：执行 /harness-verify

AI 运行三维度检查，输出验证报告：

- **CRITICAL**：必须修复才能归档
- **WARNING**：建议修复
- **SUGGESTION**：可选优化

### 步骤 5：执行 /harness-archive

验证通过后，AI 将 delta-spec 合并回主规格，变更文件夹移入 `changes/archive/`。

恢复主线：

- `progress.md`「变更暂停点」段：`task_mode` 改回 `linear`，清空其余字段
- `active_ticket` / `active_feature_id` 恢复为暂停前的值（即 `resume_ticket` / `resume_feature_id`）
- 在 `session-handoff.md` 写恢复后的开场白

---

## 3. 接口变更额外强制清单

凡涉及 API 契约的变更，`/harness-apply` 前必须完成 `docs/meta/API_CHANGE_CHECKLIST.md` 全部 applicable 项。

同步文件（按改动范围）：

1. `docs/specs/{{domain}}/spec.md`（主规格）
2. `ARCHITECTURE.md`（若涉及错误码/分层）
3. `docs/meta/FACT_REGISTRY.md`（若涉及枚举/常量）
4. `docs/meta/DEPENDENCY_MAP.md`（若跨工单依赖变化）

---

## 4. 验证标准（所有变更类型）

`/harness-archive` 前必须：

- [ ] 验证命令通过（`verify_commands.health_check`）
- [ ] `/harness-verify` 无 CRITICAL
- [ ] `progress.md` 已恢复主线或指向下一变更
- [ ] `session-handoff.md` 含下一会话开场白
- [ ] 若接口变更：`API_CHANGE_CHECKLIST.md` 已勾选
