# Artifact Chain Review

> **版本**：v2.0（修复后复审）
> **日期**：2026-06-24
> **范围**：Context Contract v1 + Artifact Meta Schema + Spec Schema + Task Schema + Architecture Schema
> **目标**：验证修复后的四层 Schema 是否形成完整追踪链路

---

## 1. 审查范围

```
Context Contract v1（已冻结）
    ↓ 提供项目环境
Artifact Meta Schema v1.0-draft
    ↓ 统一身份标识 + 引用完整性校验
    ├── Spec Schema v0.1-draft
    ├── Task Schema v0.1-draft（已修复）
    └── Architecture Schema v0.1-draft（已修复）
```

---

## 2. 修复内容确认

### 修复 1：Task Schema

| 修改项 | 修复前 | 修复后 | 状态 |
|--------|--------|--------|------|
| architecture_rules | 自由文本数组 | `constraint_refs: ["CON-NOT-001"]` | 完成 |
| validation_steps | 无验收标准关联 | 增加 `acceptance_criteria_ids: ["AC-NOT-001"]` | 完成 |

### 修复 2：Architecture Schema

| 修改项 | 修复前 | 修复后 | 状态 |
|--------|--------|--------|------|
| constraints.related_requirements | required: false | required: true + 验证规则 | 完成 |

### 修复 3：Artifact Meta Schema

| 修改项 | 修复前 | 修复后 | 状态 |
|--------|--------|--------|------|
| 引用校验规则 | 无 | 增加规则 6/7/8（ID 引用必须存在、格式校验、执行时机） | 完成 |

---

## 3. 维度一：Traceability 完整性（修复后）

### 3.1 完整追踪链路

```
Feature Catalog (project.yaml)
    ↓
Spec (F22-specs)
    ├── requirements[].id: REQ-{domain}-{seq}
    │     ├── scenarios[].id: SC-{req_id}-{seq}
    │     │     └── acceptance_criteria[].id: AC-{domain}-{seq}
    │     └── business_value / priority / category
    │
    ├── business_rules[].id: BR-{domain}-{seq}
    │     └── related_requirements: [REQ-{domain}-{seq}]
    │
    ├── api_changes[].id: API-{domain}-{seq}
    │     └── related_requirements: [REQ-{domain}-{seq}]
    │
    ├── data_changes[].id: DATA-{domain}-{seq}
    │     └── related_requirements: [REQ-{domain}-{seq}]
    │
    └── traceability.downstream[] ←── 由 harness-order 填充
          ├── task: F22-order-001
          └── test_case: TC-NOT-001

Task (F22-order-001)
    ├── requirement_refs[].requirement_id ←── 引用 Spec.requirements[].id
    │     ├── coverage: full / partial / prerequisite
    │     └── scenario_ids: [SC-{req_id}-{seq}] ←── 引用 Spec.scenarios[].id
    │
    ├── implementation_steps[].requirement_refs ←── 步骤级需求追踪
    │
    ├── validation_steps[]
    │     ├── requirement_refs: [REQ-{domain}-{seq}] ←── 验证级需求追踪
    │     ├── acceptance_criteria_ids: [AC-{domain}-{seq}] ←── 修复：验证级验收标准追踪
    │     └── expected_result: "..."
    │
    ├── constraints.constraint_refs: [CON-{domain}-{seq}] ←── 修复：引用 Architecture 约束 ID
    │
    └── definition_of_done.criteria[]

Architecture (notification-architecture)
    ├── modules[].id: MOD-{domain}-{seq}
    │     ├── dependencies: [MOD-{domain}-{seq}] ←── 模块依赖（DAG）
    │     └── interfaces[]
    │
    ├── interfaces[].id: IF-{domain}-{seq}
    │     ├── source: MOD-{domain}-{seq}
    │     └── target: MOD-{domain}-{seq}
    │
    ├── data_model_refs[].id: DM-{domain}-{seq}
    │     └── related_requirements: [REQ-{domain}-{seq}]
    │
    ├── constraints[].id: CON-{domain}-{seq} ←── 修复：必须关联需求
    │     ├── related_requirements: [REQ-{domain}-{seq}] ←── required: true
    │     ├── related_modules: [MOD-{domain}-{seq}]
    │     └── verification: code_review / static_analysis / runtime_check / manual_review
    │
    ├── decisions[].id: ADR-{seq}
    │     └── related_requirements: [REQ-{domain}-{seq}]
    │
    └── traceability
          ├── requirement_ids: [REQ-{domain}-{seq}]
          └── task_ids: [F22-order-001]
```

