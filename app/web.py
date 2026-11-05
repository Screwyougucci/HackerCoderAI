"""Public-web research helpers. Search only; no target scanning or form submission."""
from ddgs import DDGS

def search_web(query: str, max_results: int = 5) -> list[dict[str, str]]:
    query = " ".join(query.split())[:400]
    if not query:
        return []
    results = DDGS().text(query, max_results=max(1, min(max_results, 8)))
    cleaned = []
    for item in results or []:
        url = str(item.get("href", ""))
        if not url.startswith("https://"):
            continue
        cleaned.append({
            "title": str(item.get("title", "Untitled"))[:300],
            "url": url[:1500],
            "snippet": str(item.get("body", ""))[:1200],
        })
    return cleaned
