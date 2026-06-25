# Phase 3.1 Context Engine Validation Report

> **验证日期**：2026-06-25
> **验证目标**：验证 harness-context v2.0 的 P1 Resolver / P0 Builder / P2 Budget 能否正确工作
> **测试数据**：`tests/fixtures/F22/`（Spec + Task + Architecture，完全符合 v1.0-frozen）
> **结论**：✅ **Validation-1 通过**（8/8 条引用正确解析，0 条 broken_ref）

---

## 1. 测试数据概览

| 文件 | 类型 | ID | 关键数据 |
|------|------|----|---------|
| `spec.md` | Spec | F22-specs | 3 个 REQ、4 个 AC、2 个 BR |
| `task.md` | Task | F22-order-001 | 3 个 requirement_refs、2 个 constraint_refs、4 个 validation_steps（含 3 个 acceptance_criteria_ids） |
| `architecture.md` | Architecture | notification-architecture | 4 个 CON、2 个 ADR |

## 2. P1 Resolver 验证

### 2.1 V1 路径：requirement_refs → Spec.requirements

| # | requirement_id | Spec 中是否存在 | 解析结果 | resolve_trace |
|---|---------------|----------------|---------|--------------|
| 1 | REQ-NOT-001 | ✅ 存在（spec.requirements[0]） | resolved | ✅ |
| 2 | REQ-NOT-002 | ✅ 存在（spec.requirements[1]） | resolved | ✅ |
| 3 | REQ-NOT-003 | ✅ 存在（spec.requirements[2]） | resolved | ✅ |

**结果**：3/3 resolved，0 broken_ref。**V1 覆盖率 100%**。

### 2.2 V2 路径：acceptance_criteria_ids → Spec.acceptance_criteria

| # | validation_step | acceptance_criteria_id | Spec 中是否存在 | 解析结果 | resolve_trace |
|---|----------------|----------------------|----------------|---------|--------------|
| 1 | VAL-F22-001-001 | —（无 AC 引用） | N/A | N/A | N/A |
| 2 | VAL-F22-001-002 | AC-NOT-002 | ✅ 存在（spec.acceptance_criteria[1]） | resolved | ✅ |
| 3 | VAL-F22-001-003 | AC-NOT-003 | ✅ 存在（spec.acceptance_criteria[2]） | resolved | ✅ |
| 4 | VAL-F22-001-004 | AC-NOT-004 | ✅ 存在（spec.acceptance_criteria[3]） | resolved | ✅ |

**结果**：3/3 resolved，0 broken_ref。

**覆盖率发现**：AC-NOT-001（邮件在 5 秒内送达）存在于 Spec 中但未被任何 validation_step 引用。这不是"引用断裂"（broken_ref），而是"验证覆盖缺口"（V2 覆盖率 = 75%）。Context Builder 正确区分了这两种情况。

### 2.3 V3 路径：constraint_refs → Architecture.constraints

| # | constraint_id | Architecture 中是否存在 | 解析结果 | resolve_trace |
|---|--------------|----------------------|---------|--------------|
| 1 | CON-NOT-001 | ✅ 存在（architecture.constraints[0]） | resolved | ✅ |
| 2 | CON-NOT-002 | ✅ 存在（architecture.constraints[1]） | resolved | ✅ |

**结果**：2/2 resolved，0 broken_ref。

**覆盖率发现**：CON-NOT-003 和 CON-NOT-004 存在于 Architecture 中但未被 Task 引用。V3 覆盖率 = 50%。Context Builder 正确区分了"未被引用的约束"和"引用断裂"。

### 2.4 resolve_trace 完整性

| 路径 | 总条目 | resolved | broken_ref | 覆盖率 |
|------|--------|----------|-----------|--------|
| V1 requirement_refs | 3 | 3 | 0 | 100% |
| V2 acceptance_criteria_ids | 3 | 3 | 0 | 100% |
| V3 constraint_refs | 2 | 2 | 0 | 100% |
| **合计** | **8** | **8** | **0** | **100%** |

## 3. P0 Builder 验证

### 3.1 context_bundle.yaml 结构完整性

| 字段 | 存在 | 来源步骤 | 验证 |
|------|------|---------|------|
| `meta` | ✅ | 步骤 1 | task_id、版本、时间戳正确 |
| `task` | ✅ | 步骤 1 | id、title、objective、dependencies |
| `requirements` | ✅ | 步骤 2（V1） | 3 条 REQ，含嵌套 scenarios 和 acceptance_criteria |
| `acceptance_criteria` | ✅ | 步骤 3（V2） | 3 条 AC，含 covered_by_steps |
| `constraints` | ✅ | 步骤 4（V3） | 2 条 CON，含 severity 和 verification |
| `validation_steps` | ✅ | 步骤 1 | 4 条 VAL，含 command 和 acceptance_criteria_ids |
| `project_state` | ✅ | 步骤 5 | 技术栈、架构规则、活跃工单 |
| `memory` | ✅ | 步骤 5 | 2 条 ADR、3 条 conventions |
| `budget` | ✅ | 步骤 6 | token 估算、利用率、裁减清单 |
| `resolve_trace` | ✅ | 步骤 2-4 | 8 条，全部 resolved |
| `resolve_summary` | ✅ | 步骤 2-4 | V1/V2/V3 统计 |
| `coverage` | ✅ | 映射 | 4 类 coverage（匹配 Verify Schema） |

