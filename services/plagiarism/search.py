import json
import os
import urllib.parse
import urllib.request
from typing import Any

from services.plagiarism.models import SourceCandidate


def _request_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AI-SCREENING/0.1",
            "x-goog-api-key": os.environ["GEMINI_API_KEY"],
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read())


def google_search_sources(query: str, limit: int = 5) -> list[SourceCandidate]:
    """Discover public web sources using Gemini Google Search grounding.

    The search provider returns citation URLs; it does not make a plagiarism
    determination. Attribution and text comparison happen in separate stages.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for Google Search grounding.")

    model = os.getenv("AI_SCREENING_GEMINI_MODEL", "gemini-3.8-flash")
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model, safe='')}:generateContent"
    prompt = (
        "Find public web sources that may contain this exact or closely related passage. "
        "Return a concise response that cites the most relevant source pages. "
        "Do not decide whether plagiarism occurred. Search query: " + query[:2000]
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "tools": [{"google_search": {}}],
    }
    response = _request_json(endpoint, payload)
    candidates: list[SourceCandidate] = []
    seen: set[str] = set()

    metadata = response.get("candidates", [{}])[0].get("groundingMetadata", {})
    chunks = metadata.get("groundingChunks", [])
    queries = metadata.get("webSearchQueries", [])
    search_query = queries[0] if queries else query

    for index, chunk in enumerate(chunks):
        web = chunk.get("web", {})
        url = web.get("uri", "")
        title = web.get("title", "") or url
        if not url or url in seen:
            continue
        seen.add(url)
        candidates.append(
            SourceCandidate(
                source_id=f"google:{index + 1}",
                title=title,
                url=url,
                search_query=search_query,
            )
        )
        if len(candidates) >= limit:
            break

    return candidates
