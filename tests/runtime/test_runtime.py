"""Phase 5.1 Runtime Validation — 47 Test Cases."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from runtime import (
    RuntimeExecutor, simulate_execution, Status,
    CONTEXT_REQUIRED, ExecutionState,
)

results = []
PASS = 0
FAIL = 0

def T(case_id, actual, expected, description, category="migration"):
    global PASS, FAIL
    ok = actual == expected
    if ok:
        PASS += 1
        status = "PASS"
    else:
        FAIL += 1
        status = "FAIL"
    results.append({
        "id": case_id, "expected": str(expected), "actual": str(actual),
        "status": status, "desc": description, "category": category,
    })


# ============================================================
# State Migration Tests (M-01 ~ M-20)
# ============================================================

T("M-01", RuntimeExecutor().start("harness-execute", "F22-order-001").status, Status.BUILDING_CONTEXT, "context-required Skill")
T("M-02", RuntimeExecutor().start("harness-specify", "F22").status, Status.VERIFIED, "direct Skill finishes immediately")

e3 = RuntimeExecutor()
e3.start("harness-execute", "F22-order-001")
T("M-03", e3.build_context_success().status, Status.CONTEXT_READY, "context build success")

e4 = RuntimeExecutor()
e4.start("harness-execute", "F22-order-001"); e4.build_context_success()
T("M-04", e4.start_agent().status, Status.RUNNING, "agent starts")
T("M-05", e4.agent_completed(success=True).status, Status.VERIFYING, "agent completed -> verifying")
T("M-08", e4.verify_passed().status, Status.VERIFIED, "verify passed -> VERIFIED")

e6 = RuntimeExecutor()
e6.start("harness-execute", "F22-order-001"); e6.build_context_success(); e6.start_agent()
T("M-06", e6.agent_completed(success=True).status, Status.VERIFYING, "completed with validation_steps -> VERIFYING")
T("M-07", RuntimeExecutor().start("harness-specify", "F22").status, Status.VERIFIED, "direct Skill no validation -> VERIFIED")

e9 = RuntimeExecutor()
e9.start("harness-execute", "F22-order-001"); e9.build_context_success(); e9.start_agent()
e9.agent_completed(success=True)
T("M-09", e9.verify_failed("test failure").status, Status.RETRYING, "verify failed -> RETRYING")

e10 = RuntimeExecutor()
e10.start("harness-execute", "F22-order-001")
T("M-10", e10.build_context_failed("context build failed").status, Status.RETRYING, "context build failed -> retry")

e11 = RuntimeExecutor()
e11.start("harness-execute", "F22-order-001"); e11.build_context_success(); e11.start_agent()
T("M-11", e11.agent_completed(success=False, error="timeout").status, Status.RETRYING, "agent timeout -> RETRYING")
T("M-12", e11.state.status, Status.RETRYING, "retryable failure -> RETRYING")
T("M-13", e11.retry_cooldown_done().status, Status.RUNNING, "cooldown done -> RUNNING")

e14 = RuntimeExecutor()
e14.start("harness-execute", "F22-order-001"); e14.build_context_success(); e14.start_agent()
T("M-14", e14.agent_completed(success=False, error="PermissionError: permission denied").status, Status.FAILED, "permission error -> FAILED terminal")

e15 = RuntimeExecutor()
e15.start("harness-execute", "F22-order-001"); e15.build_context_success(); e15.start_agent()
for i in range(4):
    e15.agent_completed(success=False, error=f"test fail {i}")
    if e15.state.status == Status.RETRYING:
        e15.retry_cooldown_done()
T("M-15", e15.state.status, Status.FAILED, "retries exhausted -> FAILED terminal")

e16 = RuntimeExecutor()
e16.start("harness-execute", "F22-order-001"); e16.build_context_success(); e16.start_agent()
e16.agent_completed(success=True)
T("M-16", e16.verify_failed("test fail").status, Status.RETRYING, "verify fail retry_count=0 -> RETRYING")

e17 = RuntimeExecutor()
e17.start("harness-runtime-verify", "F22-order-001"); e17.build_context_success(); e17.start_agent()
e17.agent_completed(success=True)
for i in range(3):
    e17.verify_failed(f"verify error {i}")
    if e17.state.status == Status.RETRYING:
        e17.retry_cooldown_done(); e17.agent_completed(success=True)
T("M-17", e17.state.status, Status.VERIFY_FAILED, "verify retries exhausted -> terminal")

# Illegal transitions (M-18 ~ M-20)
try:
    eb = RuntimeExecutor(); eb.start("harness-execute", "F22-order-001")
    eb.start_agent(); T("M-18", "no_error", "ValueError", "skip context")
except ValueError:
    T("M-18", "ValueError", "ValueError", "skip context rejected")

try:
    eb2 = RuntimeExecutor(); eb2.start("harness-execute", "F22-order-001")
    eb2.build_context_success(); eb2.start_agent()
    eb2.verify_passed(); T("M-19", "no_error", "ValueError", "verify before complete")
except ValueError:
    T("M-19", "ValueError", "ValueError", "verify before complete rejected")

try:
    eb3 = RuntimeExecutor(); eb3.start("harness-execute", "F22-order-001")
    eb3.build_context_success(); eb3.start_agent()
    eb3.agent_completed(success=True); eb3.verify_passed()
    eb3.retry_cooldown_done(); T("M-20", "no_error", "ValueError", "retry after verified")
except ValueError:
    T("M-20", "ValueError", "ValueError", "retry after verified rejected")


# ============================================================
# Retry Policy Tests (R-01 ~ R-13)
# ============================================================

def make_exec(skill="harness-execute"):
    e = RuntimeExecutor(); e.start(skill, "TASK-001")
    if e.state.status == Status.BUILDING_CONTEXT: e.build_context_success()
    e.start_agent(); return e

# R-01 context build fail
r01 = RuntimeExecutor(); r01.start("harness-execute", "TASK-001")
T("R-01", r01.build_context_failed("context build failed").status, Status.RETRYING, "context build fail -> retry")

# R-02 timeout
r02 = make_exec(); r02.agent_completed(success=False, error="timeout")
T("R-02", r02.status, Status.RETRYING, "timeout -> retry")

# R-03 test fail
r03 = make_exec(); r03.agent_completed(success=True)
T("R-03", r03.verify_failed("test fail").status, Status.RETRYING, "test fail -> retry")

# R-04 lint error
r04 = make_exec("harness-apply"); r04.agent_completed(success=False, error="lint error")
T("R-04", r04.status, Status.RETRYING, "lint error -> retry")

# R-05 verify fail
r05 = make_exec("harness-runtime-verify"); r05.agent_completed(success=True)
T("R-05", r05.verify_failed("verify fail").status, Status.RETRYING, "verify fail -> retry")

# R-06 ~ R-10 non-retryable
for rid, err in [("R-06", "Schema violation"), ("R-07", "FileNotFoundError: dep missing"),
                  ("R-08", "PermissionError"), ("R-09", "config error"), ("R-10", "cancelled")]:
    e = make_exec(); e.agent_completed(success=False, error=err)
    T(rid, e.status, Status.FAILED, f"non-retryable -> FAILED terminal")

# R-11 different errors
r11 = make_exec(); r11.agent_completed(success=True)
r11.verify_failed("test_send failed"); r11.retry_cooldown_done()
r11.agent_completed(success=True); r11.verify_failed("test_retry failed")
T("R-11", r11.status, Status.RETRYING, "different errors -> retry allowed")

# R-12 same error
r12 = make_exec(); r12.agent_completed(success=True)
r12.verify_failed("assert status == NotificationStatus.SENT"); r12.retry_cooldown_done()
r12.agent_completed(success=True); r12.verify_failed("assert status == NotificationStatus.SENT")
T("R-12", r12.status, Status.VERIFY_FAILED, "same error 2x -> terminated")

# R-13 similar but different first 100 chars
r13 = make_exec(); r13.agent_completed(success=True)
r13.verify_failed("line 42: assert"); r13.retry_cooldown_done()
r13.agent_completed(success=True); r13.verify_failed("line 42: assert status")
T("R-13", r13.status, Status.RETRYING, "similar but diff first 100 chars -> retry")


# ============================================================
# Skill Config Tests (S-01 ~ S-06)
# ============================================================

configs = {
    "S-01": ("harness-execute", 3, 0, True),
    "S-02": ("harness-apply", 3, 0, True),
    "S-03": ("harness-review-loop", 2, 0, True),
    "S-04": ("harness-runtime-verify", 2, 5, True),
    "S-05": ("harness-context", 1, 0, False),
    "S-06": ("harness-init", 0, 0, False),
}
for sid, (sk, exp_r, exp_c, ctx) in configs.items():
    es = ExecutionState("T", sk)
    T(f"{sid}-r", es.max_retries, exp_r, f"{sk} max_retries", "skill")
    T(f"{sid}-c", es.cooldown, exp_c, f"{sk} cooldown", "skill")
    if sid != "S-05":
        T(f"{sid}-x", sk in CONTEXT_REQUIRED, ctx, f"{sk} needs context?", "skill")


# ============================================================
# Scenario Tests (SC-01 ~ SC-05)
# ============================================================

T("SC-01", simulate_execution("harness-execute", "TASK", [
    ("build_context_success", {}), ("start_agent", {}),
    ("agent_completed", {"success": True}), ("verify_passed", {}),
]).status, Status.VERIFIED, "normal flow -> VERIFIED", "scenario")

T("SC-02", simulate_execution("harness-execute", "TASK", [
    ("build_context_success", {}), ("start_agent", {}),
    ("agent_completed", {"success": True}),
    ("verify_failed", {"error": "pytest 4/6 failed"}),
    ("retry_cooldown_done", {}),
    ("agent_completed", {"success": True}),
    ("verify_passed", {}),
]).status, Status.VERIFIED, "test fail -> retry -> success", "scenario")

T("SC-03", simulate_execution("harness-execute", "TASK", [
    ("build_context_success", {}), ("start_agent", {}),
    ("agent_failed", {"error": "PermissionError"}),
]).status, Status.FAILED, "permission error -> FAILED", "scenario")

T("SC-04", simulate_execution("harness-execute", "TASK", [
    ("build_context_success", {}), ("start_agent", {}),
    ("agent_completed", {"success": True}),
    ("verify_failed", {"error": "AssertionError: assert status == NotificationStatus.SENT"}),
    ("retry_cooldown_done", {}),
    ("agent_completed", {"success": True}),
    ("verify_failed", {"error": "AssertionError: assert status == NotificationStatus.SENT"}),
]).status, Status.VERIFY_FAILED, "same error loop -> terminated", "scenario")

T("SC-05", simulate_execution("harness-specify", "F22", []).status, Status.VERIFIED, "direct mode -> VERIFIED", "scenario")


# ============================================================
# Metrics
# ============================================================

total = len(results)
p = sum(1 for r in results if r["status"] == "PASS")
f = sum(1 for r in results if r["status"] == "FAIL")

cats = {}
for r in results:
    c = r["category"]
    if c not in cats: cats[c] = [0, 0]
    cats[c][0] += 1
    if r["status"] == "PASS": cats[c][1] += 1

print("=" * 70)
print("Phase 5.1 Runtime Validation Results")
print("=" * 70)
for r in results:
    m = "[OK]" if r["status"] == "PASS" else "[FAIL]"
    print(f"  {m} {r['id']:8s} | exp: {r['expected']:15s} | act: {r['actual']:15s} | {r['desc'][:45]}")

print()
print("=" * 70)
print("METRICS")
print("=" * 70)
print(f"  Total:          {total}")
print(f"  Passed:         {p}")
print(f"  Failed:         {f}")
print(f"  Accuracy:       {p/total*100:.1f}%")
for c, (t, pp) in cats.items():
    print(f"  {c}:  {pp}/{t} ({pp/t*100 if t else 0:.0f}%)")

if f:
    print()
    print("FAILED:")
    for r in results:
        if r["status"] == "FAIL":
            print(f"  {r['id']}: exp={r['expected']}, act={r['actual']}")

print()
print("=" * 70)
print("RESULT: PASS (100%)" if p == total else f"RESULT: {p}/{total} needs review")
print("=" * 70)
