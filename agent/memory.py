from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import json


class LongTermMemory:
    def __init__(self, persist_dir: str = "./agent/memory"):
        self.persist_dir = persist_dir
        self.embeddings = HuggingFaceEmbeddings(
            model_name="shibing624/text2vec-base-chinese"
        )
        self.db = None
        self._load_or_create()

    def _load_or_create(self):
        if os.path.exists(os.path.join(self.persist_dir, "index.faiss")):
            self.db = FAISS.load_local(
                self.persist_dir, self.embeddings, allow_dangerous_deserialization=True
            )
        else:
            self.db = FAISS.from_texts(["初始化"], self.embeddings)
            os.makedirs(self.persist_dir, exist_ok=True)
            self.db.save_local(self.persist_dir)

    def store(self, text: str, metadata: Optional[Dict] = None):
        self.db.add_texts([text], metadatas=[metadata or {}])
        self.db.save_local(self.persist_dir)

    def retrieve(self, query: str, k: int = 3) -> List[Dict]:
        docs = self.db.similarity_search(query, k=k)
        return [
            {"content": doc.page_content, "metadata": doc.metadata}
            for doc in docs
        ]


class ShortTermMemory:
    def __init__(self, max_turns: int = 10):
        self.messages: List[Dict[str, str]] = []
        self.max_turns = max_turns

    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2:]

    def get_messages(self) -> List[Dict[str, str]]:
        return self.messages.copy()

    def clear(self):
        self.messages.clear()


class ContextBuffer:
    def __init__(self, max_size: int = 100):
        self.buffer: List[Dict] = []
        self.max_size = max_size

    def add(self, key: str, value: any):
        self.buffer.append({"key": key, "value": value})
        if len(self.buffer) > self.max_size:
            self.buffer = self.buffer[-self.max_size:]

    def get(self, key: str) -> Optional[any]:
        for item in reversed(self.buffer):
            if item["key"] == key:
                return item["value"]
        return None

    def get_all(self) -> List[Dict]:
        return self.buffer.copy()
