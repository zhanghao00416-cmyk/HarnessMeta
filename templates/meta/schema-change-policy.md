# Schema Change Policy

> **版本**：v1.1
> **日期**：2026-06-24
> **适用范围**：所有 Frozen Schema 文件
>   - `templates/context-schema.yaml`
>   - `templates/meta/artifact-meta-schema.yaml`
>   - `templates/meta/spec-schema.yaml`
>   - `templates/meta/task-schema.yaml`
>   - `templates/meta/architecture-schema.yaml`
>   - **`templates/meta/verify-schema.yaml`** ← Phase 2.5 新增

---

## 1. 政策背景

Phase 2 已于 2026-06-24 完成五层 Schema 的正式冻结，Phase 2.5 已于 2026-06-24 完成 Verify Schema 冻结：

| Schema | 版本 | 冻结日期 |
|--------|------|----------|
| Context Contract | v1.0-frozen | 2026-06-24 |
| Artifact Meta Schema | v1.0-frozen | 2026-06-24 |
| Spec Schema | v1.0-frozen | 2026-06-24 |
| Task Schema | v1.0-frozen | 2026-06-24 |
| Architecture Schema | v1.0-frozen | 2026-06-24 |
| **Verify Schema** | **v1.0-frozen** | **2026-06-24** |

冻结后，任何 Schema 修改必须遵循本政策，避免破坏既有 Skill、已生成的 Artifact 和跨 Schema 引用完整性。

---

## 2. 修改分类（SemVer 规则）

Schema 采用 SemVer 三段版本号：`MAJOR.MINOR.PATCH`。

### 2.1 PATCH：兼容性修复

**定义**：仅修改描述性内容，不改变字段语义或必填规则。

**允许的操作**：

- 修正文档注释、示例、说明文字
- 修正拼写错误、格式错误
- 补充字段描述（不改 required / type / format）
- 补充示例（examples）字段
- 调整 YAML 注释的可读性

**禁止的操作**：

- 修改任何字段的 `type`
- 修改任何字段的 `required: true`
- 删除任何字段
- 修改 ID 格式（format）
- 修改枚举值（enum）的含义

**版本号变更**：`v1.0.0 → v1.0.1`

**审批流程**：单人 review 即可（harness-meta 维护者）。

---

### 2.2 MINOR：新增可选字段

**定义**：新增字段或将现有字段改为可选，但不破坏既有 Artifact。

**允许的操作**：

- 新增字段（默认 `required: false`）
- 将字段从 `required: true` 改为 `required: false`（降低约束）
- 在枚举值末尾新增枚举项
- 新增可选的 ID 类型（不影响既有 ID 格式校验）

**禁止的操作**：

- 删除任何字段
- 修改任何字段的 `type`
- 修改 ID 格式（format）
- 修改既有枚举值的含义
- 将字段从 `required: false` 改为 `required: true`（提高约束属于 MAJOR）

**版本号变更**：`v1.0.0 → v1.1.0`

**审批流程**：

1. 提交 Schema 变更提案（包含新增字段用途、影响范围、是否影响既有 Artifact）
2. 由 harness-meta 维护者 review
3. 更新 Schema 头部版本号
4. 在 CHANGELOG 中记录新增字段
5. 通知所有依赖该 Schema 的 Skill 更新其生成逻辑

---

### 2.3 MAJOR：破坏性变更

**定义**：删除字段、修改语义、改变必填规则、修改 ID 格式。

**允许的操作**：

- 删除字段
- 修改字段的 `type`
- 修改字段的 `format`
- 修改既有枚举值的含义
- 将字段从 `required: false` 改为 `required: true`
- 修改 ID 格式（如 `REQ-{domain}-{seq}` 改为其他格式）

**版本号变更**：`v1.0.0 → v2.0.0`

**审批流程**：

1. 提交 RFC（Request for Comments）文档，包含：
   - 变更原因和动机
   - 详细影响范围（哪些 Skill 依赖该字段、已有 Artifact 的兼容性）
   - 迁移方案（如何处理既有 Artifact）
   - 回滚方案
2. 维护者社区讨论期（至少 7 天）
3. 维护者投票通过
4. 发布 v2.0.0 并提供迁移指南
5. 保留 v1.x 版本作为 LTS（至少 6 个月）

---

## 3. 禁止事项

### 3.1 严禁直接修改 Frozen Schema

禁止行为：

- 直接编辑 Schema 文件修改字段定义
- 通过临时补丁绕过变更流程
- 在未升级版本号的情况下修改字段语义

合规行为：

- 提交变更提案
- 通过审批流程后修改
- 更新版本号并记录 CHANGELOG

### 3.2 严禁"语义漂移"

即使在同一 MAJOR 版本内，也禁止：

- 让 `description` 字段的含义悄悄改变
- 让 `enum` 的实际取值范围悄悄改变
- 让 `format` 的实际校验规则悄悄改变

任何"语义漂移"等同于破坏性变更，必须升级 MAJOR。

---

## 4. 变更记录

所有 Schema 变更必须在 Schema 文件的"变更历史"部分和 `CHANGELOG.md`（如存在）中记录。

