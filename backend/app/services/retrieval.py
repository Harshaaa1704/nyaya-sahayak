import re


STOP_WORDS = {
    "about", "after", "also", "and", "are", "can", "does", "for", "from",
    "how", "into", "its", "that", "the", "this", "what", "when", "where",
    "which", "with", "would", "your",
}


def retrieve(chunks: list[dict], query: str, limit: int = 5) -> list[dict]:
    terms = {
        term for term in re.findall(r"[a-zA-Z0-9]{3,}", query.lower())
        if term not in STOP_WORDS
    }
    scored: list[tuple[int, dict]] = []
    for chunk in chunks:
        words = set(re.findall(r"[a-zA-Z0-9]{3,}", chunk["text"].lower()))
        score = sum(1 for term in terms if term in words)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]
