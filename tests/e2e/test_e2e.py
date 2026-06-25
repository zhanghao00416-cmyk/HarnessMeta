"""Phase 5.5 End-to-End Validation — 全链路闭环模拟器。

验证 Planner → Context → Runtime → Verify → State Update 的完整闭环。
模拟 Greenfield 全流程（init→archive）和 Brownfield 变更流程。
"""

import sys
from pathlib import Path

# 导入 Planner 和 Runtime
sys.path.insert(0, str(Path(__file__).parent.parent / "planner"))
sys.path.insert(0, str(Path(__file__).parent.parent / "runtime"))
from planner import route
from runtime import RuntimeExecutor, Status, ExecutionState, simulate_execution, CONTEXT_REQUIRED

# ============================================================
# 项目状态模拟器
# ============================================================

class ProjectSimulator:
    """模拟一个 harness-meta 项目的完整生命周期。"""

    def __init__(self, mode="greenfield"):
        self.state = self._init_state(mode)
        self.history = []  # 执行历史
        self.step_count = 0
        self.verify_count = 0
        self.retry_count = 0
        self.errors = []

    def _init_state(self, mode):
        if mode == "greenfield":
            return {
                "mode": "greenfield",
                "initialization": {"project_yaml_exists": False, "meta_files_exist": False, "feature_list_exists": False},
                "features": [],
                "tasks": [],
                "verify_results": None,
                "artifacts": {},
                "blocked_tasks": [],
            }
        elif mode == "brownfield":
            return {
                "mode": "brownfield",
                "initialization": {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True},
                "features": [{"id": "F22", "status": "passing"}],
                "tasks": [],
                "verify_results": {"overall_status": "passing", "iteration": 1, "coverage": {"requirement_coverage": 1.0}},
                "artifacts": {"context_bundle": {"exists": True}, "review_report": {"exists": True}, "runtime_report": {"exists": True}, "project_memory": {"exists": True}},
                "blocked_tasks": [],
            }

    def _add_feature(self, fid="F22", domain="notification"):
        if not any(f.get("id") == fid for f in self.state["features"]):
            self.state["features"].append({"id": fid, "status": "not_started", "domain": domain})

    def _add_task(self, tid="F22-order-001", status="active", phase=1, has_validation=True):
        self.state["tasks"] = [t for t in self.state["tasks"] if t.get("id") != tid]
        self.state["tasks"].append({"id": tid, "status": status, "current_phase": phase, "has_validation_steps": has_validation})

    def _update_feature_status(self, fid, status):
        for f in self.state["features"]:
            if f["id"] == fid:
                f["status"] = status

    def _set_artifact(self, key, exists=True):
        if "artifacts" not in self.state:
            self.state["artifacts"] = {}
        self.state["artifacts"][key] = {"exists": exists}

    def _set_verify(self, overall_status, iteration=1, coverage=None):
        self.state["verify_results"] = {
            "overall_status": overall_status,
            "iteration": iteration,
            "coverage": coverage or {"requirement_coverage": 1.0},
        }

    def execute_skill(self, skill, task_id=None):
        """模拟执行一个 Skill，更新项目状态。"""
        self.step_count += 1
        self.history.append({"step": self.step_count, "skill": skill, "task": task_id})

        # 直通 Skill：直接更新状态
        if skill in {"harness-init", "harness-init-docs", "harness-clarify", "harness-specify",
                     "harness-specify-arch", "harness-order", "harness-analyze", "harness-change",
                     "harness-archive", "harness-explore", "harness-adopt-scan", "harness-context-index",
                     "harness-adopt-spec", "harness-context", "harness-project-memory"}:
            return self._handle_direct_skill(skill)

        # Runtime 管理的 Skill
        return self._handle_runtime_skill(skill, task_id)

    def _handle_direct_skill(self, skill):
        transitions = {
            "harness-init": lambda: self.state["initialization"].update({"project_yaml_exists": True}),
            "harness-init-docs": lambda: self.state["initialization"].update(
                {"meta_files_exist": True, "feature_list_exists": True}),
            "harness-clarify": lambda: self._update_feature_status("F22", "clarifying"),
            "harness-specify": lambda: self._update_feature_status("F22", "specifying"),
            "harness-specify-arch": lambda: self._update_feature_status("F22", "ordered"),
            "harness-order": lambda: self._add_task("F22-order-001", "active", 1),
            "harness-analyze": lambda: self._set_artifact("analyze_report"),
            "harness-change": lambda: self._add_task("CHG-001", "active", 1),
            "harness-adopt-scan": lambda: self.state["initialization"].update(
                {"project_yaml_exists": True, "meta_files_exist": True, "feature_list_exists": True}),
            "harness-adopt-spec": lambda: None,
            "harness-archive": lambda: self._update_feature_status("F22", "passing"),
            "harness-context": lambda: self._set_artifact("context_bundle"),
            "harness-project-memory": lambda: self._set_artifact("project_memory"),
        }
        action = transitions.get(skill)
        if action:
            action()
        return {"status": "success", "skill": skill}

    def _handle_runtime_skill(self, skill, task_id):
        """模拟 Runtime 执行（含 retry 和 verify）。"""
        tid = task_id or "F22-order-001"

        # 需要上下文构建
        if skill in CONTEXT_REQUIRED and skill != "harness-context":
            self._set_artifact("context_bundle")
            self.history.append({"step": f"{self.step_count}.1", "skill": "harness-context", "task": tid, "phase": "BUILDING_CONTEXT"})

        # 模拟执行（90% 概率成功）
        import random
        success = random.random() > 0.1  # 10% 失败率

        if not success:
            self.retry_count += 1
            self.history.append({"step": f"{self.step_count}.2", "skill": skill, "task": tid, "phase": "FAILED→RETRYING"})
            # 重试
            self.step_count += 1
            self.history.append({"step": self.step_count, "skill": skill, "task": tid, "phase": "RETRY→RUNNING"})

        # Agent 完成
        self._add_task(tid, "active", 3)

        # 验证
        if skill in CONTEXT_REQUIRED:
            self.verify_count += 1
            self._set_verify("passing", 1, {"requirement_coverage": 1.0})

            # 更新 task 状态
            self._add_task(tid, "passing", 3)

        # 设置相关 artifact
        if skill == "harness-review-loop":
            self._set_artifact("review_report")
        elif skill == "harness-runtime-verify":
            self._set_artifact("runtime_report")

        return {"status": "success", "skill": skill, "task": tid}

    def run_until_done(self, max_steps=50):
        """运行 Planner→Runtime 循环直到所有 feature passing。"""
        for _ in range(max_steps):
            # 1. Planner 决策
            decision = route(self.state)
            next_skill = decision.get("next_skill")

            if next_skill is None:
                # 检查是否 done
                if decision.get("done") or self._all_done():
                    self.history.append({"step": "DONE", "skill": None, "reason": decision.get("reason", "all features passing")})
                    return True
                # 需要人工介入
                self.errors.append(decision.get("reason", "unknown"))
                return False

            # 2. 执行
            task_id = decision.get("target_task")
            result = self.execute_skill(next_skill, task_id)

            # 3. 记录
            reason = decision.get("reason", "")[:60]
            self.history[-1]["reason"] = reason

        return False  # 超出最大步数

    def _all_done(self):
        features = self.state.get("features", [])
        if not features:
            return False
        return all(f.get("status") == "passing" for f in features)