### 4.1 Schema 内的变更记录格式

在每个 Schema 文件的"变更历史"部分，按时间倒序记录：

```markdown
## 变更历史

### v1.1.0（2026-XX-XX）

- **新增字段**：`task.estimated_complexity`（可选）
- **新增枚举值**：`validation.type` 新增 `static_analysis`
- **影响范围**：harness-order、harness-execute、harness-verify

### v1.0.1（2026-XX-XX）

- **修正**：`spec.requirements[].priority` 描述文字错误
- **影响范围**：仅文档
```

---

## 5. 与 Skill 的关系

### 5.1 Skill 必须兼容 Frozen Schema

所有依赖 Schema 的 Skill 必须：

- 只使用 Frozen Schema 中已定义的字段
- 不依赖字段的具体顺序
- 容忍可选字段缺失
- 对未知字段采取忽略策略（forward compatibility）

### 5.2 Schema 变更后 Skill 更新责任

当 Schema 发生 MINOR 或 MAJOR 变更时：

- MINOR：依赖该 Schema 的 Skill 可选择更新（建议但不强制）
- MAJOR：所有依赖该 Schema 的 Skill 必须更新，否则视为不兼容

---

## 6. 审批角色

| 角色 | 权限 |
|------|------|
| Schema 作者 | 提交 PATCH 和 MINOR 变更 |
| harness-meta 维护者 | 审批 PATCH 和 MINOR 变更 |
| harness-meta 架构委员会 | 审批 MAJOR 变更（RFC） |

---

## 7. 例外处理

紧急安全修复（如发现 ID 校验漏洞）可走快速通道：

1. 维护者直接发布 PATCH 版本
2. 在 CHANGELOG 中标注 `[SECURITY]` 标记
3. 24 小时内通知所有依赖方

---

## 8. Phase 3 预备

Phase 2.5 Verify Schema 已于 2026-06-24 冻结，本政策已扩展覆盖：

- ✅ `verify-schema.yaml`（v1.0-frozen）
- 任何后续新增的 Schema 类型

Phase 3 Context Engine 进入后，可能新增的 Schema 类型：

- **Runtime Schema**（运行时状态，区别于 Frozen Schema，不进入冻结）
- **Capability Schema**（Skill 能力描述）
- **Context Schema 扩展**（动态上下文打包）

Phase 3 新增的 Schema 类型如需进入 Frozen 状态，需发布新的 Freeze Declaration 并扩展本政策。

---

## 9. Verify Schema 特殊说明

由于 Verify Schema 是 Phase 2.5 新增的协议层，其变更策略有一些特殊考虑：

### 9.1 V6 status 字段规则

`context.validation_status_map` 是 Verify Schema 引入的运行时状态字段，**禁止**将其合并到 Task Schema：

| 方案 | 评价 |
|------|------|
| ❌ 在 Task Schema 中新增 `validation_steps[].status` | 破坏 Frozen Schema（Task v1.0-frozen） |
| ✅ 在 Verify Schema 维护 `validation_status_map` | 不影响 Task Schema，向后兼容 |

如需修改 `validation_status_map` 的 value 枚举（`passed` / `failed` / `skipped` / `error`），按以下规则：

| 修改类型 | 版本升级 | 示例 |
|---------|---------|------|
| 增加新枚举值 | MINOR（v1.1.0） | 新增 `cancelled` |
| 修改枚举值含义 | MAJOR（v2.0.0） | `passed` 从"通过"改为"通过+警告" |
| 删除枚举值 | MAJOR（v2.0.0） | 移除 `skipped` |

### 9.2 严重度词汇表规则

Verify Schema 采用"统一字段名 + 分维度词汇表"策略：

| 维度 | 词汇表 | 字段位置 |
|------|--------|---------|
| 架构约束严重度 | `must` / `should` / `may` | `coverage.constraint_coverage.severity_distribution` |
| 运行时验证状态 | `passed` / `failed` / `skipped` / `error` | `context.validation_status_map.value` |
| 问题严重度 | `block` / `warning` / `info` | `checks[].severity`、`failures[].impact` |

**冻结原则**：

- ✅ 字段名必须一致（如统一使用 `severity` 字段名）
- ✅ 允许不同维度使用不同枚举值（语义独立）
- ❌ 不强制所有维度使用同一词汇表

如需新增词汇表（如"安全等级"用 `critical` / `high` / `medium` / `low`），必须：

1. 在 `verify-schema.yaml` §4 增加新章节
2. 明确字段位置和使用方
3. 按 MINOR 流程（v1.1.0）

---

## 附录：快速判断流程

```
需要修改 Schema 字段
    ↓
是否修改字段的 type / format / required / enum 含义？
    ├── 否 → PATCH（v1.0.x）
    │         维护者单人 review
    │
    └── 是 → 是否删除字段或破坏既有 Artifact？
              ├── 否 → MINOR（v1.x.0）
              │         提交提案 + 维护者 review
              │
              └── 是 → MAJOR（vx.0.0）
                        RFC + 社区讨论 + 投票
```