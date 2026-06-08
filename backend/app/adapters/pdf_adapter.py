from __future__ import annotations

import io

from app.adapters.document_adapter import DocumentAdapter
from app.exceptions.document_exceptions import DocumentValidationException


class PdfDocumentAdapter(DocumentAdapter):
    extension = "pdf"
    mime_type = "application/pdf"

    def validate_integrity(self, content: bytes) -> None:
        if not content.startswith(b"%PDF"):
            raise DocumentValidationException("PDF inválido: cabeçalho não reconhecido.")
        if b"%%EOF" not in content[-2048:]:
            raise DocumentValidationException("PDF inválido: final do arquivo corrompido.")

    def extract_text(self, content: bytes) -> str:
        try:
            import pdfplumber

            with pdfplumber.open(io.BytesIO(content)) as pdf:
                pages = [(page.extract_text() or "").strip() for page in pdf.pages]
        except ModuleNotFoundError as exc:
            raise DocumentValidationException(
                "Extração de PDF indisponível: dependência pdfplumber não instalada."
            ) from exc
        except Exception as exc:
            raise DocumentValidationException("Falha ao extrair texto do PDF.") from exc

        extracted_text = "\n\n".join(page for page in pages if page).strip()
        return extracted_text[:200000]
