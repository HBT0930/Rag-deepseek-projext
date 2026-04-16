#!/usr/bin/env python3
"""
AI Agent 演示脚本
展示如何将新增的 Agent 框架与现有 RAG 系统集成使用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.main import CodeAgent


def demo_basic_usage():
    """演示基础用法"""
    print("=" * 60)
    print("演示 1: 基础 Agent 使用")
    print("=" * 60)
    
    # 创建 Agent
    agent = CodeAgent(max_retries=2, max_iterations=20)
    
    # 执行简单任务
    print("任务: 分析当前项目结构")
    result = agent.run("分析当前项目的目录结构和主要文件")
    
    print(f"\n结果摘要: {result.get('summary', '')[:150]}...")
    print(f"完成 {len(result.get('completed', []))} 个任务")


def demo_rag_integration():
    """演示与 RAG 系统的集成"""
    print("\n" + "=" * 60)
    print("演示 2: 与 RAG 系统集成")
    print("=" * 60)
    
    agent = CodeAgent(max_retries=2, max_iterations=20)
    
    print("场景: 自动化文档处理流程")
    print("1. 查找 PDF 文件")
    print("2. 分析 PDF 内容")
    print("3. 生成摘要")
    
    result = agent.run("查找项目中的 PDF 文件并分析其内容")
    
    print(f"\n自动化处理完成!")
    print(f"总结: {result.get('summary', '')[:200]}...")


def demo_multi_step_task():
    """演示多步复杂任务"""
    print("\n" + "=" * 60)
    print("演示 3: 多步复杂任务")
    print("=" * 60)
    
    agent = CodeAgent(max_retries=3, max_iterations=30)
    
    print("任务: 完整项目分析")
    print("包括:")
    print("- 分析代码结构")
    print("- 检查依赖关系")
    print("- 评估代码质量")
    print("- 生成改进建议")
    
    result = agent.run("分析这个 Python 项目的代码结构、依赖关系和代码质量，并给出改进建议")
    
    print(f"\n多步任务完成!")
    print(f"完成 {len(result.get('completed', []))} 个子任务")
    print(f"总结: {result.get('summary', '')[:300]}...")


def demo_agent_tools():
    """演示 Agent 的工具使用"""
    print("\n" + "=" * 60)
    print("演示 4: Agent 工具能力")
    print("=" * 60)
    
    agent = CodeAgent(max_retries=2, max_iterations=15)
    
    print("Agent 可用工具:")
    print("- run_bash: 执行 shell 命令")
    print("- read_file: 读取文件")
    print("- write_file: 写入文件")
    print("- list_dir: 列出目录")
    print("- search_files: 搜索文件")
    print("- find_text: 查找文本")
    print("- get_file_info: 获取文件信息")
    print("- count_lines: 统计行数")
    print("- execute_python: 执行 Python 代码")
    
    result = agent.run("使用可用工具分析项目的 Python 文件数量和总代码行数")
    
    print(f"\n工具使用演示完成!")
    print(f"结果: {result.get('summary', '')[:200]}...")


def demo_agent_memory():
    """演示 Agent 记忆功能"""
    print("\n" + "=" * 60)
    print("演示 5: Agent 记忆功能")
    print("=" * 60)
    
    agent = CodeAgent(max_retries=1, max_iterations=10)
    
    # 执行第一个任务
    print("执行第一个任务...")
    agent.run("查看当前目录的 README 文件")
    
    # 查询记忆
    print("\n查询相关记忆...")
    memories = agent.query_memory("README", k=2)
    
    if memories:
        print(f"找到 {len(memories)} 条相关记忆:")
        for i, memory in enumerate(memories):
            print(f"  {i+1}. {memory.get('content', '')[:80]}...")
    else:
        print("未找到相关记忆")
    
    # 继续执行相关任务
    print("\n基于记忆执行相关任务...")
    result = agent.run("基于之前的分析，总结项目的主要功能")
    
    print(f"\n基于记忆的任务完成!")
    print(f"总结: {result.get('summary', '')[:150]}...")


def create_integrated_app_example():
    """创建集成示例代码"""
    print("\n" + "=" * 60)
    print("演示 6: 集成到 Streamlit RAG 应用的示例代码")
    print("=" * 60)
    
    example_code = '''
import streamlit as st
from agent.main import CodeAgent

# 在现有 RAG 应用中添加 Agent 功能
st.sidebar.title("🤖 AI Agent 控制面板")

# Agent 配置
if st.sidebar.checkbox("启用 AI Agent"):
    agent = CodeAgent(max_retries=2, max_iterations=20)
    
    agent_task = st.sidebar.text_input("Agent 任务", "分析上传的文档")
    
    if st.sidebar.button("执行 Agent 任务"):
        with st.spinner("Agent 正在执行任务..."):
            result = agent.run(agent_task)
            st.sidebar.success("任务完成!")
            
            # 显示结果
            with st.expander("查看 Agent 执行结果"):
                st.write("**目标:**", result.get("goal"))
                st.write("**完成的任务:**", len(result.get("completed", [])))
                st.write("**失败的任务:**", len(result.get("failed", [])))
                st.write("**总结:**", result.get("summary", ""))
    
    # 记忆查询
    if st.sidebar.checkbox("查询 Agent 记忆"):
        query = st.sidebar.text_input("查询记忆", "PDF")
        if query:
            memories = agent.query_memory(query, k=3)
            for i, memory in enumerate(memories):
                st.sidebar.write(f"记忆 {i+1}: {memory.get('content', '')[:100]}...")
'''
    
    print("以下代码可以添加到现有的 app.py 中:")
    print(example_code)


def main():
    """主演示函数"""
    print("AI Agent 框架演示")
    print("=" * 60)
    print("这个演示展示新增的 Agent 框架的功能和集成方式")
    print()
    
    demos = [
        ("基础使用", demo_basic_usage),
        ("RAG 集成", demo_rag_integration),
        ("多步任务", demo_multi_step_task),
        ("工具能力", demo_agent_tools),
        ("记忆功能", demo_agent_memory),
        ("集成示例", create_integrated_app_example),
    ]
    
    for demo_name, demo_func in demos:
        try:
            demo_func()
            print()
        except Exception as e:
            print(f"演示 '{demo_name}' 失败: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("=" * 60)
    print("演示完成!")
    print()
    print("下一步建议:")
    print("1. 运行测试: python test_agent.py")
    print("2. 查看 Agent 代码: agent/ 目录")
    print("3. 集成到现有应用: 参考上面的示例代码")
    print("4. 扩展功能: 添加更多工具到 ToolRegistry")


if __name__ == "__main__":
    main()