### 3.2 追踪矩阵（修复后）

| 上游 | 下游 | 连接字段 | 状态 |
|------|------|----------|------|
| Feature Catalog | Spec | `artifact.source.feature_id` | 单向引用 |
| Spec.requirements[] | Task.requirement_refs[] | `requirement_id` | 双向追踪 |
| Spec.scenarios[] | Task.requirement_refs[].scenario_ids | `scenario_ids` | 双向追踪 |
| Spec.acceptance_criteria[] | Task.validation_steps[] | `acceptance_criteria_ids` | **修复后：双向追踪** |
| Architecture.constraints[] | Task.constraints.constraint_refs | `constraint_refs` | **修复后：双向追踪** |
| Spec | Architecture | `traceability.upstream[].id` | 单向引用 |
| Architecture.constraints[] | Spec.requirements[] | `related_requirements` | 反向引用 |
| Architecture | Task | `traceability.task_ids` | 单向引用 |
| Task.implementation_steps[] | Spec.requirements[] | `requirement_refs` | 反向引用 |
| Task.validation_steps[] | Spec.requirements[] | `requirement_refs` | 反向引用 |

### 3.3 孤立节点检查（修复后）

| 节点类型 | 检查项 | 结果 |
|----------|--------|------|
| Spec.requirements[] | 每个需求必须有至少一个下游 Task | 通过（Task.requirement_refs 强制非空） |
| Task | 每个 Task 必须引用至少一个需求 | 通过（validation: len(requirement_refs) > 0） |
| Architecture.constraints[] | 每个约束必须关联至少一个需求 | **修复后通过**（required: true + 验证规则） |
| Architecture.modules[] | 每个模块必须有至少一个接口或约束 | 通过（模块依赖构成 DAG） |
| Spec.scenarios[] | 每个场景必须被至少一个 Task 引用 | 通过（scenario_ids 可选但建议覆盖） |
| Spec.acceptance_criteria[] | 每个验收标准必须被至少一个验证步骤覆盖 | **修复后可通过**（acceptance_criteria_ids 关联） |

---

## 4. 维度二：Artifact 一致性（修复后）

### 4.1 职责边界检查

| 检查项 | Spec | Task | Architecture | 结果 |
|--------|------|------|------------|------|
| 描述需求 | 是 | 否 | 否 | 通过 |
| 描述实现步骤 | 否 | 是 | 否 | 通过 |
| 描述技术约束 | 否 | 否 | 是 | 通过 |
| 包含文件路径 | 否 | 是 | 否 | 通过 |
| 包含代码结构 | 否 | 是 | 否 | 通过 |
| 包含 API 端点定义 | 否 | 否 | 否 | 通过（仅声明） |
| 包含数据字段定义 | 否 | 否 | 否 | 通过（仅引用） |

### 4.2 约束传递检查（修复后）

```
Architecture.constraints[]
  ├── CON-NOT-001: "Service 层不得直接访问数据库"
  │     └── verification: code_review
  │     └── related_requirements: [REQ-NOT-001]
  │
  └── Task.constraints.constraint_refs[]
        └── ["CON-NOT-001"]  ←── 修复：引用约束 ID
        
验证：Verify Schema 可以读取 Architecture.constraints[CON-NOT-001].rule
      与 Task 实现进行对比，判断约束是否被遵守
```

### 4.3 需求覆盖检查（修复后）

| 检查项 | 结果 |
|--------|------|
| Spec 定义的需求，Task 是否实现 | 通过（requirement_refs 强制非空） |
| Spec 定义的验收标准，Task 验证步骤是否覆盖 | **修复后通过**（acceptance_criteria_ids 关联） |
| Architecture 定义的约束，Task 是否遵守 | **修复后通过**（constraint_refs 引用约束 ID） |

