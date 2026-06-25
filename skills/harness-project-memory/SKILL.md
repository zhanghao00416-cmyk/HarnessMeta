---
name: harness-project-memory
description: 维护长期项目记忆和架构知识。从审查报告、运行时验证报告、规格文档中提取决策、约定、教训和技术偏好，追加到项目记忆文件中。只追加，不删除历史。
---

# harness-project-memory：长期项目记忆

## 触发条件

以下场景执行：

1. **工单/变更完成后**：`harness-verify` 通过后，执行本 Skill 积累本次经验
2. **项目里程碑**：迭代结束、版本发布时，批量积累阶段性知识
3. **用户主动要求**：用户说"记录本次经验"或"更新项目记忆"
4. **审查发现新模式**：`harness-review-loop` 或 `harness-runtime-verify` 发现可复用的模式或反复出现的问题时

## 输入

- `orders/<ORDER_ID>/review-report.md`（可选，代码审查报告）
- `orders/<ORDER_ID>/runtime-report.md`（可选，运行时验证报告）
- `changes/<CHANGE_NAME>/` 下的规格文档（`delta-spec.md`、`design.md`、`tasks.md`）
- `docs/architecture/` 或 `ARCHITECTURE.md`（架构文档）
- 已有记忆文件 `docs/meta/memory/`（如存在）

## 输出

更新/创建：

```text
docs/meta/memory/architecture-decisions.md    # 架构决策记录（ADR）
docs/meta/memory/project-conventions.md        # 项目约定（命名/目录/API/测试）
docs/meta/memory/technology-profile.yaml         # 技术栈画像
docs/meta/memory/lessons-learned.md            # 教训与陷阱
```

更新：
- `progress.md`：记录记忆更新状态

---

## 步骤

### 1. 读取输入源

收集以下来源的信息：

| 来源 | 提取内容 |
|------|---------|
| `review-report.md` | 代码质量问题模式、反复出现的错误类型、修复策略 |
| `runtime-report.md` | 常见的构建/测试失败模式、环境配置陷阱 |
| `delta-spec.md` / `design.md` | 设计决策、技术选型理由、架构变更 |
| `ARCHITECTURE.md` | 架构原则、约束条件、目录约定 |
| 已有记忆文件 | 避免重复，合并相似条目 |

### 2. 提取架构决策（ADR）

识别新的架构决策：

**判断标准**（满足任一即记录）：
- 引入了新的设计模式（如 Repository Pattern、CQRS、Event Sourcing）
- 选择了新的技术/框架（如从 Flask 迁移到 FastAPI）
- 修改了架构约束（如新增跨域调用规则、调整分层边界）
- 解决了架构层面的权衡（如一致性 vs 可用性、同步 vs 异步）

**ADR 格式**：

```markdown
## ADR-XXX: {{决策标题}}

- **日期**: {{YYYY-MM-DD}}
- **状态**: proposed / accepted / deprecated / superseded
- **来源**: {{工单/变更 ID}}

### 上下文

{{决策背景}}

### 决策

{{具体决策内容}}

### 后果

- **正面**: {{}}
- **负面**: {{}}
- **风险**: {{}}

### 替代方案

{{考虑过的其他方案及未选原因}}
```

追加到 `docs/meta/memory/architecture-decisions.md`。

### 3. 提取项目约定

识别新的命名、目录、API、测试约定：

**约定类型**：

| 类别 | 示例 |
|------|------|
| **命名约定** | 函数名用 `snake_case`，类名用 `PascalCase`，API 端点用 kebab-case |
| **目录约定** | 所有服务层放在 `services/`，禁止在 `router/` 中写业务逻辑 |
| **API 约定** | 响应统一用 `EnvelopeResponse`，错误码必须注册到 ERROR_CODE.md |
| **测试约定** | 每个 service 必须有对应测试文件，命名 `{name}_test.py` |

**约定格式**：

```markdown
## {{约定名称}}

- **类型**: naming / folder / api / testing / other
- **来源**: {{工单/变更 ID}}
- **日期**: {{YYYY-MM-DD}}

{{约定描述}}

### 示例

{{正确示例}}

{{错误示例}}
```

追加到 `docs/meta/memory/project-conventions.md`。

