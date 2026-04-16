from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

from config import DEEPSEEK_API_KEY, BASE_URL, MODEL_NAME


def build_qa_chain(vector_store):

    retriever = vector_store.as_retriever()

    llm = ChatOpenAI(
        model=MODEL_NAME,
        api_key=DEEPSEEK_API_KEY,
        base_url=BASE_URL,
        temperature=0
    )

    prompt = ChatPromptTemplate.from_template(
        """
请根据以下文档回答问题：

{context}

问题：
{question}
"""
    )

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain