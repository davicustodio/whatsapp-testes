from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.instance import Instance
from app.services.embedding_service import EmbeddingService
from app.services.llm_service import LLMService


class SearchService:
    def __init__(
        self,
        session: AsyncSession,
        embedding_service: EmbeddingService,
        llm_service: LLMService,
    ) -> None:
        self.session = session
        self.embedding_service = embedding_service
        self.llm_service = llm_service

    async def semantic_search(
        self,
        instance_name: str,
        query: str,
        limit: int = 10,
    ) -> tuple[list[dict], str | None]:
        instance_id = await self._resolve_instance_id(instance_name)
        if not instance_id:
            return [], None

        query_vector = await self.embedding_service.embed_text(query)
        if not query_vector:
            return [], None

        vector_literal = "[" + ",".join(f"{float(value):.8f}" for value in query_vector) + "]"
        stmt = text(
            """
            WITH scoped_messages AS MATERIALIZED (
                SELECT id, remote_jid, content, timestamp, embedding
                FROM messages
                WHERE instance_id = :instance_id
                  AND embedding IS NOT NULL
            )
            SELECT
                id,
                remote_jid,
                content,
                timestamp,
                (embedding <=> CAST(:query_vector AS vector)) AS distance
            FROM scoped_messages
            ORDER BY distance ASC
            LIMIT :limit_value
            """
        )
        rows = (
            await self.session.execute(
                stmt,
                {
                    "query_vector": vector_literal,
                    "instance_id": instance_id,
                    "limit_value": limit,
                },
            )
        ).mappings().all()
        results = [
            {
                "message_id": row["id"],
                "remote_jid": row["remote_jid"],
                "content": row["content"],
                "timestamp": row["timestamp"],
                "score": float(max(0.0, 1 - row["distance"])),
            }
            for row in rows
        ]

        rag_answer = await self._build_rag_answer(query=query, results=results)
        return results, rag_answer

    async def _resolve_instance_id(self, instance_name: str) -> str | None:
        result = await self.session.execute(
            select(Instance.id).where(Instance.instance_name == instance_name)
        )
        return result.scalar_one_or_none()

    async def _build_rag_answer(self, query: str, results: list[dict]) -> str | None:
        if not results:
            return "Nenhuma mensagem relevante encontrada para esse assunto."

        context_lines: list[str] = []
        for index, item in enumerate(results, start=1):
            context_lines.append(
                (
                    f"{index}. [{item['timestamp']}] "
                    f"{item['remote_jid']}: {item['content'] or '(sem texto)'} "
                    f"(score={item['score']:.4f})"
                )
            )

        prompt = (
            "Voce recebeu mensagens recuperadas por busca semantica em WhatsApp.\n"
            "Responda em Portugues BR com um resumo objetivo e os principais achados.\n\n"
            f"Pergunta do usuario: {query}\n\n"
            "Mensagens recuperadas:\n"
            + "\n".join(context_lines)
        )
        completion = await self.llm_service.chat_completion(prompt)
        if completion:
            return completion
        return "Resumo LLM indisponivel no momento. Consulte os resultados semanticos retornados abaixo."
