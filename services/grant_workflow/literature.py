"""Published-literature lookup used by the plagiarism (text similarity) check.

The check compares a proposal against work that is already published. Candidate works are
retrieved from OpenAlex with queries derived from the proposal itself, so only text the
applicant actually wrote drives the search. A failed or unconfigured lookup is reported as
missing coverage, never as "nothing was found".
"""
import logging
import os
import re
from collections import Counter
from dataclasses import dataclass, field

from ml.evidence.state import RunState
from services.research_sources.connectors import (
    openalex_api_key,
    openalex_contact,
    search_openalex,
)
from services.research_sources.models import ResearchRecord
from services.sources.registry import SourceAccessStatus

logger = logging.getLogger(__name__)

SOURCE_ID = "openalex"
SOURCE_NAME = "OpenAlex published literature"
MAX_QUERIES = 6
RESULTS_PER_QUERY = 30
MIN_ABSTRACT_WORDS = 25

_KEYWORD_LINE = re.compile(r"^\s*(?:key\s?words?|index terms)\s*[:\-–]\s*(.+)$", re.I | re.M)
_TITLE_NOISE = re.compile(r"\s*\((?:[^()]{0,60})\)\s*$")
# Running headers and footers a PDF repeats on every page are not the title.
_PAGE_FURNITURE = re.compile(r"(\|\s*page\s*\d+|^page\s+\d+|^\d+\s*$)", re.I)
_TITLE_STOP = re.compile(
    r"^\s*(?:\d+[.)]|abstract|introduction|summary|background|key\s?words?|index terms|"
    r"contents|table of|title\s*:|applicant\s*:|by\s+)",
    re.I,
)
_SECTION_BREAK = re.compile(r"(?m)^\s*\d{1,2}\.\s+[A-Z]")
_QUERY_STOP = frozenset("""
a an and are as at be because been being by can could did do does for from had has have how if in
into is it its may might more most must no not of on or our shall should so such than that the
their them then there these they this those through to under up used using was we were what when
where whether which while who will with within would you your per any all least one two other
also both only each about project proposal research study work approach methodology objective
objectives aim aims develop development use planned plan activity activities outcome outcomes
result results funding grant applicant application institution duration months year years
document purpose background summary
""".split())


@dataclass(frozen=True)
class LiteratureSearch:
    """Outcome of one literature lookup, including why coverage may be incomplete."""

    records: tuple[ResearchRecord, ...] = ()
    state: RunState = RunState.COMPLETE
    message: str = ""
    queries: tuple[str, ...] = ()
    errors: tuple[str, ...] = field(default=())


def _clean(text: str) -> str:
    return " ".join(text.split())


def _keyword_query(text: str) -> str | None:
    match = _KEYWORD_LINE.search(text)
    if not match:
        return None
    terms = [_clean(term) for term in re.split(r"[;,]", match.group(1)) if len(_clean(term)) > 2]
    return " ".join(terms[:8]) or None


def _term_query(text: str, limit: int = 8) -> str | None:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", text.lower()) if w not in _QUERY_STOP]
    if len(words) < limit:
        return None
    common = [word for word, _ in Counter(words).most_common(limit)]
    return " ".join(common) or None


def body_text(text: str) -> str:
    """The document minus the furniture a PDF repeats on every page.

    A running header counted once per page outweighs the real subject matter and
    poisons every frequency-based query, so drop it before any term counting.
    """
    lines = [line for line in text.splitlines() if not _PAGE_FURNITURE.search(line.strip())]
    repeated = Counter(line.strip() for line in lines if line.strip())
    return "\n".join(line for line in lines if repeated[line.strip()] < 3)


def _section_queries(text: str, limit: int = 3) -> list[str]:
    """One query per substantial section.

    A single bag of words over a whole proposal is dominated by its general topic;
    the sentences that describe prior work sit in one section, so query sections
    separately to give that wording its own chance to retrieve a source.
    """
    sections = [s for s in _SECTION_BREAK.split(text) if len(s.split()) >= 60]
    sections.sort(key=lambda s: len(s.split()), reverse=True)
    queries = [q for q in (_term_query(section) for section in sections[:limit]) if q]
    return queries