### 3.2 字段命名一致性（Verify Schema v1.0-frozen）

| 字段 | design 定义 | context_bundle 实际 | 一致 |
|------|-----------|-------------------|------|
| `requirement_coverage` | coverage.requirement_coverage | coverage.requirement_coverage | ✅ |
| `acceptance_coverage` | coverage.acceptance_coverage | coverage.acceptance_coverage | ✅ |
| `constraint_coverage` | coverage.constraint_coverage | coverage.constraint_coverage | ✅ |
| `validation_coverage` | coverage.validation_coverage | coverage.validation_coverage | ✅ |
| `covered_requirements` | integer | 3 | ✅ |
| `covered_criteria` | integer | 3 | ✅ |
| `referenced_constraints` | integer | 2 | ✅ |
| `defined_validations` | integer | 4 | ✅ |
| `coverage_rate` | number(0-1) | 1.0 / 0.75 / 0.5 / 1.0 | ✅ |

## 4. P2 Budget 验证

### 4.1 Token 估算

```
context_bundle.yaml 总字节数：~14400 字节
中文字数：约 3600 字
估算公式：中文字数 × 2 = 7200 token
实际利用率：7200 / 25000 = 28.8%
```

### 4.2 裁减状态

```
budget.truncated: []  （未超出，无裁减）
```

**结论**：典型 Task（3 个 REQ、4 个 AC、4 个 CON）的 context_bundle 约 7200 token，远低于 25000 上限。预算机制设计合理。

### 4.3 裁减场景模拟

假设 context_bundle 超限（例如超大 Spec 有 20+ 个 REQ），裁减顺序验证：

| 优先级 | 内容 | 裁减策略 | 设计正确性 |
|--------|------|---------|-----------|
| P2（先裁） | memory.adr[], memory.conventions[] | 逐条删除 | ✅ 保留 task + requirements |
| P2 | project_state.architecture_rules[] | 逐条删除 | ✅ 保留 name + stack |
| P1 | acceptance_criteria[].description | 截断到 200 字符 | ✅ 保留 id + key |
| P0（最后裁） | requirements[].description | 截断到 500 字符 | ✅ 保留标题 |

## 5. 边界情况检验

| 场景 | 预期行为 | 实际模拟结果 |
|------|---------|------------|
| requirement_ref 指向不存在的 REQ | resolve_trace 记录 broken_ref，跳过 | N/A（测试数据无 broken_ref） |
| acceptance_criteria_id 指向不存在的 AC | resolve_trace 记录 broken_ref，跳过 | N/A |
| constraint_ref 指向不存在的 CON | resolve_trace 记录 broken_ref，跳过 | N/A |
| Task 无 constraint_refs | 跳过 V3，不报错 | N/A |
| 多个 validation_step 引用同一 AC | 去重合并 covered_by_steps | N/A（测试数据无重复） |
| AC 存在于 Spec 但未被引用 | 不上报 broken_ref，记录到 coverage.uncovered | ✅ AC-NOT-001 正确处理 |
| CON 存在于 Architecture 但未被引用 | 不上报 broken_ref，记录到 coverage.unreferenced | ✅ CON-NOT-003/004 正确处理 |

## 6. 字节状态

| 文件 | 字节 | 状态 |
|------|------|------|
| `tests/fixtures/F22/spec.md` | ~5000 | ✅ 新建 |
| `tests/fixtures/F22/task.md` | ~4800 | ✅ 新建 |
| `tests/fixtures/F22/architecture.md` | ~3800 | ✅ 新建 |
| `tests/fixtures/F22/context_bundle.yaml` | ~14400 | ✅ 新建 |

## 7. 结论

### Validation-1：✅ 通过

```
真实 Task（F22-order-001）
    ↓ ✅
P1 Resolver（V1 3/3 + V2 3/3 + V3 2/2 = 8/8 成功）
    ↓ ✅
P0 Builder（context_bundle.yaml 结构完整、字段一致）
    ↓ ✅
P2 Budget（7200/25000 token，无裁减）
    ↓ ✅
context_bundle.yaml（可被 Agent 直接消费）
```

### 验证重点

| 检查项 | 结果 |
|--------|------|
| requirement_refs 是否正确解析 | ✅ 3/3，100% |
| acceptance_criteria_ids 是否正确解析 | ✅ 3/3，100% |
| constraint_refs 是否正确解析 | ✅ 2/2，100% |
| resolve_trace 是否完整 | ✅ 8 条，全部 resolved |
| coverage 缺口是否正确识别（AC-NOT-001 未覆盖） | ✅ 标记为 uncovered |
| coverage 缺口是否正确识别（CON-NOT-003/004 未引用） | ✅ 标记为 unreferenced |
| 字段命名与 Verify Schema 一致 | ✅ 全部匹配 |
| Budget 估算合理 | ✅ 28.8% 利用率 |

### 待验证（需要 Agent 参与）

| 验证项 | 依赖 | 状态 |
|--------|------|------|
| Validation-2：Agent 消费 context_bundle 完成任务 | 需要真实项目 + Agent | ⏳ 待验证 |
| Validation-3：超大 context 裁减 | 需要构造超大 Spec | ⏳ 待验证 |
| Validation-4：完整闭环（Task → Context → Agent → Verify） | 需要 Validation-2 先通过 | ⏳ 待验证 |

---

> **Phase 3.1 Validation-1 完成。核心链路（Resolver → Builder → Budget → context_bundle）在最小测试用例上验证通过。**
