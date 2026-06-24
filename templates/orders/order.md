# 工单 {{id}}：{{title}}

## 元数据
- **id**: {{id}}
- **state**: {{status}}
- **dependencies**: {{dependencies}}
<!-- 以下三个字段首次工单恒为“无”，仅变更场景（Flow B）使用 -->
- **patches**: {{patches}}
- **supersedes**: {{supersedes}}
- **superseded-by**: {{superseded_by}}

## 功能三元组
- **行为**：{{behavior_brief}}
- **验证**：`{{verify_command}}`
- **状态**：not_started → active → passing

## 验收标准（全部通过才能标 passing）
- [ ] `{{verify_command}}` 通过
- [ ] 分层依赖检查通过（遵循 ARCHITECTURE.md）
- [ ] 相关测试通过
- [ ] `feature_list.json` 状态 + evidence 已更新

## 关键约束
- 依赖方向严格遵守 `ARCHITECTURE.md`
- 错误码：`docs/specs/_architecture/ERROR_CODE.md`
- API 契约：`docs/specs/_architecture/API_CONTRACT.md`
- 域职责：`docs/specs/_architecture/DOMAIN_MAP.md`
- `[TBD: filled by Fxx]` 见 `AGENTS.md` — 不表示章节为空

## 不做（本工单范围外）
- 不做本功能三元组描述之外的事情
- 不修改已 passing 功能的代码（走 `docs/meta/CHANGE_WORKFLOW.md`）

---

## ━━━ 阶段 1：只读不写（禁止生成代码）━━━

### 1.1 前序代码依赖（必须 read_file）

{{code_deps}}

### 1.2 必读 docs

{{required_docs}}
- `ARCHITECTURE.md`（分层规则）
- `docs/meta/DEPENDENCY_MAP.md`（本工单 {{id}} 行）

### 1.3 阶段 1 交付物

1. 与现有实现/契约的差异清单
2. 错误码与边界条件（引用 ERROR_CODE.md）
3. 预计新增/修改文件清单（可与阶段 2 实现清单对照，允许阶段 1 微调）
4. 明确「不做」范围确认

**阶段 1 通过后才可进入阶段 2。**

---

## ━━━ 阶段 2：正式生成代码 ━━━

### 2.1 契约对齐（填写或确认）

| 项 | 约定 |
|----|------|
| 路由 / 能力 | （从 API_CONTRACT 或工单行为填写） |
| 响应 | JSON envelope / SSE（见架构规格） |
| 错误 | 参照 ERROR_CODE.md 域编码范围 |

### 2.2 实现清单（路径级）

{{implementation_plan}}

### 2.3 环境 / 命令

- 验证：`{{verify_command}}`

---

## ━━━ 阶段 3：自审、验证、交接 ━━━

### 3.1 对照 evaluator-rubric.md 自审（无 Block 项）

#### 完整性
- [ ] 功能三元组中的所有行为已实现
- [ ] 验证命令执行通过
- [ ] 无遗漏的 TODO 或占位代码

#### 正确性
- [ ] 实现匹配行为描述，无偏差
- [ ] 边界条件和错误处理已覆盖
- [ ] 状态流转逻辑正确

#### 一致性
- [ ] 遵循 ARCHITECTURE.md 中的架构约束
- [ ] 命名规范与项目一致
- [ ] 目录结构符合项目约定

### 3.2 docs 同步

- 本工单改动的 API / 错误码 / 数据模型须同步对应 `docs/specs/` 文件
- 将相关 `[TBD: filled by Fxx]` 改为 `[filled by Fxx]`

### 3.3 状态更新

1. 更新 `feature_list.json`（passing + evidence）
2. 更新 `progress.md`（标记本工单状态）
3. 更新 `session-handoff.md`（记录本次产出 + 下一步操作）

---

## ━━━ 执行指令（复制给代码工具）━━━

```text
按 AGENTS.md 启动；执行工单 {{id}}，严格阶段 1→2→3。
阶段 1：读 DEPENDENCY_MAP {{id}} 行 + 上文 docs + 前序代码，首段约束摘要 ≥5 条，输出 §1.3 交付物，禁止写代码。
阶段 2：仅实现 §2.2 清单；验证：{{verify_command}}
阶段 3：自审 + 更新 feature_list / progress / session-handoff
```

## ━━━ 执行指令结束 ━━━
