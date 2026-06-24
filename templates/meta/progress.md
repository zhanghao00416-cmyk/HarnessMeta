# 进度日志

> 记录项目工单执行进度。每次工单状态变更时更新。

---

## 元信息

| 字段 | 值 |
|------|-----|
| 项目名称 | {{project_name}} |
| 创建时间 | {{created_at}} |
| 最后更新 | {{last_updated}} |

---

## 变更暂停点

<!-- 进入变更流程（harness-change）时填写，归档（harness-archive）时清空 -->
<!-- 字段名与 docs/meta/CHANGE_WORKFLOW.md 步骤 1 保持一致 -->

| 字段 | 值 |
|------|-----|
| **task_mode** | `linear` / `change` |
| **resume_feature_id** | （暂停前 active 的 feature_id，恢复主线时用） |
| **resume_ticket** | （暂停前 active 的工单 id，恢复主线时用） |
| **change_name** | （变更目录名，即 changes/ 下的文件夹名） |

> 普通工单执行中断不需要填本段，下面「活跃工单」表的「当前阶段」列已记录中断点。

**填写示例**（变更流程启动后）：

| 字段 | 值 |
|------|-----|
| **task_mode** | `change` |
| **resume_feature_id** | `F06` |
| **resume_ticket** | `F06` |
| **change_name** | `fix-login-redirect` |

---

## 活跃工单

| 工单 | 标题 | 状态 | 当前阶段 |
|------|------|------|---------|
| {{id}} | {{title}} | {{status}} | {{phase}} |

---

## 已完成工单

| 工单 | 标题 | 完成时间 | 验证结果 |
|------|------|---------|---------|
| {{id}} | {{title}} | {{completed_at}} | {{verify_result}} |

---

## 会话历史

| 会话 | 日期 | 执行工单 | 产出摘要 |
|------|------|---------|---------|
| {{session_id}} | {{date}} | {{orders}} | {{summary}} |

---

> 此文件由 AI 在每次工单完成后自动更新。
> 人工也可随时编辑以修正进度。
