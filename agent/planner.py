from typing import List, Dict, Optional
from pydantic import BaseModel
from openai import OpenAI
import json

from config import DEEPSEEK_API_KEY, BASE_URL, MODEL_NAME


class Task(BaseModel):
    id: str
    description: str
    status: str = "pending"
    dependencies: List[str] = []


class Planner:
    def __init__(self):
        self.client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=BASE_URL
        )

    def decompose(self, goal: str) -> List[Task]:
        prompt = (
            "你是一个任务规划助手。将以下目标拆解为可执行的子任务。\n"
            f"目标: {goal}\n\n"
            "返回纯 JSON 数组格式，不要包含其他文字:\n"
            '[{"id": "1", "description": "任务描述", "dependencies": []}, ...]'
        )

        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()

        content = content.replace("```json", "").replace("```", "").strip()

        try:
            task_data = json.loads(content)
            return [Task(**t) for t in task_data]
        except (json.JSONDecodeError, Exception) as e:
            print(f"任务解析失败: {e}")
            return [Task(id="1", description=goal)]

    def replan(self, completed: List[str], remaining: str) -> List[Task]:
        prompt = (
            f"已完成任务: {completed}\n"
            f"剩余目标: {remaining}\n\n"
            "重新规划剩余任务，返回 JSON 数组:\n"
            '[{"id": "1", "description": "...", "dependencies": []}]'
        )

        response = self.client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()

        try:
            task_data = json.loads(content)
            return [Task(**t) for t in task_data]
        except Exception:
            return [Task(id="1", description=remaining)]
