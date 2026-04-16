# AI Agent 框架使用指南

本项目在原有 RAG 系统基础上新增了 AI Agent 框架，使系统具备自主任务执行能力。

## 目录

1. [架构概述](#架构概述)
2. [快速开始](#快速开始)
3. [核心模块](#核心模块)
4. [使用示例](#使用示例)
5. [集成到现有 RAG 系统](#集成到现有-rag-系统)
6. [扩展开发](#扩展开发)
7. [API 参考](#api-参考)

## 架构概述

```
Agent 框架核心组件:
├── planner.py       # 任务规划器 (LLM 拆解大目标为子任务)
├── state.py         # 状态管理器 (SQLite 持久化)
├── decision.py      # 决策引擎 (评估结果，决定下一步)
├── tools.py         # 工具注册中心 (安全执行外部操作)
├── memory.py        # 记忆层 (短期/长期/上下文记忆)
└── main.py          # Agent 主循环 (CodeAgent 类)
```

数据流:
```
用户目标 → 任务拆解 → 依赖检查 → 工具执行 → 决策评估 → 状态持久化 → 生成总结
```

## 快速开始

### 1. 安装依赖

```bash
# 确保已安装原 RAG 系统依赖
# 新增依赖: openai, pydantic
pip install openai pydantic
```

### 2. 配置 API 密钥

```bash
# 设置环境变量 (推荐)
export DEEPSEEK_API_KEY=your_api_key_here

# Windows:
# set DEEPSEEK_API_KEY=your_api_key_here
```

或修改 `config.py` 中的硬编码密钥（不推荐，仅用于开发）。

### 3. 基本使用

```python
from agent.main import CodeAgent

# 创建 Agent
agent = CodeAgent(max_retries=3, max_iterations=50)

# 执行任务
result = agent.run("分析项目中的 PDF 文档，总结主要内容")

print(f"目标: {result['goal']}")
print(f"完成: {len(result['completed'])} 个任务")
print(f"失败: {len(result['failed'])} 个任务")
print(f"总结: {result['summary']}")
```

### 4. 运行测试

```bash
python test_agent.py
```

### 5. 查看演示

```bash
python agent_demo.py
```

## 核心模块

### Planner (任务规划器)

将用户的大目标拆解为可执行的子任务。

```python
from agent.planner import Planner

planner = Planner()
tasks = planner.decompose("分析项目代码质量")
# 返回: [Task(id="1", description="查找项目中的 Python 文件", ...), ...]
```

### State Manager (状态管理器)

持久化 Agent 状态到 SQLite，支持断点续传。

```python
from agent.state import StateManager, AgentState

state_mgr = StateManager()
state = state_mgr.load()  # 加载上次执行状态
state_mgr.save(state)     # 保存当前状态
state_mgr.reset()         # 重置所有状态
```

### Decision Engine (决策引擎)

根据执行结果决定下一步动作：完成、重试、升级（人工介入）、跳过。

```python
from agent.decision import DecisionEngine

decision = DecisionEngine(max_retries=3)
result = decision.evaluate(
    result={"success": False, "error_type": "timeout"},
    error_count=1,
    iteration=5
)
# 返回: DecisionResult(action=Action.RETRY, reason="任务失败，第 2 次重试")
```

### Tool Registry (工具注册中心)

安全地执行外部操作，内置危险命令黑名单。

```python
from agent.tools import create_default_registry

tools = create_default_registry()
result = tools.execute("run_bash", cmd="ls -la")
result = tools.execute("read_file", path="README.md")
```

可用工具:
- `run_bash`: 执行 shell 命令（安全检查）
- `read_file`: 读取文件内容
- `write_file`: 写入文件
- `list_dir`: 列出目录内容
- `search_files`: 通配符搜索文件
- `find_text`: 在文件中查找文本
- `get_file_info`: 获取文件信息
- `count_lines`: 统计文件行数
- `execute_python`: 执行 Python 代码

### Memory System (记忆系统)

三层记忆结构：
1. **长期记忆**: FAISS 向量存储，持久化到磁盘
2. **短期记忆**: 内存中的对话历史
3. **上下文缓存**: 键值对临时存储

```python
from agent.memory import LongTermMemory, ShortTermMemory

long_memory = LongTermMemory()
long_memory.store("任务完成: 分析了 PDF 文档", {"type": "analysis"})
memories = long_memory.retrieve("PDF", k=3)

short_memory = ShortTermMemory(max_turns=10)
short_memory.add("user", "你好")
short_memory.add("assistant", "你好，我是 AI Agent")
```

### CodeAgent (主类)

整合所有组件，提供完整 Agent 功能。

```python
from agent.main import CodeAgent

agent = CodeAgent(
    max_retries=3,      # 最大重试次数
    max_iterations=50,  # 最大迭代次数
    memory_turns=10     # 短期记忆轮数
)

# 执行任务
result = agent.run("分析项目结构")

# 查询记忆
memories = agent.query_memory("项目", k=5)

# 获取状态
state = agent.get_state()

# 重置
agent.reset()
```

## 使用示例

### 示例 1: 项目分析

```python
agent = CodeAgent()
result = agent.run("""
分析这个 Python 项目:
1. 检查项目结构
2. 分析主要代码文件
3. 评估代码质量
4. 给出改进建议
""")
```

### 示例 2: 文档处理自动化

```python
agent = CodeAgent()
result = agent.run("""
自动化文档处理流程:
1. 查找所有 PDF 文件
2. 提取文本内容
3. 分析关键信息
4. 生成摘要报告
""")
```

### 示例 3: 代码维护任务

```python
agent = CodeAgent()
result = agent.run("""
执行代码维护:
1. 查找未使用的导入
2. 检查代码格式问题
3. 运行测试
4. 生成维护报告
""")
```

## 集成到现有 RAG 系统

### 方式 1: 添加 Agent 控制面板到 Streamlit

修改 `app.py`，添加侧边栏：

```python
import streamlit as st
from agent.main import CodeAgent

# 在现有代码中添加...

st.sidebar.title("🤖 AI Agent 控制面板")

if st.sidebar.checkbox("启用 AI Agent"):
    agent = CodeAgent(max_retries=2, max_iterations=20)
    
    agent_task = st.sidebar.text_input("Agent 任务", "分析上传的文档")
    
    if st.sidebar.button("执行 Agent 任务"):
        with st.spinner("Agent 正在执行任务..."):
            result = agent.run(agent_task)
            st.sidebar.success("任务完成!")
            
            with st.expander("查看 Agent 执行结果"):
                st.write("**目标:**", result.get("goal"))
                st.write("**完成的任务:**", len(result.get("completed", [])))
                st.write("**失败的任务:**", len(result.get("failed", [])))
                st.write("**总结:**", result.get("summary", ""))
```

### 方式 2: 创建独立的 Agent 应用

创建新的 Streamlit 应用 `app_agent.py`：

```python
import streamlit as st
from agent.main import CodeAgent

st.title("🤖 AI Agent 任务执行器")

agent = CodeAgent()

task = st.text_area("输入任务描述", "分析当前项目结构")

if st.button("执行任务"):
    with st.spinner("Agent 正在执行任务..."):
        result = agent.run(task)
    
    st.success("任务完成!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("完成任务", len(result.get("completed", [])))
    with col2:
        st.metric("失败任务", len(result.get("failed", [])))
    
    st.write("### 执行总结")
    st.write(result.get("summary", ""))
    
    with st.expander("查看详细结果"):
        st.json(result)
```

### 方式 3: 自动化 RAG 流程

使用 Agent 自动化整个 RAG 流程：

```python
from agent.main import CodeAgent

def automated_rag_pipeline(pdf_path):
    """自动化 RAG 流程"""
    agent = CodeAgent()
    
    # 阶段 1: 文档处理
    result1 = agent.run(f"处理 PDF 文档 {pdf_path}，提取文本内容")
    
    # 阶段 2: 知识库构建
    result2 = agent.run("基于提取的文本构建向量数据库")
    
    # 阶段 3: 问答系统设置
    result3 = agent.run("配置问答系统，准备回答用户问题")
    
    return {
        "document_processing": result1,
        "knowledge_base": result2,
        "qa_system": result3
    }
```

## 扩展开发

### 添加新工具

在 `tools.py` 中添加新工具：

```python
# 1. 实现工具函数
def _new_tool(param1: str, param2: int) -> dict:
    try:
        # 工具逻辑
        return {"success": True, "result": "..."}
    except Exception as e:
        return {"success": False, "error_type": "tool_error", "output": str(e)}

# 2. 在 create_default_registry() 中注册
def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    # ... 现有注册
    registry.register("new_tool", lambda p1, p2: _new_tool(p1, p2))
    return registry
```

### 自定义 Planner 提示

修改 `planner.py` 中的 `decompose()` 方法提示模板，适应特定领域任务。

### 调整决策逻辑

修改 `decision.py` 中的 `evaluate()` 方法，根据业务需求调整决策策略。

### 增强安全机制

在 `ToolRegistry` 中添加更多危险命令到 `blocked_commands` 列表，或实现更复杂的命令分析。

## API 参考

### CodeAgent 类

#### `__init__(max_retries=3, max_iterations=50, memory_turns=10)`
创建 Agent 实例。

#### `run(goal: str) -> Dict`
执行任务，返回结果字典。

#### `query_memory(query: str, k=3) -> List[Dict]`
查询长期记忆。

#### `get_state() -> AgentState`
获取当前状态。

#### `reset()`
重置 Agent 所有状态。

### AgentState 数据类

- `current_task: Optional[str]` - 当前任务 ID
- `completed_tasks: List[str]` - 已完成任务列表
- `failed_tasks: List[str]` - 失败任务列表
- `context: Dict` - 上下文字典
- `error_count: int` - 错误计数
- `iteration: int` - 迭代次数

## 故障排除

### 常见问题

1. **API 密钥错误**
   - 检查 `config.py` 或环境变量
   - 确保 DeepSeek API 可用

2. **工具执行失败**
   - 检查工具参数格式
   - 查看工具返回的 `error_type` 和 `output`

3. **任务拆解不合理**
   - 调整 `planner.py` 中的提示模板
   - 增加任务描述的明确性

4. **记忆检索不准确**
   - 确保使用中文 Embedding 模型
   - 调整检索数量参数 `k`

### 调试建议

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查 Agent 状态
agent = CodeAgent()
state = agent.get_state()
print(f"当前状态: {state}")

# 测试单个工具
from agent.tools import create_default_registry
tools = create_default_registry()
result = tools.execute("list_dir", path=".")
print(f"工具测试: {result}")
```

## 下一步计划

1. **性能优化**
   - 并行执行独立任务
   - 缓存常用工具结果

2. **功能增强**
   - 添加更多专业工具
   - 支持多 Agent 协作
   - 实现工具学习能力

3. **集成扩展**
   - 支持更多文档格式
   - 集成外部 API 服务
   - 添加可视化监控

4. **生产就绪**
   - 完善错误处理
   - 添加性能监控
   - 实现配置管理

---

**提示**: 运行 `python agent_demo.py` 查看完整功能演示，运行 `python test_agent.py` 验证系统功能。