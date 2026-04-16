from langchain_community.vectorstores import FAISS
from rag.embedding import get_embedding


def build_vector_store(documents):

    embeddings = get_embedding()

    vector_store = FAISS.from_documents(
        documents,
        embeddings
    )

    return vector_store