### 4. 更新技术画像

维护 `docs/meta/memory/technology-profile.yaml`：

```yaml
profile:
  updated_at: "2024-01-15"
  version: 2

framework:
  backend: FastAPI
  frontend: Vue 3
  orm: SQLAlchemy
  migration: Alembic

database:
  primary: PostgreSQL
  cache: Redis
  vector: Qdrant

testing:
  backend: pytest
  frontend: vitest
  coverage: "80%"

deployment:
  type: docker-compose
  ci: GitHub Actions
  cd: manual

# 变更历史
changelog:
  - date: "2024-01-15"
    change: "新增向量数据库 Qdrant"
    source: "F08_RAG检索"
  - date: "2024-01-10"
    change: "前端从 Vue 2 升级到 Vue 3"
    source: "F01_项目骨架"
```

**更新规则**：
- 技术栈发生变化时更新
- 在 `changelog` 中记录变更历史和来源
- 保留历史版本，不覆盖旧记录

### 5. 记录教训

从审查和验证失败中提取教训：

**记录条件**（满足任一）：
- 同一类问题在多个工单中重复出现
- 修复成本较高的问题（如架构级重构）
- 容易忽视但影响重大的问题（如安全漏洞）
- 环境/工具链相关的陷阱（如依赖版本冲突）

**教训格式**：

```markdown
## {{问题简述}}

- **类型**: recurring / high-cost / easy-to-miss / environment
- **来源**: {{工单/变更 ID}}
- **日期**: {{YYYY-MM-DD}}
- **频率**: {{首次/偶尔/反复}}

### 现象

{{问题表现}}

### 根因

{{根本原因分析}}

### 解决方案

{{修复方法}}

### 预防措施

{{如何避免再次发生}}

### 相关条目

- [链接到其他相关教训]
```

追加到 `docs/meta/memory/lessons-learned.md`。

### 6. 防止重复

追加前检查已有记忆：

- **ADR**：检查标题和决策内容是否已存在
- **约定**：检查同类型约定是否已覆盖
- **技术画像**：检查技术栈是否已记录
- **教训**：检查问题现象是否已记录

**处理方式**：
- 完全重复 → 跳过
- 相似但补充 → 合并到现有条目，添加新来源
- 新内容 → 追加

### 7. 生成摘要

返回更新摘要：

```yaml
summary:
  decisions_added: 2
  conventions_added: 1
  lessons_added: 3
  technology_updates: 1

files_updated:
  - docs/meta/memory/architecture-decisions.md
  - docs/meta/memory/project-conventions.md
  - docs/meta/memory/technology-profile.yaml
  - docs/meta/memory/lessons-learned.md

notes:
  - "ADR-005 替代了 ADR-003 的缓存策略"
  - "新增 Vue 3 Composition API 命名约定"
```

---

## 约束

- **只追加**：禁止删除或修改历史记忆条目
- **来源可追溯**：每个记忆条目必须标注来源（工单/变更 ID）和日期
- **可合并**：相似条目合并，避免冗余
- **定期整理**：建议每 3-5 次积累后人工审查一次，归档过时约定
- **不阻塞流程**：记忆积累失败不影响主流程（harness-archive 可继续执行）

---

## 验证清单

执行完成后自检：

- [ ] 至少一个记忆文件已更新
- [ ] 新增条目包含来源和日期
- [ ] 无重复条目（或已合并）
- [ ] 技术画像 YAML 格式有效
- [ ] `progress.md` 已更新记忆状态

---

## 返回格式

```markdown
## 项目记忆更新完成

### 新增内容

| 文件 | 新增条目数 |
|------|-----------|
| architecture-decisions.md | {{decisions_added}} |
| project-conventions.md | {{conventions_added}} |
| technology-profile.yaml | {{technology_updates}} |
| lessons-learned.md | {{lessons_added}} |

### 更新摘要

{{summary.notes}}

### 记忆文件路径

- docs/meta/memory/architecture-decisions.md
- docs/meta/memory/project-conventions.md
- docs/meta/memory/technology-profile.yaml
- docs/meta/memory/lessons-learned.md

> 提示：这些记忆文件可被后续 `harness-context` 引用，为新的工单执行提供历史上下文。
```
