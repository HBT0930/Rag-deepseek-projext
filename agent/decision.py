from enum import Enum
from dataclasses import dataclass


class Action(Enum):
    EXECUTE = "execute"
    RETRY = "retry"
    ESCALATE = "escalate"
    COMPLETE = "complete"
    SKIP = "skip"


@dataclass
class DecisionResult:
    action: Action
    reason: str
    next_step: str = ""


class DecisionEngine:
    def __init__(self, max_retries: int = 3, max_iterations: int = 50):
        self.max_retries = max_retries
        self.max_iterations = max_iterations

    def evaluate(
        self,
        result: dict,
        error_count: int,
        iteration: int
    ) -> DecisionResult:
        if iteration >= self.max_iterations:
            return DecisionResult(
                action=Action.ESCALATE,
                reason=f"达到最大迭代次数 ({self.max_iterations})"
            )

        if result.get("success"):
            return DecisionResult(
                action=Action.COMPLETE,
                reason="任务执行成功"
            )

        error_type = result.get("error_type", "unknown")

        if error_type == "dependency_not_met":
            return DecisionResult(
                action=Action.SKIP,
                reason="依赖任务未完成"
            )

        if error_count < self.max_retries:
            return DecisionResult(
                action=Action.RETRY,
                reason=f"任务失败，第 {error_count + 1} 次重试",
                next_step="调整策略后重试"
            )

        return DecisionResult(
            action=Action.ESCALATE,
            reason=f"重试 {self.max_retries} 次后仍失败，需要人工介入"
        )
