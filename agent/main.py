from openai import OpenAI
from typing import List, Dict

from config import DEEPSEEK_API_KEY, BASE_URL, MODEL_NAME
from agent.planner import Planner, Task
from agent.state import StateManager, AgentState
from agent.decision import DecisionEngine, Action
from agent.tools import ToolRegistry, create_default_registry
from agent.memory import ShortTermMemory, LongTermMemory


class CodeAgent:
    def __init__(
        self,
        max_retries: int = 3,
        max_iterations: int = 50,
        memory_turns: int = 10
    ):
        self.client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=BASE_URL)
        self.planner = Planner()
        self.state_mgr = StateManager()
        self.decision = DecisionEngine(max_retries=max_retries, max_iterations=max_iterations)
        self.tools = create_default_registry()
        self.short_memory = ShortTermMemory(max_turns=memory_turns)
        self.long_memory = LongTermMemory()

    def run(self, goal: str) -> Dict:
        print(f"\n{'='*60}")
        print(f"Agent 启动 | 目标: {goal}")
        print(f"{'='*60}\n")

        state = self.state_mgr.load()
        tasks = self.planner.decompose(goal)

        print(f"任务拆解完成，共 {len(tasks)} 个子任务\n")

        for task in tasks:
            if task.id in state.completed_tasks:
                print(f"[跳过] 任务 {task.id}: {task.description}")
                continue

            if not self._deps_met(task, state):
                print(f"[跳过] 任务 {task.id}: 依赖未完成")
                state.failed_tasks.append(task.id)
                continue

            print(f"\n[执行] 任务 {task.id}: {task.description}")
            result = self._execute_task(task, state)
            state.current_task = task.id
            state.iteration += 1

            action_result = self.decision.evaluate(result, state.error_count, state.iteration)

            if action_result.action == Action.COMPLETE:
                state.completed_tasks.append(task.id)
                state.error_count = 0
                print(f"[完成] 任务 {task.id}")
                self.long_memory.store(
                    f"任务 {task.id}: {task.description}",
                    {"status": "completed", "result": str(result)}
                )

            elif action_result.action == Action.RETRY:
                state.error_count += 1
                print(f"[重试] 任务 {task.id} | 原因: {action_result.reason}")
                retry_result = self._retry_task(task, state)
                if retry_result.get("success"):
                    state.completed_tasks.append(task.id)
                    state.error_count = 0
                    print(f"[完成] 任务 {task.id} (重试后)")
                else:
                    state.failed_tasks.append(task.id)
                    print(f"[失败] 任务 {task.id}")

            elif action_result.action == Action.ESCALATE:
                print(f"[升级] 任务 {task.id} | 原因: {action_result.reason}")
                state.failed_tasks.append(task.id)

            elif action_result.action == Action.SKIP:
                print(f"[跳过] 任务 {task.id} | 原因: {action_result.reason}")
                state.failed_tasks.append(task.id)

            self.state_mgr.save(state)

        summary = self._generate_summary(state, goal)
        print(f"\n{'='*60}")
        print(f"Agent 执行结束")
        print(f"完成: {len(state.completed_tasks)} / 失败: {len(state.failed_tasks)}")
        print(f"{'='*60}\n")
        print(summary)

        return {
            "goal": goal,
            "completed": state.completed_tasks,
            "failed": state.failed_tasks,
            "summary": summary
        }

    def _deps_met(self, task: Task, state: AgentState) -> bool:
        return all(dep_id in state.completed_tasks for dep_id in task.dependencies)

    def _execute_task(self, task: Task, state: AgentState) -> Dict:
        self.short_memory.add("user", task.description)

        context = self.long_memory.retrieve(task.description, k=2)
        context_text = "\n".join(c["content"] for c in context) if context else "无相关历史记忆"

        prompt = (
            f"你是一个自主执行任务的 AI Agent。\n\n"
            f"当前任务: {task.description}\n"
            f"历史参考: {context_text}\n\n"
            f"请用以下 JSON 格式返回执行计划:\n"
            f'{{"steps": ["步骤1", "步骤2"], "tool_calls": [{{"tool": "工具名", "args": {{}}}}]}}'
        )

        self.short_memory.add("user", prompt)

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )

            content = response.choices[0].message.content.strip()
            content = content.replace("```json", "").replace("```", "").strip()

            import json
            plan = json.loads(content)

            tool_results = []
            for tool_call in plan.get("tool_calls", []):
                tool_name = tool_call.get("tool")
                args = tool_call.get("args", {})
                
                if not tool_name:
                    return {"success": False, "error_type": "plan_error", "output": "工具名称缺失"}
                
                try:
                    tool_result = self.tools.execute(tool_name, **args)
                    tool_results.append({
                        "tool": tool_name,
                        "args": args,
                        "result": tool_result
                    })
                    
                    if not tool_result.get("success"):
                        return {
                            "success": False,
                            "error_type": tool_result.get("error_type", "tool_error"),
                            "output": tool_result.get("output", "工具执行失败"),
                            "tool_results": tool_results
                        }
                        
                except Exception as e:
                    return {
                        "success": False,
                        "error_type": "tool_exception",
                        "output": str(e),
                        "tool_results": tool_results
                    }

            result = {"success": True, "plan": plan, "tool_results": tool_results}
            self.short_memory.add("assistant", str(result))
            return result

        except Exception as e:
            self.short_memory.add("assistant", f"错误: {str(e)}")
            return {"success": False, "error_type": "planning_error", "output": str(e)}

    def _retry_task(self, task: Task, state: AgentState) -> Dict:
        print(f"  -> 调整策略后重试任务 {task.id}...")
        return self._execute_task(task, state)

    def _generate_summary(self, state: AgentState, goal: str) -> str:
        prompt = (
            f"目标: {goal}\n"
            f"已完成任务: {state.completed_tasks}\n"
            f"失败任务: {state.failed_tasks}\n\n"
            "请生成一段简洁的执行总结。"
        )

        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return f"完成 {len(state.completed_tasks)} 个任务，失败 {len(state.failed_tasks)} 个"

    def query_memory(self, query: str, k: int = 3) -> List[Dict]:
        return self.long_memory.retrieve(query, k=k)

    def get_state(self) -> AgentState:
        return self.state_mgr.load()

    def reset(self):
        self.state_mgr.reset()
        self.short_memory.clear()
        print("Agent 状态已重置")
