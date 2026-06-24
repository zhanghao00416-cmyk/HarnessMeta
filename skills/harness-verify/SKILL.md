---
name: harness-verify
description: 三维度验证。检查变更实现是否完整、正确、一致，生成验证报告。
---

# harness-verify：三维度验证

## 触发条件

harness-apply 完成后，用户要求验证实现时执行。

## 输入

- 变更名称（可选）
- `changes/{{change_name}}/`（完整变更文件夹）

## 步骤

### 1. 选择变更

如果未指定，自动选择或提示用户选择（同 harness-apply）。

### 2. 读取变更上下文

读取变更文件夹中所有 artifacts。

### 3. 初始化验证报告

创建三维度报告结构：

- **完整性**（Completeness）：任务和规格覆盖
- **正确性**（Correctness）：实现匹配规格意图
- **一致性**（Coherence）：设计决策体现在代码中

每个维度可报告三个级别：

| 级别 | 含义 |
|------|------|
| CRITICAL | 必须修复才能归档 |
| WARNING | 建议修复 |
| SUGGESTION | 可选改进 |

### 4. 验证完整性

**任务完成情况**：

- 解析 `tasks.md` 中的 checkbox
- 统计 `- [ ]`（未完成）vs `- [x]`（已完成）
- 每个未完成任务 → CRITICAL

**规格覆盖**：

- 如果存在 `delta-spec.md`，提取所有需求
- 在代码中搜索对应实现
- 未找到实现的需求 → CRITICAL

### 5. 验证正确性

**需求实现映射**：

- 对每个需求，搜索代码中的实现证据
- 实现偏离规格意图 → WARNING

**场景覆盖**：

- 对每个场景（前置/当/则），检查代码是否处理
- 检查是否有对应测试
- 未覆盖的场景 → WARNING

### 6. 验证一致性

**设计遵循**：

- 如果存在 `design.md`，提取技术决策
- 检查代码是否遵循这些决策
- 矛盾 → WARNING

**代码模式一致性**：

- 检查文件命名、目录结构、编码风格
- 与项目现有模式比较
- 显著偏离 → SUGGESTION

### 7. 附修复路径（针对每个问题）

每个 CRITICAL 和 WARNING 问题，必须给出**具体修复路径**——不只说"建议修复"，要说"在哪个 Skill 的哪一步做什么"。

| 问题级别 | 修复路径模板 |
|---------|-------------|
| CRITICAL | 回到 `harness-apply` 阶段 2，对应任务修改 → 再跑 `harness-verify` |
| CRITICAL（涉及设计） | 回到 `harness-change` 更新 delta-spec / design → 重新生成 tasks |
| WARNING | 回到 `harness-apply` 阶段 3 自审，补完遗漏 → 或新建一个 hotfix 变更处理 |
| SUGGESTION | 在下一次迭代处理，或新建 follow-up 变更 |

报告中的每个问题行尾附 `→ 修复路径：{{action}}`。

### 8. 生成验证报告

```
## 验证报告：{{change_name}}

### 摘要
| 维度 | 状态 |
|------|------|
| 完整性 | {{x}}/{{y}} 任务完成，{{n}} 个需求 |
| 正确性 | {{m}}/{{n}} 需求覆盖 |
| 一致性 | {{status}} |

### CRITICAL（必须修复）
1. {{issue}} — {{recommendation}} → 修复路径：{{action}}

### WARNING（建议修复）
1. {{issue}} — {{recommendation}} → 修复路径：{{action}}

### SUGGESTION（可选改进）
1. {{issue}} — {{recommendation}} → 修复路径：{{action}}

### 最终评估
- **如有 CRITICAL**：发现 {{n}} 个严重问题，必须修复后再归档。修复路径见上表。
- **仅 WARNING**：无严重问题，可以归档。{{n}} 个警告可选修复。修复路径见上表。
- **全部通过**：所有检查通过。**下一步**：直接执行 `harness-archive` 归档变更。
```

## 约束

- 不修改代码（只读验证）
- 不修改变更文件夹中的文件
- 验证启发：不确定时，SUGGESTION > WARNING > CRITICAL（宁缺勿滥）
- 每个问题必须给出具体建议和文件引用
