"""Validation-3 Budget Stress Test Simulator.

模拟 harness-context v2.0 的 P1 Resolver + P0 Builder + P2 Budget，
对大规模合成数据验证裁减机制。
"""

import re
import yaml
from pathlib import Path

BASE = Path(__file__).parent

# ── 加载数据 ──
with open(BASE / "spec-stress.yaml", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

with open(BASE / "architecture-stress.yaml", encoding="utf-8") as f:
    arch = yaml.safe_load(f)

with open(BASE / "task-stress.md", encoding="utf-8") as f:
    task_md = f.read()

# ── 提取 Task 引用 ──
req_refs = re.findall(r"REQ-ORD-\d{3}", task_md)
ac_refs = re.findall(r"\*\*验收标准\*\*：(AC-ORD-\d{3})", task_md)
con_refs = re.findall(r"CON-ORD-\d{3}", task_md)

print(f"=== P1 Resolver 输入 ===")
print(f"V1 requirement_refs: {len(req_refs)} 条")
print(f"V2 acceptance_criteria_ids: {len(ac_refs)} 条")
print(f"V3 constraint_refs: {len(con_refs)} 条")
print(f"总引用数: {len(req_refs) + len(ac_refs) + len(con_refs)}")

# ── P1 解析 ──
spec_reqs = {r["id"]: r for r in spec["requirements"]}
spec_acs = {a["id"]: a for a in spec["acceptance_criteria"]}
arch_cons = {c["id"]: c for c in arch["constraints"]}

resolved_reqs = []
resolved_acs = []
resolved_cons = []
resolve_trace = []

for rid in req_refs:
    if rid in spec_reqs:
        resolved_reqs.append(spec_reqs[rid])
        resolve_trace.append({"source": f"task.requirement_refs[].requirement_id", "target": f"spec.requirements.{rid}", "status": "resolved"})
    else:
        resolve_trace.append({"source": f"task.requirement_refs[].requirement_id", "target": f"spec.requirements.{rid}", "status": "broken_ref"})

for aid in ac_refs:
    if aid in spec_acs:
        resolved_acs.append(spec_acs[aid])
        resolve_trace.append({"source": "task.validation_steps[].acceptance_criteria_ids[]", "target": f"spec.acceptance_criteria.{aid}", "status": "resolved"})
    else:
        resolve_trace.append({"source": "task.validation_steps[].acceptance_criteria_ids[]", "target": f"spec.acceptance_criteria.{aid}", "status": "broken_ref"})

for cid in con_refs:
    if cid in arch_cons:
        resolved_cons.append(arch_cons[cid])
        resolve_trace.append({"source": "task.constraints.constraint_refs[]", "target": f"architecture.constraints.{cid}", "status": "resolved"})
    else:
        resolve_trace.append({"source": "task.constraints.constraint_refs[]", "target": f"architecture.constraints.{cid}", "status": "broken_ref"})

print(f"\n=== P1 Resolver 结果 ===")
print(f"V1 resolved: {len(resolved_reqs)}/{len(req_refs)}")
print(f"V2 resolved: {len(resolved_acs)}/{len(ac_refs)}")
print(f"V3 resolved: {len(resolved_cons)}/{len(con_refs)}")
broken = [t for t in resolve_trace if t["status"] == "broken_ref"]
print(f"broken_ref: {len(broken)}")

# ── 构建 context_bundle（P0 Builder） ──
bundle = {
    "context_bundle": {
        "meta": {"task_id": "ORD-order-001", "version": "2.0"},
        "task": {"id": "ORD-order-001", "title": "订单核心服务实现（大规模版）"},
        "requirements": resolved_reqs,
        "acceptance_criteria": resolved_acs,
        "constraints": resolved_cons,
        "validation_steps": [{"id": f"VAL-ORD-001-{i+1:03d}"} for i in range(len(ac_refs))],
        "project_state": {
            "name": "电商订单系统",
            "architecture_rules": [
                "Service 层不得直接访问数据库",
                "所有 API 返回标准 JSON 格式",
                "支付接口必须幂等",
            ]
        },
        "memory": {
            "adr": arch.get("decisions", []),
            "conventions": [
                "使用 Repository Pattern",
                "类型注解覆盖率 100%",
            ]
        },
        "resolve_trace": resolve_trace,
    }
}

bundle_yaml = yaml.dump(bundle, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)
bundle_bytes = len(bundle_yaml.encode("utf-8"))
bundle_tokens = bundle_bytes // 4

print(f"\n=== P0 Builder 结果 ===")
print(f"context_bundle.yaml: {bundle_bytes:,} bytes (~{bundle_tokens:,} tokens)")

# ── P2 Budget 模拟 ──
MAX_TOKENS = 25000
RESERVE = 5000
AVAILABLE = MAX_TOKENS - RESERVE  # 20000

print(f"\n=== P2 Budget ===")
print(f"max_tokens: {MAX_TOKENS}")
print(f"reserve_tokens: {RESERVE}")
print(f"available_tokens: {AVAILABLE}")
print(f"used_tokens: {bundle_tokens}")
print(f"over_by: {bundle_tokens - AVAILABLE} tokens")

trimmed = []

if bundle_tokens <= AVAILABLE:
    print(f"\n[OK] 未超出 Budget，无需裁减")
else:
    print(f"\n[WARN] 超出 Budget {bundle_tokens - AVAILABLE:,} tokens，开始裁减...")

    # 裁减前先按类别分节估算
    def section_tokens(data, key):
        section_yaml = yaml.dump({key: data}, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)
        return len(section_yaml.encode("utf-8")) // 4

    req_tokens = section_tokens(resolved_reqs, "requirements")
    ac_tokens = section_tokens(resolved_acs, "acceptance_criteria")
    con_tokens = section_tokens(resolved_cons, "constraints")
    adr_tokens = section_tokens(arch.get("decisions", []), "adr")

    print(f"\n  各节 token 估算：")
    print(f"  requirements: {req_tokens}")
    print(f"  acceptance_criteria: {ac_tokens}")
    print(f"  constraints: {con_tokens}")
    print(f"  adr (memory): {adr_tokens}")

    current = bundle_tokens

    # Step 1: 裁减 P2（memory.adr） — 逐条删除
    adrs = arch.get("decisions", [])
    print(f"\n  [P2] 裁减 memory.adr（{len(adrs)} 条）...")
    while current > AVAILABLE and len(adrs) > 0:
        removed = adrs.pop()
        trimmed.append({"section": "memory.adr", "item": removed["id"], "reason": "P2 优先裁减"})
        current = len(yaml.dump(bundle, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200).encode("utf-8")) // 4
        bundle["context_bundle"]["memory"]["adr"] = adrs

    # Step 2: 裁减 P2（project_state.architecture_rules）
    rules = bundle["context_bundle"]["project_state"].get("architecture_rules", [])
    print(f"  [P2] 裁减 architecture_rules（{len(rules)} 条）...")
    while current > AVAILABLE and len(rules) > 0:
        removed = rules.pop()
        trimmed.append({"section": "project_state.architecture_rules", "item": removed[:40], "reason": "P2 优先裁减"})

    # Step 3: 裁减 P1（截断 acceptance_criteria description）
    if current > AVAILABLE:
        print(f"  [P1] 截断 acceptance_criteria description...")
        for ac in resolved_acs:
            if "description" in ac and len(ac["description"]) > 100:
                ac["description"] = ac["description"][:100] + "..."
        trimmed.append({"section": "acceptance_criteria", "item": f"{len(resolved_acs)} 条 AC 描述截断到 100 字", "reason": "P1 优先裁减"})

    # Step 4: 裁减 P0（截断 requirements description）
    if current > AVAILABLE:
        print(f"  [P0] 截断 requirements description...")
        for req in resolved_reqs:
            if "description" in req and len(req["description"]) > 200:
                req["description"] = req["description"][:200] + "..."
        trimmed.append({"section": "requirements", "item": f"{len(resolved_reqs)} 条 REQ 描述截断到 200 字", "reason": "P0 最后裁减"})

    # 最终计算
    final_yaml = yaml.dump(bundle, allow_unicode=True, default_flow_style=False, sort_keys=False, width=200)
    final_bytes = len(final_yaml.encode("utf-8"))
    final_tokens = final_bytes // 4

    print(f"\n  === 裁减结果 ===")
    print(f"  裁减前: {bundle_tokens:,} tokens")
    print(f"  裁减后: {final_tokens:,} tokens")
    print(f"  节省: {bundle_tokens - final_tokens:,} tokens")
    print(f"  裁减项数: {len(trimmed)}")
    print(f"  是否达标: {'[OK]' if final_tokens <= AVAILABLE else '[FAIL] 仍然超限'}")

    for t in trimmed:
        print(f"  - [{t['section']}] {t['item']} ({t['reason']})")

# ── resolve_trace 统计 ──
print(f"\n=== resolve_trace 统计 ===")
print(f"总条目: {len(resolve_trace)}")
resolved = sum(1 for t in resolve_trace if t["status"] == "resolved")
print(f"resolved: {resolved}")
print(f"broken_ref: {len(broken)}")
print(f"覆盖率: {resolved}/{len(resolve_trace)} ({resolved/len(resolve_trace)*100:.1f}%)")

# ── 对比：Task Only vs Task+Bundle ──
task_size = len(task_md.encode("utf-8"))
print(f"\n=== Task Only vs Task+Bundle ===")
print(f"Task Only: {task_size:,} bytes (~{task_size//4:,} tokens)")
print(f"Task+Bundle: {final_bytes if bundle_tokens > AVAILABLE else bundle_bytes:,} bytes (~{final_tokens if bundle_tokens > AVAILABLE else bundle_tokens:,} tokens)")
print(f"比值: {(final_tokens if bundle_tokens > AVAILABLE else bundle_tokens) / (task_size//4):.1f}x")
