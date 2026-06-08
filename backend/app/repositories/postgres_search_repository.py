from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.utils.text_processing import normalize_text


class PostgresSearchRepository:
    HEADLINE_OPTIONS = "StartSel=<mark>, StopSel=</mark>, MaxWords=35, MinWords=10, ShortWord=3"

    def __init__(self):
        self.document_repository = DocumentRepository()

    def search_full_text(
        self,
        db: Session,
        *,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if db.bind and db.bind.dialect.name == "postgresql":
            return self._search_postgresql(db, query=query, limit=limit, filters=filters or {})
        return self._search_fallback(db, query=query, limit=limit, filters=filters or {})

    def _search_postgresql(
        self,
        db: Session,
        *,
        query: str,
        limit: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        clauses = [
            "d.ativo IS TRUE",
            "h.versao_ativa IS TRUE",
            "h.search_vector @@ websearch_to_tsquery(ifesdoc_search_config(), :query)",
        ]
        params: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "headline_options": self.HEADLINE_OPTIONS,
        }

        if filters.get("category"):
            clauses.append("lower(c.nome_categoria) = lower(:category)")
            params["category"] = filters["category"]
        if filters.get("document_type"):
            clauses.append(
                """
                (
                    lower(d.tipo) LIKE lower(:document_type_like)
                    OR lower(coalesce(m.tipo_documento, '')) LIKE lower(:document_type_like)
                    OR lower(coalesce(h.nome_arquivo_original, '')) LIKE lower(:document_type_like)
                )
                """
            )
            params["document_type_like"] = f"%{filters['document_type']}%"
        if filters.get("author"):
            clauses.append("lower(coalesce(m.autor, '')) LIKE lower(:author_like)")
            params["author_like"] = f"%{filters['author']}%"
        if filters.get("date_from"):
            clauses.append("d.data_publicacao >= :date_from")
            params["date_from"] = filters["date_from"]
        if filters.get("date_to"):
            clauses.append("d.data_publicacao <= :date_to")
            params["date_to"] = filters["date_to"]
        if filters.get("year"):
            clauses.append("EXTRACT(YEAR FROM d.data_publicacao) = :year")
            params["year"] = int(filters["year"])

        sql = text(
            f"""
            SELECT
                d.cod_documento AS document_id,
                d.titulo AS title,
                d.tipo AS type,
                d.data_publicacao AS document_date,
                d.criado_em AS uploaded_at,
                c.nome_categoria AS category,
                h.numero_versao AS version,
                h.nome_arquivo_original AS file_name,
                h.mime_type AS mime_type,
                h.tamanho_bytes AS size_bytes,
                h.texto_extraido AS content,
                h.ocr_executado AS ocr_executado,
                h.ocr_status AS ocr_status,
                coalesce(m.autor, u.nome) AS author_name,
                coalesce(m.tipo_documento, d.tipo) AS document_type,
                ts_rank_cd(h.search_vector, websearch_to_tsquery(ifesdoc_search_config(), :query)) AS score,
                ts_headline(
                    ifesdoc_search_config(),
                    coalesce(h.texto_extraido, d.titulo, ''),
                    websearch_to_tsquery(ifesdoc_search_config(), :query),
                    :headline_options
                ) AS snippet
            FROM historico_documento h
            JOIN documento d ON d.cod_documento = h.cod_documento
            JOIN categoria_documento c ON c.cod_categoria = d.cod_categoria
            JOIN usuario u ON u.cod_usuario = d.cod_usuario_criador
            LEFT JOIN documento_metadado m ON m.cod_documento = d.cod_documento
            WHERE {' AND '.join(clauses)}
            ORDER BY score DESC, d.cod_documento ASC
            LIMIT :limit
            """
        )
        return [self._row_to_result(row._mapping) for row in db.execute(sql, params).all()]

    def _search_fallback(
        self,
        db: Session,
        *,
        query: str,
        limit: int,
        filters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        terms = [term for term in normalize_text(query).split(" ") if term]
        if not terms:
            return []

        results = []
        for payload in self.document_repository.list_active_document_payloads(db):
            if not self._matches_filters(payload, filters):
                continue
            searchable = normalize_text(
                " ".join(
                    str(value)
                    for value in (
                        payload.get("title"),
                        payload.get("content"),
                        payload.get("author_name"),
                        payload.get("category"),
                        payload.get("document_type"),
                        payload.get("file_name"),
                    )
                    if value
                )
            )
            matched_terms = [term for term in terms if term in searchable]
            if not matched_terms:
                continue
            score = sum(searchable.count(term) for term in matched_terms)
            results.append(
                {
                    "document_id": payload["id"],
                    "title": payload["title"],
                    "type": payload["type"],
                    "document_type": payload["document_type"],
                    "category": payload["category"],
                    "document_date": payload["document_date"],
                    "uploaded_at": payload["uploaded_at"],
                    "version": payload["version"],
                    "file_name": payload["file_name"],
                    "mime_type": payload["mime_type"],
                    "size_bytes": payload["size_bytes"],
                    "content": payload["content"],
                    "ocr_executado": payload.get("ocr_executado", False),
                    "ocr_status": payload.get("ocr_status"),
                    "author_name": payload["author_name"],
                    "score": float(score),
                    "snippet": self._fallback_snippet(payload.get("content") or payload.get("title") or "", matched_terms),
                    "matched_terms": matched_terms,
                }
            )
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def _row_to_result(self, row) -> dict[str, Any]:
        return {
            "document_id": int(row["document_id"]),
            "title": row["title"] or "",
            "type": row["type"] or "",
            "document_type": row["document_type"] or row["type"] or "",
            "category": row["category"] or "",
            "document_date": row["document_date"],
            "uploaded_at": row["uploaded_at"],
            "version": int(row["version"] or 1),
            "file_name": row["file_name"] or "",
            "mime_type": row["mime_type"] or "",
            "size_bytes": int(row["size_bytes"] or 0),
            "content": row["content"] or "",
            "ocr_executado": bool(row["ocr_executado"]),
            "ocr_status": row["ocr_status"],
            "author_name": row["author_name"] or "",
            "score": float(row["score"] or 0.0),
            "snippet": row["snippet"] or "",
            "matched_terms": [],
        }

    def _matches_filters(self, payload: dict, filters: dict[str, Any]) -> bool:
        if filters.get("category") and normalize_text(payload.get("category")) != normalize_text(filters["category"]):
            return False
        if filters.get("document_type"):
            document_type = normalize_text(filters["document_type"])
            values = (
                payload.get("type"),
                payload.get("document_type"),
                payload.get("file_name"),
                payload.get("mime_type"),
            )
            if not any(document_type in normalize_text(value or "") for value in values):
                return False
        if filters.get("author") and normalize_text(filters["author"]) not in normalize_text(payload.get("author_name")):
            return False

        effective_date = payload.get("document_date") or payload.get("uploaded_at")
        if effective_date:
            if isinstance(effective_date, str):
                effective_date = datetime.fromisoformat(effective_date)
            if filters.get("date_from") and effective_date.replace(tzinfo=None) < filters["date_from"].replace(tzinfo=None):
                return False
            if filters.get("date_to") and effective_date.replace(tzinfo=None) > filters["date_to"].replace(tzinfo=None):
                return False
            if filters.get("year") and effective_date.year != int(filters["year"]):
                return False
        return True

    def _fallback_snippet(self, content: str, terms: list[str]) -> str:
        text_content = re.sub(r"\s+", " ", content or "").strip()
        if not text_content:
            return ""
        normalized_content = normalize_text(text_content)
        first_match = min(
            [normalized_content.find(term) for term in terms if normalized_content.find(term) >= 0],
            default=0,
        )
        start = max(first_match - 80, 0)
        excerpt = text_content[start:start + 240]
        for term in sorted(terms, key=len, reverse=True):
            excerpt = re.sub(
                rf"({re.escape(term)})",
                r"<mark>\1</mark>",
                excerpt,
                flags=re.IGNORECASE,
            )
        return ("... " if start else "") + excerpt
