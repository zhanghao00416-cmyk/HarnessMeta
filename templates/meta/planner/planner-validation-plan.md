# Planner Validation Plan

> **Phase**：4.1（Planner Validation）
> **依赖**：planner-state-model.md、planner-routing-rules.md
> **验证目标**：证明 Planner 在所有场景下输出正确的 next_skill
> **验证方式**：场景表驱动测试（给定 project_state → 期望 next_skill）

---

## 1. 验证策略

### 1.1 不验证什么

| 范围 | 原因 |
|------|------|
| ❌ Skill 实际执行结果 | Planner 只负责路由，不负责执行 |
| ❌ Agent 是否按 Planner 建议行动 | 不在 Planner 控制范围 |
| ❌ Skill 内部逻辑正确性 | 已在 Phase 2.5 验证 |
| ❌ 性能（响应时间） | Phase 4 不涉及性能优化 |

### 1.2 验证什么

| 验证项 | 标准 |
|--------|------|
| **确定性** | 相同 project_state 总是产生相同 next_skill |
| **覆盖性** | Flow A/B/C 的每个节点都能被 Planner 导航到 |
| **阻塞检测** | 前置条件不满足时，推荐前置 Skill 而非当前 Skill |
| **降级处理** | 状态不一致时，以 session-handoff 为准，不崩溃 |
| **边界情况** | 空项目、已完成项目、损坏状态 |

---

## 2. 测试场景

### 2.1 Flow A（Greenfield）完整链路

| # | 场景 | project_state 关键字段 | 期望 next_skill | 期望 reason |
|---|------|----------------------|----------------|------------|
| A-01 | 空项目 | `mode=greenfield, initialization.project_yaml_exists=false` | `harness-init` | 项目未初始化 |
| A-02 | init 刚完成 | `project_yaml_exists=true, meta_files_exist=false` | `harness-init-docs` | 需要生成 meta 文件 |
| A-03 | init-docs 完成 | `meta_files_exist=true, features[F22].status=not_started` | `harness-clarify` | F22 待澄清 |
| A-04 | clarify 完成 | `features[F22].status=clarifying` | `harness-specify` | F22 待生成规格 |
| A-05 | specify 完成 | `features[F22].status=specifying` | `harness-specify-arch` | F22 待生成架构规格 |
| A-06 | specify-arch 完成 | `features[F22].status=ordered` | `harness-order` | F22 待生成工单 |
| A-07 | order 完成 | `tasks[F22-order-001].status=active` | `harness-execute` | 有待执行工单 |
| A-08 | execute 完成 | `tasks[F22-order-001].status=active, phase=3` | `harness-verify` | 工单已完成阶段 3 |
| A-09 | verify 失败 | `verify_results.overall_status=failing, iteration=1` | `harness-execute` | 验证失败，需要修复后重新执行 |
| A-10 | verify 通过 | `verify_results.overall_status=passing` | `harness-archive` | 验证通过，归档 |

### 2.2 Flow A 可选 Skill 推荐

| # | 场景 | project_state 关键字段 | 期望 next_skill |
|---|------|----------------------|----------------|
| A-11 | order 完成 + 低覆盖率 | `coverage.* < 0.8` | `harness-analyze`（推荐） |
| A-12 | task=active + 无 context_bundle | `artifacts.context_bundle.exists=false` | `harness-context`（推荐） |
| A-13 | execute 完成 + 首次 | `tasks[F22-order-001].phase=3` | `harness-review-loop`（推荐） |
| A-14 | execute 完成 + 有 tests | `validation_steps 非空` | `harness-runtime-verify`（推荐） |
| A-15 | verify passing + feature 完成 | `verify.overall_status=passing` | `harness-project-memory`（推荐） |

### 2.3 Flow B（Brownfield）完整链路

| # | 场景 | project_state 关键字段 | 期望 next_skill |
|---|------|----------------------|----------------|
| B-01 | 已初始化 + 无活跃变更 | `mode=brownfield, 无 task.status=active, 无 active changes` | `harness-change` |
| B-02 | 变更已创建 | `有变更文件夹，tasks.md 存在` | `harness-apply` |
| B-03 | 变更已实现 | `apply 完成` | `harness-verify` |
| B-04 | 验证通过 | `verify.overall_status=passing` | `harness-archive` |

