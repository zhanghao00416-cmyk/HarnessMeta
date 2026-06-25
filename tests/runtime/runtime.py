"""Phase 5 Runtime Execution Layer — 状态机 + Retry Policy 引擎。

实现 runtime-state-model.md 的 10 状态状态机 + runtime-retry-policy.md 的决策逻辑。
不涉及真实 Agent 调用（Phase 5.1 仅验证状态机逻辑）。
"""

from enum import Enum
import time


class Status(Enum):
    PENDING = "PENDING"
    BUILDING_CONTEXT = "BUILDING_CONTEXT"
    CONTEXT_READY = "CONTEXT_READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    VERIFY_FAILED = "VERIFY_FAILED"


# 终态集合
TERMINAL_STATES = {Status.FAILED, Status.VERIFIED, Status.VERIFY_FAILED}

# 需要上下文的 Skill
CONTEXT_REQUIRED = {"harness-execute", "harness-apply", "harness-review-loop", "harness-runtime-verify"}

# 不需要 Runtime 的 Skill（直通模式）
DIRECT_SKILLS = {"harness-init", "harness-init-docs", "harness-clarify", "harness-specify",
                 "harness-specify-arch", "harness-order", "harness-analyze",
                 "harness-explore", "harness-change", "harness-archive"}

# 可重试错误关键字
RETRYABLE_ERRORS = [
    "上下文构建失败", "context build failed",
    "超时", "timeout",
    "输出不完整", "incomplete output",
    "测试失败", "test fail",
    "lint", "格式",
    "网络", "network",
    "验证失败", "verify fail",
]

# 不可重试错误关键字
NON_RETRYABLE_ERRORS = [
    "Schema 违规", "schema violation",
    "依赖缺失", "dependency missing", "FileNotFoundError",
    "权限错误", "PermissionError", "permission",
    "配置错误", "config error",
    "用户取消", "cancelled",
]


class ExecutionState:
    """单个 Skill 的执行状态。"""
    def __init__(self, task_id: str, skill: str):
        self.task_id = task_id
        self.skill = skill
        self.status = Status.PENDING
        self.retry_count = 0
        self.max_retries = self._default_max_retries(skill)
        self.cooldown = self._default_cooldown(skill)
        self.last_error = None
        self.previous_errors = []  # 用于相同错误检测
        self.context_ready = False
        self.result = {}
        self.verify = {"overall_status": None, "validation_status_map": {}}
        self.completed = False  # Agent 是否完成

    def _default_max_retries(self, skill: str) -> int:
        config = {
            "harness-execute": 3, "harness-apply": 3,
            "harness-review-loop": 2, "harness-runtime-verify": 2,
            "harness-context": 1,
        }
        return config.get(skill, 0)

    def _default_cooldown(self, skill: str) -> int:
        if skill == "harness-runtime-verify":
            return 5
        return 0


