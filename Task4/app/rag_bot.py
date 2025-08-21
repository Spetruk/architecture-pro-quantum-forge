"""
RAG-бот с техниками промптинга
Поддерживает Few-shot и Chain-of-Thought подходы
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Конфигурация RAG-бота"""
    vector_db_path: str = "chroma_db"
    embedding_model: str = "all-mpnet-base-v2"
    max_results: int = 5
    temperature: float = 0.7
    chunk_size: int = 2000
    chunk_overlap: int = 200


class RAGBot:
    """RAG-бот с поддержкой различных техник промптинга"""
    
    def __init__(self, config: RAGConfig):
        self.config = config
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.embedding_model,
            model_kwargs={'device': 'cpu'}
        )
        
        # Инициализация векторной базы
        persist_dir = os.path.abspath(config.vector_db_path)
        if not os.path.exists(persist_dir):
            raise FileNotFoundError(
                f"Векторная база не найдена по пути: {persist_dir}. "
                f"Убедитесь, что каталог смонтирован в контейнер (docker-compose) и индекс создан (Task3)."
            )
        self.vector_db = Chroma(
            persist_directory=persist_dir,
            embedding_function=self.embeddings
        )
        
        # Инициализация LLM
        self.llm = self._initialize_llm()
        
        # Промпты для различных техник
        self.prompts = self._create_prompts()
        
        logger.info("RAG-бот инициализирован")
    
    def _create_prompts(self) -> Dict[str, PromptTemplate]:
        """Создание промптов для различных техник"""
        
        # Базовый промпт
        base_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
Используй следующую информацию для ответа на вопрос:

Контекст:
{context}

Вопрос: {question}

Ответ:"""
        )
        
        # Few-shot промпт
        few_shot_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
Ты - помощник по вселенной научной фантастики. Вот несколько примеров вопросов и ответов:

Пример 1:
Вопрос: Кто такой Xarn Velgor?
Ответ: Xarn Velgor - это могущественный темный лорд, бывший ученик Wardens, который перешел на темную сторону Synth Flux. Он известен своими способностями к Synth Flux и использованием Lumen Blade.

Пример 2:
Вопрос: Что такое Synth Flux?
Ответ: Synth Flux - это энергетическое поле, которое окружает и связывает все в существовании. Это источник силы для Wardens и Vyrn, позволяющий им использовать различные способности.

Теперь ответь на вопрос, используя предоставленный контекст:

Контекст:
{context}

Вопрос: {question}

Ответ:"""
        )
        
        # Chain-of-Thought промпт
        cot_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
Ты - помощник по вселенной научной фантастики. Отвечай на вопросы, рассуждая пошагово.

Контекст:
{context}

Вопрос: {question}

Давай рассуждать пошагово:

1. Сначала определим, о чем спрашивает пользователь
2. Найдем релевантную информацию в контексте
3. Проанализируем найденную информацию
4. Сформулируем четкий и полный ответ

Рассуждение:"""
        )
        
        return {
            "base": base_prompt,
            "few_shot": few_shot_prompt,
            "chain_of_thought": cot_prompt
        }
    
    def _initialize_llm(self):
        """Инициализация LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY не найден в переменных окружения")
        return ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=self.config.temperature,
            api_key=api_key
        )
    
    def search_documents(self, query: str) -> List[Document]:
        """Поиск релевантных документов"""
        try:
            results = self.vector_db.similarity_search(
                query, 
                k=self.config.max_results
            )
            logger.info(f"Найдено {len(results)} релевантных документов")
            return results
        except Exception as e:
            logger.error(f"Ошибка при поиске документов: {e}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """Форматирование контекста из найденных документов"""
        if not documents:
            return "Информация не найдена в базе знаний."
        
        context_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Неизвестный источник')
            category = doc.metadata.get('category', 'Неизвестная категория')
            chunk_id = doc.metadata.get('chunk_id', 'N/A')
            
            context_parts.append(f"""
--- Документ {i} ---
Источник: {source}
Категория: {category}
Чанк: {chunk_id}
Содержание:
{doc.page_content}
""")
        
        return "\n".join(context_parts)
    
    def generate_response(self, query: str, technique: str = "base") -> Dict[str, Any]:
        """Генерация ответа с использованием выбранной техники промптинга"""
        
        # Поиск релевантных документов
        documents = self.search_documents(query)
        context = self.format_context(documents)
        
        # Выбор промпта
        if technique not in self.prompts:
            logger.warning(f"Неизвестная техника {technique}, используем базовую")
            technique = "base"
        
        prompt = self.prompts[technique]
        
        # Создание цепочки RAG
        chain = (
            {"context": lambda x: x["context"], "question": lambda x: x["question"]}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        # Генерация ответа с помощью LLM
        response = chain.invoke({
            "context": context,
            "question": query
        })
        
        # Сохраняем финальный промпт для отладки
        formatted_prompt = self.prompts[technique].format(context=context, question=query)

        return {
            "query": query,
            "technique": technique,
            "response": response,
            "context": context,
            "prompt": formatted_prompt,
            "sources": [
                {
                    "source": doc.metadata.get('source', 'Неизвестный источник'),
                    "category": doc.metadata.get('category', 'Неизвестная категория'),
                    "chunk_id": doc.metadata.get('chunk_id', 'N/A'),
                    "content_preview": doc.page_content[:200] + "..."
                }
                for doc in documents
            ],
            "num_sources": len(documents)
        }
    

    

    
    def interactive_mode(self):
        """Интерактивный режим работы с ботом"""
        print("🤖 RAG-бот запущен в интерактивном режиме")
        print("Доступные техники промптинга:")
        print("  - base: Базовый промпт")
        print("  - few_shot: Few-shot обучение")
        print("  - chain_of_thought: Chain-of-Thought рассуждение")
        print("LLM: OpenAI GPT-3.5-turbo")
        print("Введите 'quit' для выхода")
        print("-" * 50)
        
        while True:
            try:
                query = input("\n❓ Ваш вопрос: ").strip()
                
                if query.lower() in ['quit', 'exit', 'выход']:
                    print("👋 До свидания!")
                    break
                
                if not query:
                    continue
                
                # Выбор техники
                print("\nВыберите технику промптинга:")
                print("1. base (базовая)")
                print("2. few_shot (few-shot)")
                print("3. chain_of_thought (chain-of-thought)")
                
                choice = input("Введите номер (1-3) или Enter для базовой: ").strip()
                
                technique_map = {
                    "1": "base",
                    "2": "few_shot", 
                    "3": "chain_of_thought"
                }
                
                technique = technique_map.get(choice, "base")
                
                print(f"\n🔍 Поиск информации...")
                result = self.generate_response(query, technique)
                
                print(f"\n🤖 Ответ ({technique}):")
                print("-" * 40)
                print(result["response"])
                print("-" * 40)
                
                print(f"\n📚 Источники ({result['num_sources']}):")
                for i, source in enumerate(result["sources"], 1):
                    print(f"  {i}. {source['source']} ({source['category']})")
                
            except KeyboardInterrupt:
                print("\n👋 До свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")


def main():
    """Основная функция"""
    # Загрузка переменных окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    # Конфигурация
    config = RAGConfig()
    
    # Создание и запуск бота
    bot = RAGBot(config)
    bot.interactive_mode()


if __name__ == "__main__":
    main()
