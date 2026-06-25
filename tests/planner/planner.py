"""Phase 4 Planner 路由引擎 — 确定性规则引擎。

基于 planner-routing-rules.md 实现 R1-R4 四层决策。
输入：project_state（dict）
输出：decision（dict，含 next_skill、reason、prerequisites_met 等）
"""

# ============================================================
# Flow 定义
# ============================================================

FLOW_A = [
    "harness-init",
    "harness-init-docs",
    "harness-clarify",
    "harness-specify",
    "harness-specify-arch",
    "harness-order",
    "harness-analyze",       # optional
    "harness-context",       # recommended
    "harness-execute",
    "harness-review-loop",   # optional
    "harness-runtime-verify", # optional
    "harness-verify",
    "harness-project-memory", # optional
    "harness-archive",
]

FLOW_B = [
    "harness-explore",       # optional
    "harness-change",
    "harness-apply",
    "harness-review-loop",   # optional
    "harness-runtime-verify", # optional
    "harness-verify",
    "harness-project-memory", # optional
    "harness-archive",
]

FLOW_C = [
    "harness-adopt-scan",
    "harness-context-index",  # optional
    "harness-adopt-spec",
]

OPTIONAL_SKILLS = {
    "harness-analyze",
    "harness-context",
    "harness-review-loop",
    "harness-runtime-verify",
    "harness-project-memory",
    "harness-explore",
    "harness-context-index",
}

# ============================================================
# 前置条件判断
# ============================================================

def _init(state):
    i = state.get("initialization", {})
    return not i.get("project_yaml_exists", False)

def _init_docs(state):
    i = state.get("initialization", {})
    return i.get("project_yaml_exists", False) and not i.get("meta_files_exist", False)

def _any_feature_at(state, status):
    for f in state.get("features", []):
        if f.get("status") == status:
            return True
    return False

def _any_task_at(state, status):
    for t in state.get("tasks", []):
        if t.get("status") == status:
            return True
    return False

def _task_at_phase(state, phase):
    for t in state.get("tasks", []):
        if t.get("current_phase") == phase:
            return True
    return False

def _artifact_exists(state, atype):
    a = state.get("artifacts", {})
    return a.get(atype, {}).get("exists", False)

def _verify_status(state):
    v = state.get("verify_results") or {}
    return v.get("overall_status")

def _verify_iteration(state):
    v = state.get("verify_results") or {}
    return v.get("iteration", 0)

def _coverage_below(state, threshold):
    v = state.get("verify_results") or {}
    cov = v.get("coverage", {})
    for key in ["requirement_coverage", "acceptance_coverage", "constraint_coverage", "validation_coverage"]:
        if cov.get(key, 1.0) < threshold:
            return True
    return False

def _has_active_task(state):
    return _any_task_at(state, "active")

def _has_passing_task(state):
    return _any_task_at(state, "passing")

def _active_task_has_validation_steps(state):
    for t in state.get("tasks", []):
        if t.get("status") == "active" and t.get("has_validation_steps"):
            return True
    return False

def _all_features_passing(state):
    for f in state.get("features", []):
        if f.get("status") != "passing":
            return False
    return bool(state.get("features"))

def _any_blocked(state):
    for t in state.get("blocked_tasks", []):
        if t.get("blocked_by"):
            return t
    return None

# ============================================================
# R1：模式检测
# ============================================================

def detect_mode(state):
    if state.get("mode"):
        return state["mode"]
    i = state.get("initialization", {})
    if not i.get("project_yaml_exists", False):
        return "greenfield"
    if _all_features_passing(state):
        return "brownfield"  # all passing means ready for changes
    return "brownfield"

# ============================================================
# R2-R4：路由逻辑
# ============================================================

def route(state):
    mode = detect_mode(state)

    if mode == "greenfield":
        return _route_flow(state, FLOW_A, "Flow A (Greenfield)")
    elif mode == "brownfield":
        return _route_flow(state, FLOW_B, "Flow B (Brownfield)")
    elif mode == "adopt":
        return _route_flow(state, FLOW_C, "Flow C (Adopt)")
    else:
        return {"next_skill": "harness-init", "reason": "未知模式，建议初始化项目", "prerequisites_met": True}

