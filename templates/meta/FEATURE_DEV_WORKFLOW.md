# 功能开发流程

本文档定义新功能从讨论到交付的标准流程。

---

## 四步流程

```
澄清需求 → 生成规格 → 生成工单 → 三段式执行
```

| 步骤 | Skill | 交付物 |
|------|-------|--------|
| 1. 澄清 | `/harness-clarify` | project.yaml 中的 behavior/docs/verify_command |
| 2. 规格 | `/harness-specify` | docs/specs/ 下按域分组的 spec.md |
| 3. 工单 | `/harness-order` | orders/ 下的工单文件 + DEPENDENCY_MAP.md 更新 |
| 4. 执行 | `/harness-execute` | 代码 + 测试 + 自审 + progress.md 更新 |

**原则**：一次会话 / 一次 PR **只执行一条**工单。

---

## 修改已有功能

**新功能**用本流程；**修改已有功能/接口**用 `docs/meta/CHANGE_WORKFLOW.md`。

三种变更类型：

| 类型 | 代号 | Schema |
|------|------|--------|
| 热修复 | `hotfix` | proposal → tasks |
| 常规变更 | `standard` | proposal → delta-spec → tasks |
| 复杂功能 | `feature` | proposal → delta-spec → design → tasks |

修改已通过验证的功能 **禁止**直接改代码，必须走变更流程。

---

## 讨论阶段必对齐的问题

执行 `/harness-clarify` 前，每个功能至少确认：

1. **系统边界**：这个功能属于哪一层？（api / domain / services / infra）
2. **对外契约**：新路由还是改现有？请求/响应格式？
3. **默认值与限制**：超时、数量上限、集合名等
4. **错误策略**：失败返回哪个错误码
5. **非目标**：明确不做的事

结论必须写入 project.yaml 的 `behavior` 字段，避免代码阶段反复猜测。

---

## 按影响面选择 docs

| 变更类型 | 必读/必改 docs |
|----------|----------------|
| 新 API / 改字段 | `docs/specs/{{domain}}/spec.md` + `ARCHITECTURE.md` |
| 数据模型 | `docs/specs/{{domain}}/spec.md` |
| 纯内部重构 | 可跳过规格更新，仍需工单 + 测试 |

---

## 工单三段式

- **阶段 1（只读）**：读 DEPENDENCY_MAP、必读 docs、前序代码 → 输出差异与文件清单 → **禁止写代码**
- **阶段 2（写码）**：schemas → domain → services/infra → api + 测试
- **阶段 3（自审）**：对照契约自审，输出修改文件清单 + 评审评分

给 Agent 的指令示例：

```text
执行工单 {{F04}}：{{功能标题}}，严格阶段 1→2→3；
先读 AGENTS.md、feature_list.json、docs/meta/DEPENDENCY_MAP.md 对应行。
```

---

## 何时可简化

| 场景 | 是否仍需 docs + 工单 |
|------|---------------------|
| 新 API / 改字段 / 新错误码 | **必须** 规格 + 工单 |
| 纯 bugfix、契约不变 | 可简化工单，需测试复现 |
| 新增跨模块功能 | **必须** 先更新规格再生成工单 |