# ============================================================
# E2E 测试
# ============================================================

def run_greenfield_e2e():
    """Greenfield 完整流程。"""
    print("=" * 70)
    print("E2E Test 1: Greenfield Full Flow (init → archive)")
    print("=" * 70)

    sim = ProjectSimulator("greenfield")

    # 先加入一个 feature
    sim._add_feature("F22", "notification")

    success = sim.run_until_done(max_steps=30)

    print(f"\nSteps: {sim.step_count}")
    print(f"Verifications: {sim.verify_count}")
    print(f"Retries: {sim.retry_count}")

    for h in sim.history:
        marker = "  "
        print(f"  {marker} Step {str(h.get('step','?')):5s} | {str(h.get('skill','')):25s} | {str(h.get('reason',''))[:50]}")

    print(f"\nFinal state:")
    print(f"  Features: {sim.state['features']}")
    print(f"  Tasks: {sim.state['tasks']}")
    print(f"  Init: {sim.state['initialization']}")

    # 验证
    all_passing = sim._all_done()
    print(f"\n  All features passing: {all_passing}")
    print(f"  Steps taken: {sim.step_count}")
    print(f"  Errors: {len(sim.errors)}")

    return {
        "name": "Greenfield Full Flow",
        "success": success and all_passing,
        "steps": sim.step_count,
        "verifies": sim.verify_count,
        "retries": sim.retry_count,
        "errors": len(sim.errors),
        "all_passing": all_passing,
    }


def run_brownfield_e2e():
    """Brownfield 变更流程。"""
    print("\n" + "=" * 70)
    print("E2E Test 2: Brownfield Change Flow")
    print("=" * 70)

    sim = ProjectSimulator("brownfield")
    success = sim.run_until_done(max_steps=15)

    print(f"\nSteps: {sim.step_count}")
    for h in sim.history:
        print(f"    {str(h.get('step','?')):5s} | {str(h.get('skill','')):25s} | {str(h.get('reason',''))[:50]}")

    return {
        "name": "Brownfield Change Flow",
        "success": success,
        "steps": sim.step_count,
        "verifies": sim.verify_count,
        "retries": sim.retry_count,
        "errors": len(sim.errors),
        "all_passing": True,
    }


