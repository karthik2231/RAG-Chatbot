from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path

import faiss
import fitz
import httpx
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import Settings


@dataclass
class TextChunk:
    text: str
    page_number: int
    chunk_index: int
    document_id: int
    document_name: str


class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> list[str]:
        if not text.strip():
            return []

        # Prefer a natural boundary before the size limit. Moving the next
        # window back by ``chunk_overlap`` keeps relevant context in both
        # neighbouring chunks; a character boundary is the final fallback.
        chunks: list[str] = []
        start = 0
        overlap = min(max(self.chunk_overlap, 0), self.chunk_size - 1)
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                boundary = -1
                for separator in self.separators[:-1]:
                    position = text.rfind(separator, start + 1, end + 1)
                    if position > boundary:
                        boundary = position + len(separator)
                if boundary > start:
                    end = boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(text):
                break
            start = max(end - overlap, start + 1)

        return chunks


class DocumentProcessor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    def extract_text_from_pdf(self, file_path: Path) -> list[tuple[int, str]]:
        pages: list[tuple[int, str]] = []
        with fitz.open(file_path) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                if text.strip():
                    pages.append((page_num, text))
        return pages

    def create_chunks(
        self, pages: list[tuple[int, str]], document_id: int, document_name: str
    ) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        chunk_index = 0
        for page_number, page_text in pages:
            for text in self.splitter.split_text(page_text):
                chunks.append(
                    TextChunk(
                        text=text,
                        page_number=page_number,
                        chunk_index=chunk_index,
                        document_id=document_id,
                        document_name=document_name,
                    )
                )
                chunk_index += 1
        return chunks


class EmbeddingService:
    _model: SentenceTransformer | None = None

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def model(self) -> SentenceTransformer:
        if EmbeddingService._model is None:
            EmbeddingService._model = SentenceTransformer(self.settings.embedding_model)
        return EmbeddingService._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return np.array(embeddings, dtype=np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        embedding = self.model.encode([query], show_progress_bar=False, convert_to_numpy=True)
        return np.array(embedding[0], dtype=np.float32)


class VectorStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.index_dir = settings.faiss_index_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def _user_index_path(self, user_id: int) -> Path:
        return self.index_dir / f"user_{user_id}.index"

    def _user_metadata_path(self, user_id: int) -> Path:
        return self.index_dir / f"user_{user_id}.meta"

    def add_chunks(self, user_id: int, chunks: list[TextChunk], embeddings: np.ndarray) -> None:
        if not chunks:
            return

        index_path = self._user_index_path(user_id)
        meta_path = self._user_metadata_path(user_id)
        dimension = embeddings.shape[1]

        if index_path.exists() and meta_path.exists():
            index = faiss.read_index(str(index_path))
            with meta_path.open("rb") as f:
                metadata: list[dict] = pickle.load(f)
        else:
            index = faiss.IndexFlatIP(dimension)
            metadata = []

        faiss.normalize_L2(embeddings)
        index.add(embeddings)

        for chunk in chunks:
            metadata.append(
                {
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "document_id": chunk.document_id,
                    "document_name": chunk.document_name,
                }
            )

        faiss.write_index(index, str(index_path))
        with meta_path.open("wb") as f:
            pickle.dump(metadata, f)

    def search(
        self, user_id: int, query_embedding: np.ndarray, top_k: int, document_ids: list[int] | None = None
    ) -> list[dict]:
        index_path = self._user_index_path(user_id)
        meta_path = self._user_metadata_path(user_id)

        if not index_path.exists() or not meta_path.exists():
            return []

        index = faiss.read_index(str(index_path))
        with meta_path.open("rb") as f:
            metadata: list[dict] = pickle.load(f)

        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)

        k = min(top_k * 3, index.ntotal) if document_ids else min(top_k, index.ntotal)
        if k == 0:
            return []

        scores, indices = index.search(query, k)
        results: list[dict] = []

        for score, idx in zip(scores[0], indices[0], strict=False):
            if idx < 0 or idx >= len(metadata):
                continue
            item = metadata[idx]
            if document_ids and item["document_id"] not in document_ids:
                continue
            results.append({**item, "score": float(score)})
            if len(results) >= top_k:
                break

        return results

    def remove_document(self, user_id: int, document_id: int) -> None:
        index_path = self._user_index_path(user_id)
        meta_path = self._user_metadata_path(user_id)

        if not index_path.exists() or not meta_path.exists():
            return

        with meta_path.open("rb") as f:
            metadata: list[dict] = pickle.load(f)

        remaining = [m for m in metadata if m["document_id"] != document_id]
        if len(remaining) == len(metadata):
            return

        if not remaining:
            index_path.unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            return

        embedding_service = EmbeddingService(self.settings)
        texts = [item["text"] for item in remaining]
        embeddings = embedding_service.embed_texts(texts)

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(embeddings)
        index.add(embeddings)

        faiss.write_index(index, str(index_path))
        with meta_path.open("wb") as f:
            pickle.dump(remaining, f)