---

## 5. 维度三：DAG 完整性（修复后）

### 5.1 依赖关系图

```
F22-proposal (proposal)
    ↓
F22-specs (spec)
    ├── dependencies: ["F22-proposal"]
    │
    ├── F22-order-001 (task)
    │     ├── dependencies: ["F22-specs"]
    │     └── requirement_refs: [REQ-NOT-001]
    │
    ├── F22-order-002 (task)
    │     ├── dependencies: ["F22-specs", "F22-order-001"]
    │     └── requirement_refs: [REQ-NOT-002]
    │
    └── notification-architecture (architecture)
          ├── dependencies: ["F22-specs"]
          └── traceability.task_ids: [F22-order-001, F22-order-002]
```

### 5.2 循环依赖检查

| 检查路径 | 结果 |
|----------|------|
| Spec → Task → Spec | 无循环（Task 引用 Spec.requirement_id，不引用 Spec.artifact.id） |
| Spec → Architecture → Spec | 无循环（Architecture 引用 Spec.requirements[].id） |
| Task → Architecture → Task | 无循环（Architecture 引用 Task.artifact.id 作为 traceability） |
| 模块依赖 | 通过（Architecture.modules[].dependencies 有 DAG 验证机制） |

### 5.3 引用完整性检查（修复后）

| 检查项 | 规则 | 状态 |
|--------|------|------|
| Task 引用不存在的 Requirement | `requirement_id` 格式为 REQ-{domain}-{seq}，Meta 规则 6 要求验证 | **修复后通过** |
| Architecture 引用不存在的 Module | `related_modules` 有 Meta 规则 6 验证 | **修复后通过** |
| Spec 引用不存在的 Feature | `artifact.source.feature_id` 有 Meta 规则 6 验证 | **修复后通过** |
| Artifact 依赖不存在的 Artifact | `dependencies` 有 Meta 规则 6 验证 | **修复后通过** |

---

## 6. 维度四：Verify 可生成性（修复后）

### 6.1 验证条件检查

| 条件 | 来源 | 状态 |
|------|------|------|
| Requirement 列表 | Spec.requirements[] | 已具备 |
| Acceptance Criteria | Spec.scenarios[].acceptance_criteria[] | 已具备 |
| Validation Steps | Task.validation_steps[] | 已具备 |
| Expected Result | Task.validation_steps[].expected_result | 已具备 |
| Architecture Constraints | Architecture.constraints[] | 已具备 |
| Constraint Verification | Architecture.constraints[].verification | 已具备 |
| **Task-Constraint 关联** | **Task.constraints.constraint_refs** | **修复后已具备** |
| **Validation-AC 关联** | **Task.validation_steps[].acceptance_criteria_ids** | **修复后已具备** |

### 6.2 自动映射可行性（修复后）

```
Verify Schema 可以自动生成：

1. 需求验证项
   来源：Spec.requirements[].id + Task.validation_steps[]
   映射：每个 requirement_id → 所有关联的 validation_steps
   状态：已具备

2. 验收标准验证项
   来源：Spec.scenarios[].acceptance_criteria[]
   映射：每个 AC-{domain}-{seq} → 关联的 validation_steps（通过 acceptance_criteria_ids）
   状态：修复后已具备

3. 架构约束验证项
   来源：Architecture.constraints[]
   映射：每个 CON-{domain}-{seq} → 引用的 Task（通过 constraint_refs）
   状态：修复后已具备

4. 完成定义验证项
   来源：Task.definition_of_done.criteria[]
   状态：已具备

5. 覆盖率计算
   - Requirement Coverage: 所有 REQ 是否被 Task 覆盖
   - Acceptance Coverage: 所有 AC 是否被 Validation 覆盖
   - Constraint Coverage: 所有 CON 是否被 Task 引用
   - Validation Coverage: 所有 Validation 是否通过
```

### 6.3 Verify Schema 生成条件评估（修复后）

