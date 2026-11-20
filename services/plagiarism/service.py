import re
import urllib.request
from uuid import uuid4

from ml.semantic_matching.service import compare_texts
from services.plagiarism.attribution import resolve_attribution
from services.plagiarism.models import PlagiarismEvidence, SourceCandidate
from services.plagiarism.search import google_search_sources


def _fetch_page_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "AI-SCREENING/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        raw = response.read(1_000_000).decode("utf-8", errors="ignore")
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", raw)
    return " ".join(text.split())


def _best_source_window(applicant: str, source: str) -> tuple[float, str]:
    applicant_words = applicant.split()
    source_words = source.split()
    if not applicant_words or not source_words:
        return 0.0, ""
    window = max(40, min(len(applicant_words) * 2, 300))
    step = max(20, window // 2)
    best_score = 0.0
    best_text = ""
    for start in range(0, max(1, len(source_words) - window + 1), step):
        chunk = " ".join(source_words[start : start + window])
        score = compare_texts(applicant, chunk).score
        if score > best_score:
            best_score, best_text = score, chunk
    return best_score, best_text


def _best_applicant_window(applicant: str, source_passage: str) -> str:
    """Return the applicant excerpt most similar to the selected source passage."""
    words = applicant.split()
    source_words = source_passage.split()
    if not words or not source_words:
        return ""
    window = min(len(words), max(12, min(len(source_words), 100)))
    step = max(5, window // 4)
    best_score = -1.0
    best_text = " ".join(words[:window])
    for start in range(0, max(1, len(words) - window + 1), step):
        excerpt = " ".join(words[start : start + window])
        score = compare_texts(excerpt, source_passage).score
        if score > best_score:
            best_score, best_text = score, excerpt
    return best_text


def _match_type(similarity: float, applicant: str, source: str) -> str:
    if similarity >= 0.9:
        return "near-verbatim"
    if similarity >= 0.65:
        return "close-paraphrase"
    if similarity >= 0.45:
        return "related-overlap"
    return "weak-overlap"


_BOILERPLATE = (
    "institutional research ethics committee",
    "participants will receive information",
    "withdraw without penalty",
    "host institution",
    "office space",
    "quarterly financial reports",
    "procurement procedures",
)


def classify_disposition(applicant_passage: str, source_passage: str, similarity: float) -> str:
    """Classify only the supplied matched excerpts, never whole-document context."""
    applicant = " ".join(applicant_passage.split()).casefold()
    source = " ".join(source_passage.split()).casefold()
    matched_text = f"{applicant} {source}"
    if any(phrase in matched_text for phrase in _BOILERPLATE):
        return "GENERIC_OR_BOILERPLATE"
    if re.search(r"(?i)(?:cited from|source:|reference:|references:|quoted from|according to)", applicant):
        return "PROPERLY_ATTRIBUTED_CONTEXT"
    if similarity >= 0.65:
        return "POTENTIAL_VERBATIM_OR_NEAR_VERBATIM"
    if similarity >= 0.45:
        return "POTENTIAL_PARAPHRASED_OVERLAP"
    return "INSUFFICIENT_EVIDENCE"


def check_public_sources(text: str, *, limit: int = 5) -> list[PlagiarismEvidence]:
    """Find public-source similarity evidence; never returns a plagiarism verdict."""
    normalized = " ".join(text.split())
    if len(normalized) < 40:
        raise ValueError("At least 40 characters are required for source comparison.")

    candidates = google_search_sources(normalized[:1200], limit=limit)
    findings: list[PlagiarismEvidence] = []
    for candidate in candidates:
        try:
            source_text = _fetch_page_text(candidate.url)
        except Exception:
            continue
        if not source_text:
            continue
        score, matched_text = _best_source_window(normalized, source_text)
        if score < 0.35:
            continue
        applicant_passage = _best_applicant_window(normalized, matched_text)
        attribution = resolve_attribution(candidate.url, candidate.title)
        enriched = SourceCandidate(
            source_id=candidate.source_id,
            title=candidate.title,
            url=candidate.url,
            snippet=candidate.snippet,
            search_query=candidate.search_query,
            attribution=attribution,
        )
        findings.append(
            PlagiarismEvidence(
                finding_id=f"PLG-{uuid4().hex[:10]}",
                status="REVIEW_REQUIRED",
                match_type=_match_type(score, applicant_passage, matched_text),
                similarity=round(score, 4),
                applicant_passage=applicant_passage[:2000],
                source_passage=matched_text[:2000],
                source=enriched,
                explanation=(
                    "Potential text similarity detected against a public source. "
                    "The source URL and attribution metadata are provided for human comparison."
                ),
                confidence=round(score, 4),
                disposition=classify_disposition(applicant_passage, matched_text, score),
            )
        )
    return sorted(findings, key=lambda item: item.similarity, reverse=True)


def check_public_sources_with_coverage(
    text: str, *, limit: int = 5
) -> tuple[list[PlagiarismEvidence], list[dict[str, str]]]:
    normalized = " ".join(text.split())
    if len(normalized) < 40:
        raise ValueError("At least 40 characters are required for source comparison.")

    candidates = google_search_sources(normalized[:1200], limit=limit)
    findings: list[PlagiarismEvidence] = []
    unavailable: list[dict[str, str]] = []
    for candidate in candidates:
        try:
            source_text = _fetch_page_text(candidate.url)
        except Exception:
            unavailable.append({
                "source_id": candidate.source_id,
                "title": candidate.title,
                "url": candidate.url,
                "state": "UNAVAILABLE",
            })
            continue
        if not source_text:
            unavailable.append({
                "source_id": candidate.source_id,
                "title": candidate.title,
                "url": candidate.url,
                "state": "NO_TEXT_LAYER",
            })
            continue
        score, matched_text = _best_source_window(normalized, source_text)
        if score < 0.35:
            continue
        applicant_passage = _best_applicant_window(normalized, matched_text)
        attribution = resolve_attribution(candidate.url, candidate.title)
        enriched = SourceCandidate(
            source_id=candidate.source_id,
            title=candidate.title,
            url=candidate.url,
            snippet=candidate.snippet,
            search_query=candidate.search_query,
            attribution=attribution,
        )
        findings.append(
            PlagiarismEvidence(
                finding_id=f"PLG-{uuid4().hex[:10]}",
                status="REVIEW_REQUIRED",
                match_type=_match_type(score, applicant_passage, matched_text),
                similarity=round(score, 4),
                applicant_passage=applicant_passage[:2000],
                source_passage=matched_text[:2000],
                source=enriched,
                explanation=(
                    "Potential text similarity detected against a public source. "
                    "The source URL and attribution metadata are provided for human comparison."
                ),
                confidence=round(score, 4),
                disposition=classify_disposition(applicant_passage, matched_text, score),
            )
        )
    return sorted(findings, key=lambda item: item.similarity, reverse=True), unavailable
