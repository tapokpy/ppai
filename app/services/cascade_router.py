from app.config import settings
from app.services import business_rules, llm_cloud, llm_local, rag

try:
    from langfuse import Langfuse

    _langfuse = (
        Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
        if settings.langfuse_public_key and settings.langfuse_secret_key
        else None
    )
except ImportError:
    _langfuse = None

SYSTEM_PROMPT = (
    "Ты — ассистент компании «ПридПром», специализирующейся на светодиодных "
    "экранах (продажа, монтаж, обслуживание)."
)

# Порог длины ответа локальной модели, при котором он считается "уверенным".
# В README точный критерий не описан — это временная эвристика для Этапа 1,
# в Этапе 3 (RAG Quality) её планируется заменить на реранкинг/скоринг.
LOCAL_CONFIDENCE_MIN_LENGTH = 20


async def route_query(query: str, category: str = "general") -> dict:
    trace = _langfuse.trace(name="cascade_router", input=query) if _langfuse else None

    rules_text = await business_rules.get_active_rules_text(category)
    system_prompt = SYSTEM_PROMPT
    if rules_text:
        system_prompt = f"{SYSTEM_PROMPT}\n\nБизнес-правила, которые нужно учитывать:\n{rules_text}"

    documents, similarity = rag.search(query)

    if documents and similarity >= settings.rag_score_threshold:
        context = "\n\n".join(documents)
        prompt = f"Контекст:\n{context}\n\nВопрос: {query}"
        answer = await llm_local.generate(prompt, system=system_prompt)
        source = "rag"
    else:
        answer = await llm_local.generate(query, system=system_prompt)
        if len(answer.strip()) >= LOCAL_CONFIDENCE_MIN_LENGTH:
            source = "local"
        else:
            answer = await llm_cloud.generate(query, system=system_prompt)
            source = "cloud"

    if trace:
        trace.update(output=answer, metadata={"source": source, "rag_similarity": similarity})

    return {"answer": answer, "source": source}
