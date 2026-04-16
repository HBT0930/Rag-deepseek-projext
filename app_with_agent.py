import streamlit as st
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag.loader import load_pdf
from rag.vector_store import build_vector_store
from rag.qa_chain import build_qa_chain
from agent.main import CodeAgent


# 页面配置
st.set_page_config(
    page_title="AI 文档问答系统 (RAG + Agent)",
    page_icon="🤖",
    layout="wide"
)

# 标题
st.title("📄🤖 AI 文档问答系统 (RAG + Agent)")

# 侧边栏 - Agent 控制面板
st.sidebar.title("🤖 AI Agent 控制面板")

# 初始化 Agent
if "agent" not in st.session_state:
    st.session_state.agent = CodeAgent(max_retries=2, max_iterations=20)

agent = st.session_state.agent

# Agent 功能开关
agent_enabled = st.sidebar.checkbox("启用 AI Agent", value=True)

if agent_enabled:
    st.sidebar.markdown("---")
    st.sidebar.subheader("任务执行")
    
    # 预设任务选项
    task_options = {
        "分析项目结构": "分析当前项目的目录结构和主要文件",
        "处理PDF文档": "处理上传的PDF文档，提取文本内容并分析",
        "自动化问答": "基于上传的文档自动构建知识库并回答常见问题",
        "代码质量检查": "检查项目代码质量，找出潜在问题",
        "自定义任务": ""
    }
    
    selected_task = st.sidebar.selectbox(
        "选择预设任务",
        list(task_options.keys())
    )
    
    if selected_task == "自定义任务":
        agent_task = st.sidebar.text_area("输入自定义任务", "分析上传的文档")
    else:
        agent_task = task_options[selected_task]
        st.sidebar.info(f"任务: {agent_task[:50]}...")
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("执行任务", type="primary"):
            st.session_state.agent_task_running = True
    
    with col2:
        if st.button("重置 Agent"):
            agent.reset()
            st.sidebar.success("Agent 已重置!")
    
    # 执行 Agent 任务
    if st.session_state.get("agent_task_running"):
        with st.spinner("🤖 Agent 正在执行任务..."):
            result = agent.run(agent_task)
            st.session_state.agent_result = result
            st.session_state.agent_task_running = False
        
        st.sidebar.success("任务完成!")
        
        # 显示结果摘要
        with st.sidebar.expander("查看任务结果", expanded=True):
            st.write(f"**目标:** {result.get('goal', '')[:50]}...")
            st.metric("完成任务", len(result.get('completed', [])))
            st.metric("失败任务", len(result.get('failed', [])))
            
            if st.button("查看详细报告"):
                st.session_state.show_agent_report = True
    
    # 显示详细报告
    if st.session_state.get("show_agent_report") and st.session_state.get("agent_result"):
        st.sidebar.markdown("---")
        st.sidebar.subheader("详细报告")
        result = st.session_state.agent_result
        
        st.sidebar.write("**完整总结:**")
        st.sidebar.write(result.get('summary', ''))
        
        if st.sidebar.button("关闭报告"):
            st.session_state.show_agent_report = False
    
    # 记忆查询功能
    st.sidebar.markdown("---")
    st.sidebar.subheader("记忆查询")
    
    memory_query = st.sidebar.text_input("查询记忆", "PDF")
    if memory_query and st.sidebar.button("查询"):
        memories = agent.query_memory(memory_query, k=3)
        if memories:
            st.sidebar.success(f"找到 {len(memories)} 条相关记忆")
            for i, memory in enumerate(memories):
                with st.sidebar.expander(f"记忆 {i+1}"):
                    st.write(memory.get('content', '')[:200] + "...")
        else:
            st.sidebar.info("未找到相关记忆")
    
    # Agent 状态
    st.sidebar.markdown("---")
    st.sidebar.subheader("Agent 状态")
    
    state = agent.get_state()
    st.sidebar.write(f"迭代次数: {state.iteration}")
    st.sidebar.write(f"错误计数: {state.error_count}")
    st.sidebar.write(f"完成任务: {len(state.completed_tasks)}")
    st.sidebar.write(f"失败任务: {len(state.failed_tasks)}")

# 主区域 - 原 RAG 功能
st.header("📄 文档问答系统")

# 文件上传
uploaded_file = st.file_uploader("上传PDF文档", type="pdf")

if uploaded_file:
    # 严格验证文件类型
    if not uploaded_file.name.lower().endswith('.pdf'):
        st.error(f"❌ 只支持 PDF 文件，当前文件 '{uploaded_file.name}' 不是 PDF 格式")
        st.stop()
    
    # 保存上传的文件
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())
    
    st.success("文档上传成功，正在构建知识库...")
    
    # 加载文档
    documents = load_pdf("temp.pdf")
    
    # 构建向量存储
    vector_store = build_vector_store(documents)
    
    # 构建问答链
    qa_chain = build_qa_chain(vector_store)
    
    st.success("知识库构建完成！")
    
    # 如果启用了 Agent，自动分析文档
    if agent_enabled and st.session_state.get("auto_analyze", True):
        with st.spinner("Agent 正在分析文档..."):
            doc_analysis_result = agent.run(f"分析上传的PDF文档，提取主要内容")
            st.session_state.doc_analysis = doc_analysis_result
        
        with st.expander("📊 Agent 文档分析结果", expanded=True):
            if st.session_state.get("doc_analysis"):
                result = st.session_state.doc_analysis
                st.write("**分析总结:**")
                st.write(result.get('summary', ''))
                
                # 提取关键信息
                st.write("**关键信息:**")
                st.write("- 文档已成功上传并处理")
                st.write("- 知识库构建完成")
                st.write("- 可以开始提问")
    
    # 问答区域
    st.markdown("---")
    st.subheader("💬 问答系统")
    
    question = st.text_input("请输入你的问题", placeholder="例如：这篇文档主要讲什么？")
    
    if question:
        with st.spinner("正在生成回答..."):
            answer = qa_chain.invoke(question)
        
        st.write("### AI回答")
        st.write(answer)
        
        # 如果启用了 Agent，记录问答交互
        if agent_enabled:
            agent.long_memory.store(
                f"用户提问: {question}",
                {"type": "qa", "question": question, "answer": answer[:100]}
            )

# 页脚
st.markdown("---")
st.markdown("### 系统信息")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("**RAG 系统**\n文档问答功能")

with col2:
    st.info("**AI Agent**\n自主任务执行")

with col3:
    st.info("**集成系统**\n智能文档处理")

# 初始化 session state
if "agent_task_running" not in st.session_state:
    st.session_state.agent_task_running = False
if "agent_result" not in st.session_state:
    st.session_state.agent_result = None
if "show_agent_report" not in st.session_state:
    st.session_state.show_agent_report = False
if "auto_analyze" not in st.session_state:
    st.session_state.auto_analyze = True
if "doc_analysis" not in st.session_state:
    st.session_state.doc_analysis = None