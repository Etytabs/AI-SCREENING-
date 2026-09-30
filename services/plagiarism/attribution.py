import re
import urllib.request
from html import unescape
from urllib.parse import urlparse

from services.plagiarism.models import SourceAttribution


_META_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\']([^"\']+)["\'][^>]+content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)


def _metadata(url: str) -> dict[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "AI-SCREENING/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(600_000).decode("utf-8", errors="ignore")
    return {key.lower(): unescape(value).strip() for key, value in _META_RE.findall(raw)}


def resolve_attribution(url: str, fallback_title: str = "") -> SourceAttribution:
    try:
        meta = _metadata(url)
    except Exception:
        return SourceAttribution(
            title=fallback_title,
            source_url=url,
            attribution_basis="search result only",
            metadata_confidence=0.25 if fallback_title else 0.1,
        )

    authors = []
    for key in ("citation_author", "author", "article:author", "dc.creator"):
        if meta.get(key):
            authors.extend(part.strip() for part in re.split(r";|,\s*(?=[A-Z])", meta[key]) if part.strip())
            if authors:
                break

    publisher = meta.get("citation_publisher") or meta.get("og:site_name") or meta.get("publisher")
    published = (
        meta.get("citation_publication_date")
        or meta.get("article:published_time")
        or meta.get("date")
        or meta.get("dc.date")
    )
    title = meta.get("citation_title") or meta.get("og:title") or fallback_title
    host = urlparse(url).netloc
    return SourceAttribution(
        title=title,
        authors=tuple(dict.fromkeys(authors)),
        publisher=publisher or host or None,
        published_date=published,
        source_url=url,
        attribution_basis="page metadata",
        metadata_confidence=0.8 if authors or publisher else 0.55,
    )