### 2.4 Flow C（Adopt）

| # | 场景 | project_state 关键字段 | 期望 next_skill |
|---|------|----------------------|----------------|
| C-01 | adopt 模式 + 未扫描 | `mode=adopt, 无 project.yaml` | `harness-adopt-scan` |
| C-02 | adopt-scan 完成 | `project.yaml 存在, features 全部 passing` | `harness-adopt-spec`（建议先 harness-context-index） |

### 2.5 阻塞与降级

| # | 场景 | project_state 关键字段 | 期望 next_skill |
|---|------|----------------------|----------------|
| D-01 | 依赖未完成 | `F22-order-003.blocked_by=["F22-order-001"], F22-order-001.status=active` | `harness-execute`（执行 F22-order-001） |
| D-02 | progress 与 session 不一致 | `progress 说 F22.status=specifying, session 说 last_skill=harness-clarify` | 以 session 为准：`harness-specify` |
| D-03 | 跳过必选 Skill | `harness-order 完成，但 harness-specify-arch 未运行` | `harness-specify-arch`（补充缺失步骤） |
| D-04 | Artifact 丢失 | `tasks[F22-order-001].status=active, artifacts.spec.exists=false` | `harness-specify`（重新生成丢失的 spec） |

### 2.6 边界情况

| # | 场景 | 期望行为 |
|---|------|---------|
| E-01 | 所有 feature 都 passing | `{ done: true }` 或 `harness-project-memory` |
| E-02 | 空 feature_list.json | `harness-init`（重建） |
| E-03 | progress.md 损坏（解析失败） | 输出 warn，以文件系统状态为准 |
| E-04 | 同时有 greenfield 和 brownfield 特征 | 以 mode 为准（优先 brownfield 如果 project.yaml 存在） |
| E-05 | verify 第 3 轮迭代 | 如果 still failing，推荐人工介入（不推荐无限制循环） |

---

## 3. 验证执行

### 3.1 方式

使用 Python 脚本模拟 Planner 路由引擎，对每个场景输入 project_state，比对期望输出。

```
tests/planner/
├── test_flow_a.py      # A-01 到 A-15
├── test_flow_b.py      # B-01 到 B-04
├── test_flow_c.py      # C-01 到 C-02
├── test_blocking.py     # D-01 到 D-04
├── test_edge_cases.py  # E-01 到 E-05
└── fixtures/            # 每个场景的 project_state YAML
```

### 3.2 验证脚本结构

```python
def test_planner(scenario_id, project_state, expected_next_skill, expected_reason=None):
    result = planner.route(project_state)
    assert result["next_skill"] == expected_next_skill, \
        f"{scenario_id}: expected {expected_next_skill}, got {result['next_skill']}"
    if expected_reason:
        assert expected_reason in result["reason"], \
            f"{scenario_id}: reason mismatch"
```

### 3.3 通过标准

```
所有场景（~30 个）的 next_skill 与期望一致 → ✅ 通过
任一场景不一致 → ❌ 失败（需修正路由规则或状态模型）
```

---

## 4. 回归测试

Planner 路由规则修改后，必须重新运行全部场景。

| 修改类型 | 需重新验证的场景 |
|---------|----------------|
| 新增 Skill | 全部（Skill 插入可能改变链顺序） |
| 修改前置条件 | 该 Skill 相关的阻塞场景（D 类） |
| 修改推荐规则 | 可选 Skill 场景（A-11 到 A-15） |
| 修改 Flow 链 | 该 Flow 的全部场景 |

---

## 5. 与 Phase 2.5 验证的关系

| Phase 2.5 验证了什么 | Phase 4 验证了什么 |
|---------------------|-------------------|
| Skill 内部逻辑正确 | Skill 调用顺序正确 |
| Schema 字段一致 | 前置条件判断正确 |
| 引用链完整 | 流程链完整（不跳步） |

**Phase 4 验证的是"编排"，不是"实现"**。

---

> **v1.0-draft（2026-06-25）**：初始版本。定义 30 个测试场景覆盖 Flow A/B/C、阻塞、降级、边界。