def _route_flow(state, flow, flow_name):
    # R2：流程链定位
    # 找到第一个"应该运行但尚未完成"的 Skill

    # 特殊处理：检查阻塞
    blocked = _any_blocked(state)
    if blocked:
        return {
            "next_skill": "harness-execute",
            "reason": f"任务 {blocked['task_id']} 被 {blocked['blocked_by']} 阻塞，需先完成依赖",
            "prerequisites_met": True,
            "blocked": True,
            "target_task": blocked["blocked_by"][0],
        }

    # 特殊处理：verify 失败需要重试
    vs = _verify_status(state)
    if vs == "failing":
        it = _verify_iteration(state)
        if it >= 3:
            return {
                "next_skill": None,
                "reason": f"验证已失败 {it} 轮，建议人工介入",
                "prerequisites_met": False,
                "loop_detected": True,
            }
        return {
            "next_skill": "harness-execute",
            "reason": f"验证失败（第 {it} 轮），需要修复后重新执行",
            "prerequisites_met": True,
        }

    # 遍历 Flow 链
    for i, skill in enumerate(flow):
        completed = _is_skill_completed(skill, state)
        if completed:
            continue  # 已完成，检查下一个

        # 未完成 — 检查前置条件
        prereqs_met, missing = _check_prerequisites(skill, state)

        if not prereqs_met:
            # 前置条件不满足 — 推荐前置 Skill
            if missing:
                return {
                    "next_skill": missing,
                    "reason": f"{skill} 的前置条件不满足，需要先运行 {missing}",
                    "prerequisites_met": False,
                    "missing_prerequisite": missing,
                }
            return {
                "next_skill": skill,
                "reason": f"推荐运行 {skill}",
                "prerequisites_met": True,
            }

        # 可选 Skill 检查
        if skill in OPTIONAL_SKILLS and not _is_skill_recommended(skill, state):
            continue  # 可选且不推荐，跳过

        return {
            "next_skill": skill,
            "reason": _skill_reason(skill, state),
            "prerequisites_met": True,
        }

    # 所有 Skill 都完成
    if _all_features_passing(state):
        return {"next_skill": None, "reason": "所有功能已完成", "prerequisites_met": True, "done": True}

    return {"next_skill": "harness-archive", "reason": "流程链遍历完成，建议归档", "prerequisites_met": True}


# ============================================================
# Skill 完成判定
# ============================================================

def _is_skill_completed(skill, state):
    features = state.get("features", [])
    tasks = state.get("tasks", [])
    init = state.get("initialization", {})
    artifacts = state.get("artifacts", {})

    checks = {
        "harness-init": lambda: init.get("project_yaml_exists"),
        "harness-init-docs": lambda: init.get("meta_files_exist") and init.get("feature_list_exists"),
        "harness-clarify": lambda: _any_feature_at(state, "clarifying") or _any_feature_at(state, "specifying") or _any_feature_at(state, "ordered") or _any_feature_at(state, "executing") or _any_feature_at(state, "verifying") or _any_feature_at(state, "passing"),
        "harness-specify": lambda: _any_feature_at(state, "specifying") or _any_feature_at(state, "ordered") or _any_feature_at(state, "executing") or _any_feature_at(state, "verifying") or _any_feature_at(state, "passing"),
        "harness-specify-arch": lambda: _any_feature_at(state, "ordered") or _any_feature_at(state, "executing") or _any_feature_at(state, "verifying") or _any_feature_at(state, "passing"),
        "harness-order": lambda: _any_task_at(state, "active") or _any_task_at(state, "passing") or _any_feature_at(state, "executing") or _any_feature_at(state, "verifying") or _any_feature_at(state, "passing"),
        "harness-analyze": lambda: artifacts.get("analyze_report", {}).get("exists", False),
        "harness-context": lambda: artifacts.get("context_bundle", {}).get("exists", False) or _task_at_phase(state, 3) or _any_task_at(state, "passing"),
        "harness-execute": lambda: _task_at_phase(state, 3) or _any_task_at(state, "passing") or _verify_status(state) is not None,
        "harness-review-loop": lambda: artifacts.get("review_report", {}).get("exists", False),
        "harness-runtime-verify": lambda: artifacts.get("runtime_report", {}).get("exists", False),
        "harness-verify": lambda: _verify_status(state) is not None,
        "harness-project-memory": lambda: artifacts.get("project_memory", {}).get("exists", False),
        "harness-archive": lambda: all(f.get("status") == "passing" for f in features) if features else False,
        "harness-explore": lambda: False,  # explore 始终可重新运行
        "harness-change": lambda: _any_task_at(state, "active") or _any_task_at(state, "passing"),
        "harness-apply": lambda: _task_at_phase(state, 3),
        "harness-adopt-scan": lambda: init.get("project_yaml_exists") and _all_features_passing(state),
        "harness-context-index": lambda: artifacts.get("project_index", {}).get("exists", False),
        "harness-adopt-spec": lambda: _any_task_at(state, "passing"),
    }
    return checks.get(skill, lambda: False)()