def document_title(text: str) -> str | None:
    """The title printed at the top of the document itself.

    An uploaded PDF often carries no parsed application title, and a bag of frequent
    words retrieves almost nothing useful. The document's own title block is the single
    best query for finding the work it was taken from, so read it off the first lines.
    """
    words: list[str] = []
    parts: list[str] = []
    for raw in text.splitlines():
        line = _clean(raw)
        if not line:
            if parts:
                break  # a blank line closes the title block
            continue
        if _PAGE_FURNITURE.search(line):
            continue  # page header/footer, never the title
        if line.isupper():
            # A cover label such as "RESEARCH PROPOSAL" sits above the real title.
            if parts:
                break
            continue
        if _TITLE_STOP.match(line):
            break
        # Author lines and other short fragments end the wrapped title.
        if parts and len(line.split()) < 4:
            break
        parts.append(line)
        words.extend(line.split())
        if len(words) >= 30 or line.endswith("."):
            break
    title = _clean(" ".join(parts))
    return title if len(title.split()) >= 4 else None


def build_queries(title: str | None, narrative_text: str) -> list[str]:
    """Derive up to MAX_QUERIES OpenAlex queries from the proposal's own wording."""
    body = body_text(narrative_text)
    candidates = [
        _clean(_TITLE_NOISE.sub("", title or "")),
        document_title(narrative_text),
        _keyword_query(body),
        _term_query(body),
        *_section_queries(body),
    ]
    queries: list[str] = []
    for candidate in candidates:
        cleaned = _clean(candidate or "")[:250]
        if len(cleaned.split()) >= 3 and cleaned.lower() not in {q.lower() for q in queries}:
            queries.append(cleaned)
    return queries[:MAX_QUERIES]


def openalex_enabled() -> bool:
    """On when explicitly enabled, or when a key or polite-pool address is configured."""
    flag = (os.getenv("AI_SCREENING_OPENALEX_ENABLED") or "").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        return False
    if flag in {"1", "true", "yes", "on"}:
        return True
    return bool(openalex_api_key() or openalex_contact())


class PublishedLiteratureSource:
    """OpenAlex-backed comparison source for the plagiarism check."""

    provider_id = SOURCE_ID
    source_name = SOURCE_NAME

    def __init__(self, search=search_openalex, *, results_per_query: int = RESULTS_PER_QUERY) -> None:
        self._search = search
        self.results_per_query = results_per_query

    def status(self) -> SourceAccessStatus:
        if not openalex_enabled():
            return SourceAccessStatus.NOT_CONFIGURED
        return SourceAccessStatus.AVAILABLE

    def search(self, queries: list[str]) -> LiteratureSearch:
        if not openalex_enabled():
            return LiteratureSearch(
                state=RunState.BLOCKED,
                message="OpenAlex is not configured; published literature was not searched. "
                        "Set AI_SCREENING_OPENALEX_API_KEY or AI_SCREENING_OPENALEX_MAILTO in .env.",
            )
        if not queries:
            return LiteratureSearch(
                state=RunState.BLOCKED,
                message="No usable search terms could be derived from the proposal; "
                        "published literature was not searched.",
            )
        found: dict[str, ResearchRecord] = {}
        errors: list[str] = []
        for query in queries:
            try:
                results = self._search(query, self.results_per_query)
            except Exception as exc:
                logger.warning("OpenAlex search failed for %r: %s", query, exc)
                errors.append(f"{type(exc).__name__}: {exc}")
                continue
            for record in results:
                # Only works with a substantive abstract can be text-compared.
                if record.record_id and len(record.abstract.split()) >= MIN_ABSTRACT_WORDS:
                    found.setdefault(record.record_id, record)
        records = tuple(found.values())
        if errors and not records:
            return LiteratureSearch(
                state=RunState.FAILED, queries=tuple(queries), errors=tuple(errors),
                message=f"OpenAlex could not be searched ({errors[0]}); published literature was not compared.",
            )
        state = RunState.PARTIAL if errors else RunState.COMPLETE
        message = (
            f"{len(records)} published work(s) with abstracts compared from "
            f"{len(queries)} query(ies)"
            + (f"; {len(errors)} query(ies) failed" if errors else "")
        )
        return LiteratureSearch(records, state, message, tuple(queries), tuple(errors))
