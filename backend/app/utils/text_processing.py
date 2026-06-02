import re
import unicodedata

STOPWORDS_PT_BR = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "entre", "era", "essa", "esse", "esta", "este", "eu", "foi",
    "ha", "isso", "isto", "ja", "la", "mais", "mas", "na", "nas", "no",
    "nos", "o", "os", "ou", "para", "pela", "pelas", "pelo", "pelos", "por",
    "que", "se", "sem", "ser", "sobre", "sua", "suas", "seu", "seus", "tem", "uma",
    "umas", "um", "uns",
}


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def tokenize_text(text: str) -> list[str]:
    if not text:
        return []
    return [token for token in text.split(" ") if token]


def remove_stopwords(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in STOPWORDS_PT_BR]


def preprocess_for_indexing(text: str) -> dict:
    normalized_text = normalize_text(text)
    raw_tokens = tokenize_text(normalized_text)
    filtered_tokens = remove_stopwords(raw_tokens)

    positions_by_term: dict[str, list[int]] = {}
    for position, token in enumerate(filtered_tokens):
        positions_by_term.setdefault(token, []).append(position)

    return {
        "normalized_text": normalized_text,
        "processed_text": " ".join(filtered_tokens),
        "raw_tokens": raw_tokens,
        "tokens": filtered_tokens,
        "positions_by_term": positions_by_term,
        "term_count": len(positions_by_term),
        "token_count": len(filtered_tokens),
    }
