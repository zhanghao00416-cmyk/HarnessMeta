# Harness-Meta Roadmap

> **当前版本**：Harness Core v1.0（2026-06-25）
> **当前阶段**：实战验证期——不新增功能，收集真实项目反馈

---

## 已完成（Harness Core v1.0）

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 1 | Context Contract 协议层 | ✅ v1.0-frozen |
| Phase 2 | 四层 Artifact Schema（Meta/Spec/Task/Architecture） | ✅ v1.0-frozen |
| Phase 2.5 | Verify Schema + 四消费者接入 | ✅ v1.0-frozen |
| Phase 3 | Context Engine（P0/P1/P2 三组件 + AB Test） | ✅ 完成 |
| Phase 4 | Rule-Based Planner（30 场景验证） | ✅ 完成 |
| Phase 5 | Runtime Execution Layer（55 场景验证） | ✅ 完成 |
| Phase 5.5 | E2E 全链路验证（5 场景） | ✅ 完成 |
| 工程化收尾 | 模板治理 + README 瘦身 + 结构审查 | ✅ 完成 |

---

## 当前阶段：实战验证期（无新功能）

**目标**：在 2-3 个真实项目中验证 Core v1.0，收集问题与反馈。

**不做的事**：
- 不新增 Skill
- 不新增 Schema
- 不启动 Phase 6

**做的事**：
- 用真实项目跑完 Flow A（Greenfield）和 Flow B（Brownfield）
- 记录 LLM 实际执行中的偏差（格式不遵守、跳步、遗漏）
- 收集模板使用中的痛点（填充困难、歧义、过度复杂）
- 验证前端流程（FRONTEND_STYLE + COMPONENT_LIBRARY）

**退出条件**（满足后才评估 Phase 6）：
- [ ] 至少 2 个真实项目完成 Flow A 全流程
- [ ] 至少 1 个真实项目完成 Flow B 全流程
- [ ] 收集并修复 P0/P1 级别的问题
- [ ] Core 稳定性得到验证（无 Schema 违规、无状态机死锁）

---

## Backlog（Phase 6 候选，暂不启动）

以下能力已进入 Backlog，待实战验证期结束后评估启动优先级。

### 候选 1：Project Memory Engine

- **目标**：从手动提取（harness-project-memory）升级为自动记忆引擎
- **依赖**：Core v1.0 实战反馈
- **预估**：需要至少 3 个项目的记忆积累数据才能设计

### 候选 2：Multi-Agent Orchestrator

- **目标**：从可选的 Agent 模式升级为原生多 Agent 编排
- **依赖**：真实项目中 Agent 调用频率和效果数据
- **风险**：增加框架复杂度，可能违背"LLM 无关"原则

### 候选 3：Capability Discovery

- **目标**：自动发现项目已有能力，辅助 harness-adopt-scan
- **依赖**：Context Engine v2.0 稳定性验证
- **预估**：Phase 3 已有初步设计（见 `docs/governance/phase3-context-engine.md`）

---

## 版本规划

| 版本 | 触发条件 | 内容 |
|------|---------|------|
| **v1.0.x（PATCH）** | 实战中发现的小修复 | 模板微调、Skill 文案优化、示例更新 |
| **v1.1.0（MINOR）** | 实战反馈积累到一定量 | 新增可选字段、优化流程（不破坏兼容性） |
| **v2.0.0（MAJOR）** | 实战验证充分后启动 Phase 6 | 可能涉及 Schema MAJOR 变更（走 RFC 流程） |

---

## 决策原则

1. **补缺优于优化**：实战中发现的缺失能力，优先于已有能力的优化
2. **稳定性优于功能**：宁可少一个功能，也不引入不稳定因素
3. **简单优于复杂**：每个新增能力必须通过"技能引入否决标准"评审
4. **实战优于理论**：所有设计决策基于真实项目数据，而非假设
