# Harness Core v1.0 Release Notes

> **发布日期**：2026-06-25
> **版本**：Harness Core v1.0
> **状态**：Stable

---

## 核心能力

Harness Core v1.0 是一套纯 Markdown/YAML 的 AI 编程元框架，通过 20 个 Skill 链驱动 AI 生成整套工程管理体系。

### 三套流程

| 流程 | 适用场景 | Skill 链 |
|------|---------|---------|
| **Flow A（Greenfield）** | 从零建项目 | init → init-docs → clarify → specify → specify-arch → order → [analyze] → [context] → execute → [review-loop] → [runtime-verify] → verify → [project-memory] → archive |
| **Flow B（Brownfield）** | 已有项目改代码 | [explore] → change → apply → [review-loop] → [runtime-verify] → verify → [project-memory] → archive |
| **Flow C（Adopt）** | 已有代码接入 | adopt-scan → context-index → adopt-spec → 后续走 Flow B |

### 七层架构

1. **准备层**：init / init-docs / clarify
2. **规格层**：specify / specify-arch
3. **执行层**：order / context / execute
4. **审查层**：analyze / review-loop / runtime-verify / verify
5. **变更层**：explore / change / apply / archive
6. **记忆层**：project-memory / context-index
7. **接入层**：adopt-scan / adopt-spec

---

## Schema 体系（6 套冻结）

| Schema | 版本 | 角色 |
|--------|------|------|
| Context Contract | v1.0-frozen | 统一上下文协议 |
| Artifact Meta Schema | v1.0-frozen | 产物身份标识 + 引用完整性 |
| Spec Schema | v1.0-frozen | 业务规格（What） |
| Task Schema | v1.0-frozen | 实现工单（How） |
| Architecture Schema | v1.0-frozen | 约束结构（Constraints） |
| Verify Schema | v1.0-frozen | 链路最终消费者（V1-V6 规则 + 4 类覆盖率） |

---

## 验证体系

### Planner（规则引擎）
- 30 个测试场景，覆盖 Flow A/B/C 全链路
- 路由准确率 100%

### Runtime（状态机）
- 10 状态执行状态机（PENDING → ... → VERIFIED）
- 55 个测试场景，覆盖状态迁移 + Retry + 死循环防护
- 固定重试 + 连续 2 次相同错误终止

### E2E（端到端闭环）
- 5 个场景：Greenfield / Brownfield / Adopt / Verify-Retry / Loop-Detection
- 全部通过

---

## 工程化收尾（本次完成）

| 项目 | 内容 |
|------|------|
| **模板治理** | 8 个过程文档从 templates/meta/ 迁移到 docs/governance/ |
| **README 瘦身** | 从 412 行精简到 202 行，治理信息迁出到 GOVERNANCE.md |
| **目录职责分离** | templates/（用户面向）vs docs/governance/（维护者面向）物理隔离 |
| **引用完整性** | 全仓库零断链 |
| **结构审查** | Repository Structure Review 评分 9.5/10 |

---

## 已知限制

1. **无真实项目验证**：Core v1.0 的验证基于 F22 fixture 和模拟测试，尚未经过 2-3 个真实项目实战
2. **前端架构规格**：FRONTEND_STYLE.md 和 COMPONENT_LIBRARY.md 已具备模板，但前端流程未经深度验证
3. **Agent 体系可选**：多 Agent 模式（backend-dev / frontend-dev / code-reviewer / spec-validator）已定义但为可选增强，单会话模式为默认

---

## 下一步

Phase 6（Project Memory Engine / Multi-Agent Orchestrator / Capability Discovery）**暂不启动**，进入 Backlog。

等待：
- 真实项目验证（至少 2-3 个）
- 收集问题与反馈
- 确认 Core 稳定性

之后再评估启动。
