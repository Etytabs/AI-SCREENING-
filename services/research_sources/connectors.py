import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from services.research_sources.models import ResearchRecord


def _get(url: str, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "AI-SCREENING/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def search_crossref(query: str, rows: int = 10) -> list[ResearchRecord]:
    params = urllib.parse.urlencode({"query.bibliographic": query, "rows": min(rows, 50)})
    payload = json.loads(_get("https://api.crossref.org/works?" + params))
    records = []
    for item in payload.get("message", {}).get("items", []):
        authors = tuple(" ".join(filter(None, (a.get("given"), a.get("family")))) for a in item.get("author", []))
        records.append(ResearchRecord(record_id=item.get("DOI") or item.get("URL", ""), title=(item.get("title") or [""])[0], authors=authors, doi=item.get("DOI"), source_id="crossref", source_url=item.get("URL"), provenance={"retrieval_method": "crossref_rest"}))
    return records


def search_arxiv(query: str, rows: int = 10) -> list[ResearchRecord]:
    params = urllib.parse.urlencode({"search_query": "all:" + query, "start": 0, "max_results": min(rows, 50)})
    root = ET.fromstring(_get("https://export.arxiv.org/api/query?" + params))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    records = []
    for entry in root.findall("a:entry", ns):
        url = entry.findtext("a:id", "", ns)
        record_id = url.rsplit("/", 1)[-1]
        records.append(ResearchRecord(record_id=record_id, title=" ".join(entry.findtext("a:title", "", ns).split()), abstract=" ".join(entry.findtext("a:summary", "", ns).split()), authors=tuple(a.findtext("a:name", "", ns) for a in entry.findall("a:author", ns)), arxiv_id=record_id, source_id="arxiv", source_url=url, full_text_url="https://arxiv.org/pdf/" + record_id, provenance={"retrieval_method": "arxiv_atom_api"}))
    return records


def search_pmc(query: str, rows: int = 10) -> list[ResearchRecord]:
    params = urllib.parse.urlencode({"db": "pmc", "term": query, "retmax": min(rows, 50), "retmode": "json"})
    search = json.loads(_get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + params))
    ids = search.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    params = urllib.parse.urlencode({"db": "pmc", "id": ",".join(ids), "retmode": "json"})
    payload = json.loads(_get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + params))
    return [ResearchRecord(record_id=pmcid, title=payload.get("result", {}).get(pmcid, {}).get("title", ""), pmid=payload.get("result", {}).get(pmcid, {}).get("pmid"), source_id="pmc", source_url="https://pmc.ncbi.nlm.nih.gov/articles/" + pmcid + "/", full_text_url="https://pmc.ncbi.nlm.nih.gov/articles/" + pmcid + "/", provenance={"retrieval_method": "ncbi_eutils"}) for pmcid in ids]


def search_core(query: str, rows: int = 10) -> list[ResearchRecord]:
    api_key = os.getenv("AI_SCREENING_CORE_API_KEY")
    if not api_key:
        raise RuntimeError("AI_SCREENING_CORE_API_KEY is required for CORE search.")
    params = urllib.parse.urlencode({"q": query, "limit": min(rows, 100)})
    payload = json.loads(_get("https://api.core.ac.uk/v3/search/works?" + params, {"Authorization": "Bearer " + api_key, "User-Agent": "AI-SCREENING/0.1"}))
    return [ResearchRecord(record_id=str(item.get("id", "")), title=item.get("title", ""), abstract=item.get("abstract", "") or "", doi=item.get("doi"), source_id="core", source_url=item.get("downloadUrl"), full_text_url=item.get("downloadUrl"), provenance={"retrieval_method": "core_api"}) for item in payload.get("results", [])]


def search_source(source_id: str, query: str, rows: int = 10) -> list[ResearchRecord]:
    connector = {"crossref": search_crossref, "arxiv": search_arxiv, "pmc": search_pmc, "core": search_core}.get(source_id)
    if connector is None:
        raise ValueError(f"Source {source_id!r} is discovery-only or has no connector configured.")
    return connector(query, rows)
