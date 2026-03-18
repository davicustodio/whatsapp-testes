import asyncio
from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    async def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            return []

        def _encode() -> list[float]:
            model = self._get_model()
            vector = model.encode(text, normalize_embeddings=True)
            return vector.tolist()

        return await asyncio.to_thread(_encode)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        valid_texts = [text for text in texts if text.strip()]
        if not valid_texts:
            return [[] for _ in texts]

        def _encode_many() -> list[list[float]]:
            model = self._get_model()
            vectors = model.encode(valid_texts, normalize_embeddings=True)
            return vectors.tolist()

        encoded = await asyncio.to_thread(_encode_many)
        iterator = iter(encoded)
        result: list[list[float]] = []
        for text in texts:
            result.append(next(iterator) if text.strip() else [])
        return result


@lru_cache
def get_embedding_service() -> EmbeddingService:
    settings = get_settings()
    return EmbeddingService(settings.embedding_model)
