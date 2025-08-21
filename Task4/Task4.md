# Task 4: RAG-бот (краткое руководство)

## Что это
- RAG-бот на OpenAI GPT-3.5-turbo + ChromaDB + all-mpnet-base-v2.
- Требуется готовый индекс в `Task3/chroma_db` и `OPENAI_API_KEY` в `.env`.

## Быстрый старт
- Docker: `cd Task4 && ./run.sh` → открыть `http://localhost:8501`
- Локально: `pip install -r Task4/requirements.txt && cp Task4/env_example.txt Task4/.env && cd Task4 && streamlit run web_interface.py`

## Использование
- Веб-интерфейс: введите вопрос, выберите технику промптинга: `base`, `few_shot`, `chain_of_thought`.
- Через код:
```python
from rag_bot import RAGBot, RAGConfig
bot = RAGBot(RAGConfig())
res = bot.generate_response("Кто такой Xarn Velgor?", technique="chain_of_thought")
print(res["response"])
```

## Техники промптинга (кратко)
- `base`: кратко по контексту.
- `few_shot`: примеры в шаблоне улучшают форму ответа.
- `chain_of_thought`: пошаговое рассуждение перед итоговым ответом.

Примечание: для CoT выберите технику `chain_of_thought` — модель сначала рассуждает, затем дает ответ.

## Конфигурация
- `.env`: `OPENAI_API_KEY=...`
- Индекс: `Task3/chroma_db` (Docker монтирует `../Task3/chroma_db` → `/app/chroma_db`).



## Скриншоты
- Примеры работы бота находятся в папке `Task4/screenshots/`.