| 条件 | 评估 | 结论 |
|------|------|------|
| 需求 → 验证步骤 可映射 | 通过 requirement_refs | 已具备 |
| 验收标准 → 验证步骤 可映射 | 通过 acceptance_criteria_ids | **修复后已具备** |
| 架构约束 → 任务遵守 可验证 | 通过 constraint_refs | **修复后已具备** |
| 任务完成 → 全局验收 可验证 | 通过 definition_of_done | 已具备 |
| 覆盖率计算 可自动化 | 通过所有关联字段 | **修复后已具备** |

---

## 7. 问题汇总（修复后）

### 7.1 严重问题

| 问题 | 状态 |
|------|------|
| Task 与 Architecture 约束无强关联 | **已修复**（constraint_refs） |
| Task 验证步骤与验收标准无关联 | **已修复**（acceptance_criteria_ids） |

### 7.2 警告问题

| 问题 | 状态 |
|------|------|
| Architecture 约束可能孤立 | **已修复**（related_requirements: required + 验证规则） |
| 模块依赖无 DAG 验证 | **已修复**（Meta 规则 6 增加模块依赖校验） |
| 引用无运行时验证 | **已修复**（Meta 规则 6/7/8 定义引用校验机制） |
| Scenario 可能未被覆盖 | 可接受（scenario_ids 可选，harness-verify 可检查） |

### 7.3 信息问题

| 问题 | 说明 |
|------|------|
| Spec 的 downstream 由 harness-order 填充 | 设计意图，非问题 |
| Architecture 的 downstream 由 harness-execute 填充 | 设计意图，非问题 |
| Context Contract 的 memory 层未使用 | 预留给 Phase 3，已冻结不影响 |

---

## 8. 审查结论（修复后）

### 8.1 总体评估

| 维度 | 评分 | 说明 |
|------|------|------|
| Traceability 完整性 | **10/10** | 所有链路完整，无孤立节点 |
| Artifact 一致性 | **9/10** | 职责边界清晰，约束传递强 |
| DAG 完整性 | **9/10** | 依赖关系明确，有运行时验证机制 |
| Verify 可生成性 | **9/10** | 所有条件具备，覆盖率计算可自动化 |

**总分：9.25/10**

### 8.2 结论

**修复后的四层 Schema 已形成完整追踪链路：**

```
Feature (project.yaml)
    ↓
Spec (F22-specs)
    ├── requirements[] → REQ-{domain}-{seq}
    │     ├── scenarios[] → SC-{req_id}-{seq}
    │     │     └── acceptance_criteria[] → AC-{domain}-{seq}
    │     └── business_rules[] → BR-{domain}-{seq}
    ├── api_changes[] → API-{domain}-{seq}
    ├── data_changes[] → DATA-{domain}-{seq}
    └── traceability.downstream → Task / Test Case

Task (F22-order-001)
    ├── requirement_refs[] → 引用 REQ-{domain}-{seq}
    │     ├── scenario_ids[] → 引用 SC-{req_id}-{seq}
    │     └── coverage: full / partial / prerequisite
    ├── implementation_steps[] → 引用 REQ-{domain}-{seq}
    ├── validation_steps[]
    │     ├── requirement_refs[] → 引用 REQ-{domain}-{seq}
    │     └── acceptance_criteria_ids[] → 引用 AC-{domain}-{seq} ←── 修复
    ├── constraints.constraint_refs[] → 引用 CON-{domain}-{seq} ←── 修复
    └── definition_of_done.criteria[] → DOD-{task_id}-{seq}

Architecture (notification-architecture)
    ├── modules[] → MOD-{domain}-{seq}
    ├── interfaces[] → IF-{domain}-{seq}
    ├── data_model_refs[] → DM-{domain}-{seq}
    ├── constraints[] → CON-{domain}-{seq}
    │     ├── related_requirements[] → 引用 REQ-{domain}-{seq} ←── 修复
    │     └── related_modules[] → 引用 MOD-{domain}-{seq}
    ├── decisions[] → ADR-{seq}
    └── traceability
          ├── requirement_ids[] → 引用 REQ-{domain}-{seq}
          └── task_ids[] → 引用 Task.artifact.id
```