# ============================================================
# 前置条件检查
# ============================================================

def _check_prerequisites(skill, state):
    """返回 (是否满足, 缺失的前置 Skill)。"""
    prereqs = {
        "harness-init": (True, None),
        "harness-init-docs": (state.get("initialization", {}).get("project_yaml_exists", False), "harness-init"),
        "harness-clarify": (state.get("initialization", {}).get("feature_list_exists", False), "harness-init"),
        "harness-specify": (_any_feature_at(state, "clarifying"), "harness-clarify"),
        "harness-specify-arch": (_any_feature_at(state, "specifying"), "harness-specify"),
        "harness-order": (_any_feature_at(state, "ordered") or _any_feature_at(state, "specifying"), "harness-specify-arch"),
        "harness-analyze": (True, None),
        "harness-context": (_has_active_task(state), "harness-order"),
        "harness-execute": (_has_active_task(state), "harness-order"),
        "harness-review-loop": (_task_at_phase(state, 3), "harness-execute"),
        "harness-runtime-verify": (_task_at_phase(state, 3), "harness-execute"),
        "harness-verify": (_task_at_phase(state, 3) or _any_task_at(state, "passing"), "harness-execute"),
        "harness-project-memory": (_verify_status(state) == "passing", "harness-verify"),
        "harness-archive": (_verify_status(state) == "passing", "harness-verify"),
        "harness-explore": (True, None),
        "harness-change": (state.get("initialization", {}).get("project_yaml_exists", False), "harness-init"),
        "harness-apply": (_has_active_task(state), "harness-change"),
        "harness-adopt-scan": (True, None),
        "harness-context-index": (True, None),
        "harness-adopt-spec": (state.get("initialization", {}).get("project_yaml_exists", False), "harness-adopt-scan"),
    }
    met, missing = prereqs.get(skill, (True, None))
    return met, missing


def _is_skill_recommended(skill, state):
    """判断可选 Skill 是否推荐运行。"""
    rules = {
        "harness-analyze": lambda: _coverage_below(state, 0.8),
        "harness-context": lambda: _has_active_task(state) and not _artifact_exists(state, "context_bundle"),
        "harness-review-loop": lambda: _task_at_phase(state, 3),
        "harness-runtime-verify": lambda: _active_task_has_validation_steps(state),
        "harness-project-memory": lambda: _verify_status(state) == "passing",
        "harness-explore": lambda: False,  # 默认不推荐 explore
        "harness-context-index": lambda: not _artifact_exists(state, "project_index"),
    }
    return rules.get(skill, lambda: True)()


def _skill_reason(skill, state):
    """生成推荐原因。"""
    reasons = {
        "harness-init": "项目未初始化",
        "harness-init-docs": "需要生成 meta 文件",
        "harness-clarify": "功能待澄清",
        "harness-specify": "功能待生成规格",
        "harness-specify-arch": "功能待生成架构规格",
        "harness-order": "功能待生成工单",
        "harness-analyze": "建议审计覆盖率",
        "harness-context": "建议构建上下文",
        "harness-execute": "有待执行工单",
        "harness-review-loop": "建议代码审查",
        "harness-runtime-verify": "建议运行时验证",
        "harness-verify": "需要验证工单",
        "harness-project-memory": "建议积累项目记忆",
        "harness-archive": "验证通过，可归档",
        "harness-explore": "建议探索代码库",
        "harness-change": "需要创建变更",
        "harness-apply": "需要实现变更",
        "harness-adopt-scan": "需要扫描已有代码",
        "harness-context-index": "建议构建项目索引",
        "harness-adopt-spec": "需要反推规格",
    }
    return reasons.get(skill, f"推荐运行 {skill}")