class RuntimeExecutor:
    """Runtime 执行器 — 状态机驱动。"""

    def __init__(self):
        self.state: ExecutionState = None

    @property
    def status(self) -> Status:
        return self.state.status if self.state else None

    def start(self, skill: str, task_id: str) -> ExecutionState:
        """创建执行状态。"""
        self.state = ExecutionState(task_id, skill)
        return self._transition_from_pending()

    def _transition_from_pending(self):
        """PENDING → BUILDING_CONTEXT 或 RUNNING（直通）。"""
        s = self.state
        if s.skill in DIRECT_SKILLS:
            s.status = Status.RUNNING
            # 直通：直接完成
            s.completed = True
            return self._on_completed()
        if s.skill in CONTEXT_REQUIRED and s.skill != "harness-context":
            s.status = Status.BUILDING_CONTEXT
            return s
        s.status = Status.RUNNING
        return s

    def build_context_success(self):
        """BUILDING_CONTEXT → CONTEXT_READY。"""
        if self.state.status != Status.BUILDING_CONTEXT:
            raise ValueError(f"非法迁移：{self.state.status} → CONTEXT_READY")
        self.state.context_ready = True
        self.state.status = Status.CONTEXT_READY
        return self.state

    def build_context_failed(self, error: str):
        """BUILDING_CONTEXT → FAILED"""
        if self.state.status != Status.BUILDING_CONTEXT:
            raise ValueError(f"非法迁移：{self.state.status} → FAILED")
        self.state.last_error = error
        self.state.status = Status.FAILED
        return self._handle_failure()

    def start_agent(self):
        """CONTEXT_READY → RUNNING"""
        if self.state.status not in {Status.CONTEXT_READY, Status.PENDING}:
            raise ValueError(f"非法迁移：{self.state.status} → RUNNING")
        self.state.status = Status.RUNNING
        return self.state

    def agent_completed(self, success: bool = True, error: str = None):
        """RUNNING → COMPLETED 或 FAILED"""
        if self.state.status != Status.RUNNING:
            raise ValueError(f"非法迁移：{self.state.status} → COMPLETED/FAILED")
        if success:
            self.state.completed = True
            self.state.status = Status.COMPLETED
            return self._on_completed()
        else:
            self.state.last_error = error
            self.state.status = Status.FAILED
            return self._handle_failure()

    def _on_completed(self):
        """COMPLETED → VERIFYING 或 VERIFIED"""
        s = self.state
        if s.skill in DIRECT_SKILLS:
            s.status = Status.VERIFIED
            return s
        # 检查是否有 validation_steps（简化：skill 在 CONTEXT_REQUIRED 中则需要验证）
        if s.skill in CONTEXT_REQUIRED:
            s.status = Status.VERIFYING
            return s
        s.status = Status.VERIFIED
        return s

    def verify_passed(self):
        """VERIFYING → VERIFIED"""
        if self.state.status != Status.VERIFYING:
            raise ValueError(f"非法迁移：{self.state.status} → VERIFIED")
        self.state.verify["overall_status"] = "passing"
        self.state.status = Status.VERIFIED
        return self.state

    def verify_failed(self, error: str):
        """VERIFYING → VERIFY_FAILED"""
        if self.state.status != Status.VERIFYING:
            raise ValueError(f"非法迁移：{self.state.status} → VERIFY_FAILED")
        self.state.verify["overall_status"] = "failing"
        self.state.last_error = error
        self.state.status = Status.VERIFY_FAILED
        return self._handle_verify_failure()

    def _handle_failure(self):
        """FAILED → RETRYING 或 FAILED（终态）"""
        s = self.state
        if self._is_retryable(s.last_error) and self._can_retry():
            s.status = Status.RETRYING
            return s
        # 不可重试或耗尽 → 终态
        return s

    def _handle_verify_failure(self):
        """VERIFY_FAILED → RETRYING 或 VERIFY_FAILED（终态）"""
        s = self.state
        if self._is_retryable(s.last_error) and self._can_retry():
            s.status = Status.RETRYING
            return s
        return s

    def retry_cooldown_done(self):
        """RETRYING → RUNNING"""
        if self.state.status != Status.RETRYING:
            raise ValueError(f"非法迁移：{self.state.status} → RUNNING")
        self.state.retry_count += 1
        self.state.status = Status.RUNNING
        return self.state

    def _can_retry(self) -> bool:
        s = self.state
        if s.retry_count >= s.max_retries:
            return False
        # 先记录本次错误，再检查（确保第二次相同错误被检测）
        s.previous_errors.append(s.last_error or "")
        if len(s.previous_errors) >= 2:
            last_two = s.previous_errors[-2:]
            if last_two[0][:100] == last_two[1][:100]:
                return False  # 连续 2 次相同错误
        return True

    def _is_retryable(self, error: str) -> bool:
        if not error:
            return True
        error_lower = error.lower()
        for keyword in NON_RETRYABLE_ERRORS:
            if keyword.lower() in error_lower:
                return False
        return True

    def is_terminal(self) -> bool:
        return self.state.status in TERMINAL_STATES

    def is_direct_mode(self, skill: str) -> bool:
        return skill in DIRECT_SKILLS


# ============================================================
# 辅助函数
# ============================================================
def simulate_execution(skill: str, task_id: str, events: list) -> ExecutionState:
    """用事件列表模拟一次完整执行。

    events 是 (event_name, kwargs) 的列表。
    """
    executor = RuntimeExecutor()
    state = executor.start(skill, task_id)

    for event_name, kwargs in events:
        kwargs = kwargs or {}
        if event_name == "build_context_success":
            state = executor.build_context_success()
        elif event_name == "build_context_failed":
            state = executor.build_context_failed(**kwargs)
        elif event_name == "start_agent":
            state = executor.start_agent()
        elif event_name == "agent_completed":
            state = executor.agent_completed(**kwargs)
        elif event_name == "verify_passed":
            state = executor.verify_passed()
        elif event_name == "verify_failed":
            state = executor.verify_failed(**kwargs)
        elif event_name == "retry_cooldown_done":
            state = executor.retry_cooldown_done()
        elif event_name == "agent_failed":
            state = executor.agent_completed(success=False, **kwargs)

    return state
