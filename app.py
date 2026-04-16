import streamlit as st

from rag.loader import load_pdf
from rag.vector_store import build_vector_store
from rag.qa_chain import build_qa_chain


st.title("📄 AI 文档问答系统 (RAG)")

uploaded_file = st.file_uploader("上传PDF文档", type="pdf")

if uploaded_file:

    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.success("文档上传成功，正在构建知识库...")

    documents = load_pdf("temp.pdf")

    vector_store = build_vector_store(documents)

    qa_chain = build_qa_chain(vector_store)

    st.success("知识库构建完成！")

    question = st.text_input("请输入你的问题")

    if question:

        result = qa_chain.invoke(question)

        st.write("### AI回答")

        st.write(result)