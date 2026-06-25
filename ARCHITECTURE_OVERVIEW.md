# Harness Core v1.0 Architecture Overview

> 面向技术评估者的架构概览。详细治理信息见 `docs/governance/GOVERNANCE.md`。

---

## 设计哲学

harness-meta 的核心设计哲学是 **"用结构约束 AI 的自由度"**——不是给 AI 更多的自由，而是用模板结构、依赖图约束、三段式执行等机制，确保 AI 产出可预测、可验证、可追溯。

| 设计原则 | 实现机制 |
|---------|---------|
| 模板结构化 | 每个产出物有固定 section，AI 填充而非自由发挥 |
| 依赖图约束 | artifact 按 DAG 顺序生成，前驱不存在则阻塞 |
| 增量变更 | 变更只表达 delta，不重写全局 spec |
| 三段式执行 | 只读 → 写码 → 自审，阶段间暂停确认，防止跳步 |
| 断点续跑 | 每个 Skill 启动时扫描磁盘文件判断状态 |
| 工单三态流转 | not_started → active → passing，单一数据源 |
| LLM 无关 | 全部纯 Markdown/YAML，任何 AI 工具可用 |

---

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户（自然语言）                        │
└────────────────────────┬────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │    Flow A      │    Flow B      │   Flow C
        │  Greenfield    │  Brownfield    │   Adopt
        └───────┬────────┴────────┬───────┴───────┬───────┘
                │                 │               │
        ┌───────▼─────────────────▼───────────────▼───────┐
        │              20 个 Skill 链                      │
        │                                                 │
        │  准备层: init → init-docs → clarify              │
        │  规格层: specify → specify-arch                  │
        │  执行层: order → context → execute               │
        │  审查层: analyze → review-loop → runtime-verify  │
        │          → verify                                │
        │  变更层: explore → change → apply → archive      │
        │  记忆层: project-memory / context-index          │
        │  接入层: adopt-scan → adopt-spec                 │
        └───────────────────┬─────────────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  6 套冻结 Schema  │
                   │                 │
                   │ Context Contract│  统一变量协议
                   │ Artifact Meta   │  身份标识 + 引用
                   │ Spec Schema     │  业务规格 (What)
                   │ Task Schema     │  实现工单 (How)
                   │ Architecture    │  约束结构
                   │ Verify Schema   │  链路消费者 (V1-V6)
                   └─────────────────┘
```

---

## 核心机制

### 1. 三段式执行（防跳步）

每个工单严格按三阶段执行，阶段间暂停等待用户确认：

| 阶段 | 目标 | 硬约束 |
|------|------|--------|
| 阶段 1（只读） | 读前序代码 + docs，输出差异清单 | **禁止写代码** |
| 阶段 2（写码） | 仅实现清单内文件 | **禁止越界修改** |
| 阶段 3（自审） | 对照 evaluator-rubric 逐项检查 | **不通过必须修复** |

### 2. Verify 闭环验证（V1-V6 规则）

```
Requirement (Spec)     → V1  需求是否被 Task 引用
Acceptance Criteria    → V2  AC 是否被 validation_step 覆盖
Constraint (Arch)      → V3  约束是否被 Task 引用
Reference              → V4  引用 ID 是否全部有效
DoD                    → V5  完成定义是否满足
Validation             → V6  验证步骤是否全部通过
```

四类覆盖率：`requirement_coverage` / `acceptance_coverage` / `constraint_coverage` / `validation_coverage`

### 3. Runtime 状态机（10 状态）

```
PENDING → BUILDING_CONTEXT → CONTEXT_READY → RUNNING → COMPLETED
                                                          ↓
                    RETRYING ←──── FAILED ←────── (重试/终止)
                        ↓
                    RUNNING → COMPLETED → VERIFYING → VERIFIED
                                                    ↘ VERIFY_FAILED
```

- 固定重试（无指数退避），连续 2 次相同错误立即终止
- 直通模式：init/clarify/specify 等无状态 Skill 跳过 Runtime

### 4. Context Engine（上下文构建）

P0 Builder / P1 Resolver / P2 Budget 三组件：

- **P1 Resolver**：自动遍历 Frozen Schema 引用链（V1/V2/V3），解析 requirement_refs → acceptance_criteria_ids → constraint_refs
- **P2 Budget**：Token 预算控制（30000 上限），按优先级裁减（P2 记忆先裁 → P1 截断 → P0 核心最后裁）
- **P0 Builder**：生成 `context_bundle.yaml` 结构化输出

---

## 技术选型理由

| 选择 | 理由 |
|------|------|
| **纯 Markdown/YAML** | LLM 无关，任何 AI 工具可直接消费；无运行时依赖 |
| **Schema 冻结 + SemVer** | 防止 Schema 漂移，保障跨项目兼容性 |
| **磁盘文件状态**（非数据库） | 支持 git 版本控制、断点续跑、跨会话恢复 |
| **结构化 ID 引用**（非自由文本） | 支持引用完整性校验和覆盖率计算 |
| **规则引擎 Planner**（非 LLM 路由） | 路由决策确定性 100%，可测试、可审计 |

---

## 目录职责

```
harness-meta/
├── README.md                 # 面向使用者：介绍 + 快速开始 + 流程
├── USAGE.md                  # 面向使用者：详细使用说明
├── RELEASE_NOTES.md          # 版本发布记录
├── ARCHITECTURE_OVERVIEW.md  # 本文件：架构概览
├── ROADMAP.md                # 路线图
├── docs/governance/          # 面向维护者：治理文档
├── schemas/                  # 变更 schema（hotfix/standard/feature）
├── skills/                   # 20 个 Skill 定义
├── templates/                # 模板文件（只含会被复制到用户项目的内容）
└── tests/                    # 测试套件（Planner + Runtime + E2E + Fixture）
```
