from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_pdf(file_path):
    # 验证文件类型
    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"只支持 PDF 文件，当前文件 '{file_path}' 不是 PDF 格式")
    
    # 验证文件存在
    import os
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")

    loader = PyPDFLoader(file_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )

    documents = text_splitter.split_documents(docs)

    return documents