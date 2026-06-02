from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod

from app.utils.text_processing import normalize_text, preprocess_for_indexing


class EmbeddingAdapter(ABC):
    model_name = "base"

    @abstractmethod
    def encode_text(self, text: str) -> list[float]:
        pass

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.encode_text(text) for text in texts]


class MockEmbeddingAdapter(EmbeddingAdapter):
    model_name = "mock-hashing-v1"

    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def encode_text(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = preprocess_for_indexing(text)["tokens"]
        normalized_text = normalize_text(text)

        features = list(tokens)
        features.extend(self._char_ngrams(normalized_text, size=3))
        if not features and normalized_text:
            features = normalized_text.split()

        for feature in features:
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    def _char_ngrams(self, text: str, *, size: int) -> list[str]:
        compact = text.replace(" ", "_")
        if len(compact) < size:
            return [compact] if compact else []
        return [compact[index:index + size] for index in range(len(compact) - size + 1)]


class SentenceTransformerEmbeddingAdapter(EmbeddingAdapter):
    def __init__(
        self,
        model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Use MockEmbeddingAdapter "
                "or install the dependency to enable real semantic embeddings."
            ) from exc

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)

    def encode_text(self, text: str) -> list[float]:
        embedding = self._model.encode(text or "", normalize_embeddings=True)
        return [float(value) for value in embedding.tolist()]

    def encode_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True)
        return [[float(value) for value in embedding.tolist()] for embedding in embeddings]