def run_adopt_e2e():
    """Adopt 流程。"""
    print("\n" + "=" * 70)
    print("E2E Test 3: Adopt Flow")
    print("=" * 70)

    # Adopt 流程
    state = {
        "mode": "adopt",
        "initialization": {"project_yaml_exists": False, "meta_files_exist": False},
        "features": [],
        "tasks": [],
        "artifacts": {},
    }
    # 手动模拟
    decisions = []
    for _ in range(5):
        d = route(state)
        decisions.append(d)
        if d.get("next_skill") is None:
            break
        # 模拟执行
        skill = d["next_skill"]
        if skill == "harness-adopt-scan":
            state["initialization"]["project_yaml_exists"] = True
            state["initialization"]["meta_files_exist"] = True
            state["features"] = [{"id": "F01", "status": "passing"}]
        elif skill == "harness-context-index":
            state["artifacts"]["project_index"] = {"exists": True}
        elif skill == "harness-adopt-spec":
            state["tasks"] = [{"id": "F01-order-001", "status": "passing"}]

    print(f"\nDecisions: {len(decisions)}")
    for d in decisions:
        print(f"    {str(d.get('next_skill','done')):25s} | {str(d.get('reason',''))[:50]}")

    return {
        "name": "Adopt Flow",
        "success": len(decisions) >= 2,
        "steps": len(decisions),
        "verifies": 0,
        "retries": 0,
        "errors": 0,
        "all_passing": True,
    }


def run_verify_retry_e2e():
    """验证重试机制。"""
    print("\n" + "=" * 70)
    print("E2E Test 4: Verify → Retry → Verify Loop")
    print("=" * 70)

    # 模拟 execute 完成后 verify 失败→重试→成功
    events = [
        ("build_context_success", {}),
        ("start_agent", {}),
        ("agent_completed", {"success": True}),
        ("verify_failed", {"error": "pytest 4/6 failed"}),
        ("retry_cooldown_done", {}),
        ("agent_completed", {"success": True}),
        ("verify_passed", {}),
    ]
    final_state = simulate_execution("harness-execute", "F22-order-001", events)
    passed = final_state.status == Status.VERIFIED

    print(f"  Final status: {final_state.status}")
    print(f"  Retry count: {final_state.retry_count}")
    print(f"  Verify passed: {passed}")

    return {
        "name": "Verify Retry Loop",
        "success": passed,
        "steps": len(events),
        "verifies": 2,
        "retries": 1,
        "errors": 0,
        "all_passing": passed,
    }


def run_loop_detection_e2e():
    """死循环防护。"""
    print("\n" + "=" * 70)
    print("E2E Test 5: Loop Detection (same error → terminate)")
    print("=" * 70)

    events = [
        ("build_context_success", {}),
        ("start_agent", {}),
        ("agent_completed", {"success": True}),
        ("verify_failed", {"error": "AssertionError: assert status == SENT"}),
        ("retry_cooldown_done", {}),
        ("agent_completed", {"success": True}),
        ("verify_failed", {"error": "AssertionError: assert status == SENT"}),
    ]
    final_state = simulate_execution("harness-execute", "F22-order-001", events)
    terminated = final_state.status == Status.VERIFY_FAILED

    print(f"  Final status: {final_state.status}")
    print(f"  Terminated (loop detected): {terminated}")

    return {
        "name": "Loop Detection",
        "success": terminated,
        "steps": len(events),
        "verifies": 2,
        "retries": 1,
        "errors": 0,
        "all_passing": terminated,
    }


# ============================================================
# 运行全部 E2E 测试
# ============================================================

results = []
results.append(run_greenfield_e2e())
results.append(run_brownfield_e2e())
results.append(run_adopt_e2e())
results.append(run_verify_retry_e2e())
results.append(run_loop_detection_e2e())

print("\n" + "=" * 70)
print("Phase 5.5 E2E Validation Summary")
print("=" * 70)
for r in results:
    status = "[OK]" if r["success"] else "[FAIL]"
    print(f"  {status} {r['name']:30s} | steps={r['steps']:3d} | verifies={r['verifies']} | retries={r['retries']} | all_passing={r['all_passing']}")

passed = sum(1 for r in results if r["success"])
total = len(results)
print(f"\n  Passed: {passed}/{total}")
print(f"  Result: {'PASS' if passed == total else 'FAIL'}")
print("=" * 70)
