from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from app.core.logging import logger


class OCRAdapter:
    def extract_text_from_pdf(
        self,
        file_path: str,
        language: str = "por",
        dpi: int = 200,
        max_pages: int | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        started_at = time.perf_counter()
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return self._failure(
                started_at,
                language=language,
                dpi=dpi,
                error="Arquivo PDF não encontrado para OCR.",
            )

        try:
            import pytesseract
            from pdf2image import convert_from_path
        except ModuleNotFoundError as exc:
            logger.warning("Dependência de OCR ausente: %s", exc)
            return self._failure(
                started_at,
                language=language,
                dpi=dpi,
                error="Dependências de OCR não instaladas.",
            )

        try:
            images = convert_from_path(
                str(path),
                dpi=dpi,
                first_page=1,
                last_page=max_pages if max_pages and max_pages > 0 else None,
            )
            page_texts: list[str] = []
            for index, image in enumerate(images, start=1):
                remaining_timeout = self._remaining_timeout(started_at, timeout_seconds)
                if timeout_seconds is not None and remaining_timeout <= 0:
                    raise TimeoutError("Tempo limite de OCR excedido.")
                options = {"lang": language}
                if timeout_seconds is not None:
                    options["timeout"] = remaining_timeout
                text = pytesseract.image_to_string(image, **options)
                normalized_text = (text or "").strip()
                if normalized_text:
                    page_texts.append(f"--- Página {index} ---\n{normalized_text}")
            full_text = "\n\n".join(page_texts).strip()
            processing_time_ms = int((time.perf_counter() - started_at) * 1000)
            logger.info(
                "OCR concluído para %s: %s página(s), %s caractere(s), %sms",
                path.name,
                len(images),
                len(full_text),
                processing_time_ms,
            )
            return {
                "text": full_text,
                "pages_processed": len(images),
                "language": language,
                "dpi": dpi,
                "success": True,
                "error": None,
                "processing_time_ms": processing_time_ms,
            }
        except Exception as exc:
            logger.warning("OCR falhou para %s: %s", path, exc)
            return self._failure(
                started_at,
                language=language,
                dpi=dpi,
                error=str(exc),
            )

    def _failure(self, started_at: float, *, language: str, dpi: int, error: str) -> dict[str, Any]:
        return {
            "text": "",
            "pages_processed": 0,
            "language": language,
            "dpi": dpi,
            "success": False,
            "error": error,
            "processing_time_ms": int((time.perf_counter() - started_at) * 1000),
        }

    def _remaining_timeout(self, started_at: float, timeout_seconds: int | None) -> int:
        if timeout_seconds is None:
            return 0
        elapsed = int(time.perf_counter() - started_at)
        return max(timeout_seconds - elapsed, 0)
