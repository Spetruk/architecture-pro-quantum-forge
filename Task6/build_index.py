#!/usr/bin/env python3
"""
Создание векторного индекса для базы знаний из Task6/knowledge_base
"""

import json
import os
import time
from pathlib import Path
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


class KnowledgeBaseIndexer:
    def __init__(self, knowledge_base_path: str | None = None):
        """Инициализация индексера (берёт данные из Task6/knowledge_base)."""
        script_dir = Path(__file__).resolve().parent
        self.base_dir = script_dir
        self.knowledge_base_path = (
            Path(knowledge_base_path) if knowledge_base_path else script_dir / "knowledge_base"
        )
        self.embeddings_model = "all-mpnet-base-v2"
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.embeddings_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        )

        self.documents: List[Document] = []
        self.chunks: List[Document] = []

    def load_documents(self) -> List[Document]:
        print("📚 Загрузка документов из Task6/knowledge_base...")
        for file_path in self.knowledge_base_path.rglob("*.txt"):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8").strip()
                if not content:
                    continue
                relative_path = file_path.relative_to(self.knowledge_base_path)
                category = relative_path.parts[0] if len(relative_path.parts) > 1 else "root"
                metadata = {
                    "source": str(relative_path),
                    "category": category,
                    "filename": file_path.name,
                    "file_path": str(file_path),
                    "file_size": len(content),
                }
                self.documents.append(Document(page_content=content, metadata=metadata))
            except Exception as e:
                print(f"⚠️ Ошибка при загрузке {file_path}: {e}")

        print(f"✅ Загружено {len(self.documents)} документов")
        return self.documents

    def split_documents(self) -> List[Document]:
        print("✂️ Разбиение документов на чанки...")
        for doc in self.documents:
            chunks = self.text_splitter.split_documents([doc])
            filtered: List[Document] = []
            for i, chunk in enumerate(chunks):
                if len(chunk.page_content.strip()) < 10:
                    continue
                chunk.metadata.update(
                    {
                        "chunk_id": f"{doc.metadata['filename']}_{i}",
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                )
                filtered.append(chunk)
            self.chunks.extend(filtered)
        print(f"✅ Создано {len(self.chunks)} чанков (после фильтрации)")
        return self.chunks

    def create_vector_index(self, persist_directory: str | None = None) -> Chroma:
        print("🔍 Создание векторного индекса (Task6/chroma_db)...")
        target_dir = Path(persist_directory) if persist_directory else (self.base_dir / "chroma_db")
        os.makedirs(target_dir, exist_ok=True)
        vectorstore = Chroma.from_documents(
            documents=self.chunks,
            embedding=self.embeddings,
            persist_directory=str(target_dir),
        )
        print(f"✅ Векторный индекс создан и сохранён в {target_dir}")
        return vectorstore

    def test_search(self, vectorstore: Chroma, test_queries: List[str] | None = None) -> None:
        if test_queries is None:
            test_queries = [
                "Что такое Synth Flux?",
                "Кто такой Xarn Velgor?",
            ]
        print("\n🧪 Тестирование поиска:\n" + "=" * 50)
        for q in test_queries:
            print(f"\n🔍 Запрос: {q}")
            results = vectorstore.similarity_search(q, k=3)
            for i, r in enumerate(results, 1):
                print(f"  {i}. {r.metadata.get('source')}\n     {r.page_content[:150]}...")

    def save_statistics(self, vectorstore: Chroma, processing_time: float) -> dict:
        stats = {
            "model": {
                "name": self.embeddings_model,
                "embedding_size": 768,
            },
            "knowledge_base": {
                "path": str(self.knowledge_base_path),
                "total_documents": len(self.documents),
                "total_chunks": len(self.chunks),
            },
            "processing": {
                "time_seconds": processing_time,
                "time_minutes": processing_time / 60,
                "chunks_per_second": 0 if processing_time == 0 else len(self.chunks) / processing_time,
            },
            "vectorstore": {"type": "ChromaDB", "persist_directory": "./chroma_db"},
        }
        Path("indexing_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        print("📊 Статистика сохранена в indexing_stats.json")
        return stats


def main():
    print("🚀 Запуск создания векторного индекса (Task6)")
    print("=" * 50)
    start = time.time()

    indexer = KnowledgeBaseIndexer()
    indexer.load_documents()
    indexer.split_documents()
    if not indexer.chunks:
        print("⚠️ Нет данных для индексации (0 чанков). Проверьте Task6/knowledge_base.")
        return
    vs = indexer.create_vector_index()
    # indexer.test_search(vs)  # при необходимости включить

    elapsed = time.time() - start
    indexer.save_statistics(vs, elapsed)

    print("\n" + "=" * 50)
    print("Готово.")


if __name__ == "__main__":
    main()


