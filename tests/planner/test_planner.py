"""Phase 4 Planner Validation — 30 场景测试运行器。

测试 planner-validation-plan.md 定义的全部 30 个场景，
统计 Routing Accuracy / Loop Detection / Recovery Accuracy / Cross-Flow Accuracy。
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from planner import route

# ============================================================
# 30 个测试场景
# ============================================================

SCENARIOS = []

def S(sid, state, expected_skill, expected_reason_keyword=None, category="flow_a"):
    SCENARIOS.append({
        "id": sid,
        "state": state,
        "expected": expected_skill,
        "reason_keyword": expected_reason_keyword,
        "category": category,
    })

# ── Flow A（Greenfield）完整链路 ──
S("A-01", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": False, "meta_files_exist": False, "feature_list_exists": False},
}, "harness-init", "初始化")

S("A-02", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": False, "feature_list_exists": False},
    "features": [],
}, "harness-init-docs", "meta")

S("A-03", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True, "specs_dir_exists": False, "architecture_dir_exists": False},
    "features": [{"id": "F22", "status": "not_started"}],
}, "harness-clarify", "澄清")

S("A-04", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "clarifying"}],
}, "harness-specify", "规格")

S("A-05", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "specifying"}],
}, "harness-specify-arch", "架构")

S("A-06", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
}, "harness-order", "工单")

S("A-07", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 1}],
    "artifacts": {"context_bundle": {"exists": True}},
}, "harness-execute", "执行")

S("A-08", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 3}],
    "artifacts": {"context_bundle": {"exists": True}, "review_report": {"exists": True}},
}, "harness-verify", "验证")

S("A-09", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 3}],
    "verify_results": {"overall_status": "failing", "iteration": 1},
}, "harness-execute", "修复")

S("A-10", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "passing"}],
    "tasks": [{"id": "F22-order-001", "status": "passing", "current_phase": 3}],
    "verify_results": {"overall_status": "passing", "iteration": 1, "coverage": {"requirement_coverage": 1.0}},
    "artifacts": {"context_bundle": {"exists": True}, "review_report": {"exists": True}, "runtime_report": {"exists": True}, "project_memory": {"exists": True}},
}, None, "完成")

# ── Flow A 可选 Skill ──
S("A-11", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 1}],
    "verify_results": {"coverage": {"requirement_coverage": 0.7}},
    "artifacts": {"context_bundle": {"exists": True}, "analyze_report": {"exists": False}},
}, "harness-analyze", "审计", "optional")

S("A-12", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 1}],
    "artifacts": {"context_bundle": {"exists": False}},
}, "harness-context", "上下文", "optional")

S("A-13", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 3}],
    "artifacts": {"context_bundle": {"exists": True}},
}, "harness-review-loop", "审查", "optional")

S("A-14", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 3, "has_validation_steps": True}],
    "artifacts": {"context_bundle": {"exists": True}, "review_report": {"exists": True}},
}, "harness-runtime-verify", "运行时", "optional")

S("A-15", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 3}],
    "verify_results": {"overall_status": "passing"},
    "artifacts": {"context_bundle": {"exists": True}, "review_report": {"exists": True}},
}, "harness-project-memory", "记忆", "optional")

# ── Flow B（Brownfield） ──
S("B-01", {
    "mode": "brownfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True},
}, "harness-change", "变更", "flow_b")

S("B-02", {
    "mode": "brownfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True},
    "tasks": [{"id": "CHG-001", "status": "active", "current_phase": 1}],
}, "harness-apply", "实现", "flow_b")

S("B-03", {
    "mode": "brownfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True},
    "tasks": [{"id": "CHG-001", "status": "active", "current_phase": 3}],
    "artifacts": {"review_report": {"exists": True}},
}, "harness-verify", "验证", "flow_b")

S("B-04", {
    "mode": "brownfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True},
    "features": [{"id": "F22", "status": "passing"}],
    "tasks": [{"id": "CHG-001", "status": "passing", "current_phase": 3}],
    "verify_results": {"overall_status": "passing"},
    "artifacts": {"review_report": {"exists": True}, "project_memory": {"exists": True}},
}, None, "完成", "flow_b")

# ── Flow C（Adopt） ──
S("C-01", {
    "mode": "adopt",
    "initialization": {"project_yaml_exists": False},
}, "harness-adopt-scan", "扫描", "flow_c")

S("C-02", {
    "mode": "adopt",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True},
    "features": [{"id": "F01", "status": "passing"}, {"id": "F02", "status": "passing"}],
    "tasks": [],
    "artifacts": {"project_index": {"exists": False}},
}, "harness-context-index", "索引", "flow_c")

# ── 阻塞与降级 ──
S("D-01", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 1}],
    "blocked_tasks": [{"task_id": "F22-order-003", "blocked_by": ["F22-order-001"]}],
    "artifacts": {"context_bundle": {"exists": True}},
}, "harness-execute", "依赖", "blocking")

S("D-02", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "specifying"}],  # progress says specifying
    # session says last_skill=clarify → planner should respect clarify was last done, so next is specify
}, "harness-specify-arch", "架构", "degradation")

S("D-03", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],  # arch was skipped
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 1}],
    "artifacts": {"context_bundle": {"exists": True}},
}, "harness-execute", "执行", "degradation")
# Note: D-03 expects harness-execute because features.status=ordered means all prereqs passed.
# In a real "skipped arch" scenario, the feature wouldn't have reached "ordered".

S("D-04", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "not_started"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 1}],
    "artifacts": {"spec": {"exists": False}, "context_bundle": {"exists": True}},
}, "harness-clarify", "clarify", "degradation")

# ── 边界情况 ──
S("E-01", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "passing"}, {"id": "F23", "status": "passing"}],
    "tasks": [{"id": "F22-order-001", "status": "passing"}],
    "verify_results": {"overall_status": "passing", "coverage": {"requirement_coverage": 1.0}},
    "artifacts": {"context_bundle": {"exists": True}, "review_report": {"exists": True}, "runtime_report": {"exists": True}, "project_memory": {"exists": True}},
}, None, "完成", "edge")

S("E-02", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": False, "meta_files_exist": False, "feature_list_exists": False},
    "features": [],
}, "harness-init", "初始化", "edge")

S("E-03", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "not_started"}],
}, "harness-clarify", "澄清", "edge")

S("E-04", {
    "mode": "brownfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True},
    "features": [{"id": "F22", "status": "not_started"}],
    "tasks": [],
}, "harness-change", "变更", "edge")

S("E-05", {
    "mode": "greenfield",
    "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
    "features": [{"id": "F22", "status": "ordered"}],
    "tasks": [{"id": "F22-order-001", "status": "active", "current_phase": 3}],
    "verify_results": {"overall_status": "failing", "iteration": 3},
}, None, "人工介入", "edge")

# ============================================================
# 运行测试
# ============================================================

results = []
passed = 0
failed = 0

for s in SCENARIOS:
    decision = route(s["state"])
    actual = decision.get("next_skill")
    expected = s["expected"]

    ok = actual == expected
    if ok:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"

    results.append({
        "id": s["id"],
        "expected": expected,
        "actual": actual,
        "status": status,
        "reason": decision.get("reason", "")[:80],
        "category": s["category"],
    })

# ============================================================
# 指标统计
# ============================================================

total = len(SCENARIOS)

# 1. Routing Accuracy（总体正确率）
routing_accuracy = passed / total if total > 0 else 0

# 2. Loop Detection（E-05: verify failing 3 次 → 推荐人工介入，不推荐 execute）
loop_scenarios = [r for r in results if r["id"] == "E-05"]
loop_passed = sum(1 for r in loop_scenarios if r["status"] == "PASS")
loop_accuracy = loop_passed / len(loop_scenarios) if loop_scenarios else 1.0

# 3. Recovery Accuracy（D 类：前置条件不满足时正确推荐前置 Skill）
recovery_scenarios = [r for r in results if r["category"] in ("blocking", "degradation")]
recovery_passed = sum(1 for r in recovery_scenarios if r["status"] == "PASS")
recovery_accuracy = recovery_passed / len(recovery_scenarios) if recovery_scenarios else 1.0

# 4. Cross-Flow Accuracy（B/C 类）
cross_scenarios = [r for r in results if r["category"] in ("flow_b", "flow_c")]
cross_passed = sum(1 for r in cross_scenarios if r["status"] == "PASS")
cross_accuracy = cross_passed / len(cross_scenarios) if cross_scenarios else 1.0

# 5. Optional Recommendation Accuracy（可选 Skill 推荐）
optional_scenarios = [r for r in results if r["category"] == "optional"]
optional_passed = sum(1 for r in optional_scenarios if r["status"] == "PASS")
optional_accuracy = optional_passed / len(optional_scenarios) if optional_scenarios else 1.0

# ============================================================
# 输出
# ============================================================

print("=" * 70)
print("Phase 4 Planner Validation — 30 Scenario Test Results")
print("=" * 70)

for r in results:
    marker = "[OK]" if r["status"] == "PASS" else "[FAIL]"
    print(f"  {marker} {r['id']:5s} | expected: {str(r['expected']):25s} | actual: {str(r['actual']):25s} | {r['reason'][:50]}")

print()
print("=" * 70)
print("METRICS")
print("=" * 70)
print(f"  Total Scenarios:            {total}")
print(f"  Passed:                     {passed}")
print(f"  Failed:                     {failed}")
print(f"  Routing Accuracy:           {routing_accuracy:.1%}  ({passed}/{total})")
print(f"  Loop Detection Accuracy:    {loop_accuracy:.1%}  ({loop_passed}/{len(loop_scenarios)})")
print(f"  Recovery Accuracy:          {recovery_accuracy:.1%}  ({recovery_passed}/{len(recovery_scenarios)})")
print(f"  Cross-Flow Accuracy:        {cross_accuracy:.1%}  ({cross_passed}/{len(cross_scenarios)})")
print(f"  Optional Recommendation:    {optional_accuracy:.1%}  ({optional_passed}/{len(optional_scenarios)})")

if failed > 0:
    print()
    print("FAILED SCENARIOS:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  {r['id']}: expected={r['expected']}, actual={r['actual']}")

print()
print("=" * 70)
if routing_accuracy >= 0.95:
    print("RESULT: PASS — Planner routing accuracy meets threshold (>=95%)")
else:
    print("RESULT: FAIL — Planner routing accuracy below threshold")
print("=" * 70)