class RAGService:
    SYSTEM_PROMPT = """You are an expert AI assistant that answers questions based strictly on the provided document context.
Rules:
1. Only use information from the context to answer questions.
2. If the answer is not in the context, say you cannot find that information in the uploaded documents.
3. Be concise, accurate, and cite page numbers when referencing specific information.
4. Maintain conversation continuity when prior messages are provided.
5. Answer in no more than four short sentences unless the user asks for detail."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)
        self.vector_store = VectorStore(settings)

    def build_prompt(self, query: str, context_chunks: list[dict], history: list[dict]) -> str:
        context_text = "\n\n".join(
            f"[Document: {chunk['document_name']}, Page {chunk['page_number']}]\n{chunk['text']}"
            for chunk in context_chunks
        )

        history_text = "\n".join(f"{msg['role'].upper()}: {msg['content']}" for msg in history[-6:])

        return f"""{self.SYSTEM_PROMPT}

Conversation History:
{history_text or 'None'}

Context:
{context_text or 'No relevant context found.'}

User Question:
{query}

Answer:"""

    async def _generate_answer_ollama(self, prompt: str) -> str:
        ollama_url = self.settings.ollama_url.strip().rstrip("/")
        if not ollama_url:
            raise ValueError(
                "OLLAMA_URL is not configured. Set a valid OLLAMA_URL in your .env file and restart the backend."
            )

        payload = {
            "model": self.settings.ollama_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.settings.ollama_keep_alive,
            "options": {
                "num_predict": self.settings.ollama_num_predict,
                "num_ctx": self.settings.ollama_num_ctx,
                "temperature": 0.2,
            },
        }

        try:
            # A cold Ollama model load can take well over 30 seconds on CPU.
            # Keep this comfortably above the initial-load time so the first
            # chat request does not fail while Ollama is preparing the model.
            async with httpx.AsyncClient(timeout=self.settings.ollama_timeout_seconds) as client:
                response = await client.post(f"{ollama_url}/api/generate", json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ValueError(f"Ollama API error: {exc}") from exc

        if isinstance(data, dict):
            if text := data.get("text"):
                return text.strip()
            if response_text := data.get("response"):
                return response_text.strip()
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and isinstance(first_choice.get("text"), str):
                    return first_choice["text"].strip()
            results = data.get("results")
            if isinstance(results, list) and results:
                first_result = results[0]
                if isinstance(first_result, dict):
                    if text := first_result.get("text"):
                        return text.strip()
                    if output := first_result.get("output"):
                        return output.strip()

        raise ValueError("Ollama returned an unexpected response format.")

    async def generate_answer(self, prompt: str) -> str:
        if self.settings.llm_provider.lower() != "ollama":
            raise ValueError(
                f"Unsupported LLM provider: {self.settings.llm_provider}. Only 'ollama' is supported."
            )
        return await self._generate_answer_ollama(prompt)

    async def query(
        self,
        user_id: int,
        query: str,
        document_ids: list[int],
        history: list[dict],
    ) -> tuple[str, list[dict]]:
        query_embedding = self.embedding_service.embed_query(query)
        context_chunks = self.vector_store.search(
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=self.settings.top_k_results,
            document_ids=document_ids or None,
        )

        prompt = self.build_prompt(query, context_chunks, history)
        answer = await self.generate_answer(prompt)

        sources = [
            {
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "page_number": chunk["page_number"],
                "score": chunk["score"],
                "excerpt": chunk["text"][:200],
            }
            for chunk in context_chunks
        ]
        return answer, sources


def serialize_sources(sources: list[dict]) -> str:
    return json.dumps(sources)