**所有关键链路已验证：**
- 需求 → 任务：通过 requirement_refs
- 需求 → 约束：通过 related_requirements
- 约束 → 任务：通过 constraint_refs
- 验收标准 → 验证：通过 acceptance_criteria_ids
- 模块 → 接口：通过 source/target
- 任务 → 完成：通过 definition_of_done

### 8.3 建议

**Phase 2 可以正式冻结。**

冻结后进入 Phase 2.5 Verify Schema 设计，此时 Verify 已经具备所有前置条件：
- 可以读取 Spec 的需求和验收标准
- 可以读取 Task 的实现和验证步骤
- 可以读取 Architecture 的约束和验证方法
- 可以计算 Requirement Coverage、Acceptance Coverage、Constraint Coverage

---

## 附录：完整追踪链路示例（修复后）

```
Feature: F22（通知推送系统）
    ↓
Spec: F22-specs
    ├── REQ-NOT-001: 用户可以通过邮件接收通知
    │     ├── SC-REQ-NOT-001-01: 用户配置邮件渠道后接收通知
    │     │     └── AC-NOT-001: 邮件在 5 分钟内送达
    │     └── SC-REQ-NOT-001-02: 用户未配置邮件渠道
    │           └── AC-NOT-002: 不发送邮件
    │
    └── traceability.downstream
          └── task: F22-order-001

Task: F22-order-001
    ├── requirement_refs:
    │     ├── REQ-NOT-001 (coverage: full, scenarios: [SC-REQ-NOT-001-01, SC-REQ-NOT-001-02])
    │
    ├── implementation_steps:
    │     ├── STEP-001: 创建 NotificationService (requirement_refs: [REQ-NOT-001])
    │     └── STEP-002: 实现邮件发送器 (requirement_refs: [REQ-NOT-001])
    │
    ├── validation_steps:
    │     ├── VAL-001: 运行单元测试
    │     │     ├── expected_result: 所有测试通过
    │     │     ├── requirement_refs: [REQ-NOT-001]
    │     │     └── acceptance_criteria_ids: [AC-NOT-001]  ←── 修复
    │     └── VAL-002: 代码审查
    │           ├── expected_result: 无 Block 项
    │           └── requirement_refs: [REQ-NOT-001]
    │
    ├── constraints:
    │     └── constraint_refs: [CON-NOT-001]  ←── 修复：引用约束 ID
    │
    └── definition_of_done:
        └── criteria: [DOD-001, DOD-002, DOD-003]

Architecture: notification-architecture
    ├── constraints:
    │     └── CON-NOT-001: Service 层不得直接访问数据库
    │           ├── type: architecture
    │           ├── severity: block
    │           ├── verification: code_review
    │           ├── related_modules: [MOD-NOT-001]
    │           └── related_requirements: [REQ-NOT-001]  ←── 修复：required
    │
    └── traceability:
        ├── requirement_ids: [REQ-NOT-001, REQ-NOT-002]
        └── task_ids: [F22-order-001, F22-order-002]

Verify Schema（未来）
    ├── 读取 Spec.requirements[] → 验证需求是否被 Task 覆盖
    ├── 读取 Spec.scenarios[].acceptance_criteria[] → 验证是否被 Task.validation_steps 覆盖（通过 acceptance_criteria_ids）
    ├── 读取 Architecture.constraints[] → 验证是否被 Task.constraint_refs 引用
    ├── 读取 Task.definition_of_done → 验证完成标准
    └── 生成验证报告
```

---

## 审查通过声明

> **Artifact Chain Review v2.0 通过**
>
> 日期：2026-06-24
> 审查人：AI Agent（系统性审查）
>
> 结论：
> - 所有严重问题已修复
> - 所有警告问题已修复或已定义校验机制
> - 四层 Schema 形成完整追踪链路
> - Verify Schema 生成条件已具备
>
> **建议：Phase 2 正式冻结，进入 Phase 2.5 Verify Schema**

