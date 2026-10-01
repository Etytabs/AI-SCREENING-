import json
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from services.research_sources.models import ResearchRecord


def _get(url: str, headers: dict[str, str] | None = None) -> bytes:
    request = urllib.request.Request(url, headers=headers or {"User-Agent": "shakaHive/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read()


def search_crossref(query: str, rows: int = 10) -> list[ResearchRecord]:
    params = urllib.parse.urlencode({"query.bibliographic": query, "rows": min(rows, 50)})
    payload = json.loads(_get("https://api.crossref.org/works?" + params))
    return [ResearchRecord(record_id=i.get("DOI") or i.get("URL", ""), title=(i.get("title") or [""])[0], authors=tuple(" ".join(filter(None, (a.get("given"), a.get("family")))) for a in i.get("author", [])), doi=i.get("DOI"), source_id="crossref", source_url=i.get("URL"), provenance={"retrieval_method": "crossref_rest"}) for i in payload.get("message", {}).get("items", [])]


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


def search_doaj(query: str, rows: int = 10) -> list[ResearchRecord]:
    params = urllib.parse.urlencode({"verb": "ListRecords", "metadataPrefix": "oai_doaj", "from": "2020-01-01"})
    root = ET.fromstring(_get("https://doaj.org/oai.article?" + params))
    ns = {"oai": "http://www.openarchives.org/OAI/2.0/", "d": "http://doaj.org/features/oai_doaj/"}
    needle = query.lower()
    records = []
    for record in root.findall(".//oai:record", ns):
        title = record.findtext(".//d:title", "", ns)
        abstract = record.findtext(".//d:abstract", "", ns)
        if needle not in (title + " " + abstract).lower():
            continue
        doi = record.findtext(".//d:doi", None, ns)
        url = record.findtext(".//d:fullTextUrl", None, ns)
        identifier = doi or record.findtext(".//oai:identifier", "", ns)
        records.append(ResearchRecord(record_id=identifier, title=title, abstract=abstract, doi=doi, source_id="doaj", source_url=url, full_text_url=url, provenance={"retrieval_method": "doaj_oai_pmh"}))
        if len(records) >= min(rows, 20):
            break
    return records


def search_core(query: str, rows: int = 10) -> list[ResearchRecord]:
    api_key = os.getenv("AI_SCREENING_CORE_API_KEY")
    if not api_key:
        raise RuntimeError("AI_SCREENING_CORE_API_KEY is required for CORE search.")
    params = urllib.parse.urlencode({"q": query, "limit": min(rows, 100)})
    payload = json.loads(_get("https://api.core.ac.uk/v3/search/works?" + params, {"Authorization": "Bearer " + api_key, "User-Agent": "shakaHive/0.1"}))
    return [ResearchRecord(record_id=str(i.get("id", "")), title=i.get("title", ""), abstract=i.get("abstract", "") or "", doi=i.get("doi"), source_id="core", source_url=i.get("downloadUrl"), full_text_url=i.get("downloadUrl"), provenance={"retrieval_method": "core_api"}) for i in payload.get("results", [])]


OPENALEX_WORKS_URL = "https://api.openalex.org/works"
_OPENALEX_FIELDS = (
    "id,doi,display_name,publication_year,publication_date,abstract_inverted_index,"
    "authorships,primary_location,best_oa_location,type"
)


def openalex_contact() -> str | None:
    """OpenAlex polite-pool contact address (AI_SCREENING_OPENALEX_MAILTO)."""
    return (os.getenv("AI_SCREENING_OPENALEX_MAILTO") or "").strip() or None


def openalex_api_key() -> str | None:
    return (os.getenv("AI_SCREENING_OPENALEX_API_KEY") or "").strip() or None


def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    """OpenAlex stores abstracts as {word: [positions]}; rebuild the running text."""
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for word, slots in inverted_index.items():
        for slot in slots:
            positions[slot] = word
    return " ".join(positions[slot] for slot in sorted(positions))


def search_openalex(query: str, rows: int = 10) -> list[ResearchRecord]:
    """Search OpenAlex works. No key is required; a key raises the rate limit."""
    fields = {"search": query, "per-page": str(min(max(rows, 1), 50)), "select": _OPENALEX_FIELDS}
    contact, key = openalex_contact(), openalex_api_key()
    if contact:
        fields["mailto"] = contact
    if key:
        fields["api_key"] = key
    agent = "shakaHive/0.1" + (f" (mailto:{contact})" if contact else "")
    payload = json.loads(_get(OPENALEX_WORKS_URL + "?" + urllib.parse.urlencode(fields), {"User-Agent": agent}))
    records = []
    for item in payload.get("results", []):
        work_id = (item.get("id") or "").rsplit("/", 1)[-1]
        doi_url = item.get("doi")
        location = item.get("primary_location") or {}
        best_oa = item.get("best_oa_location") or {}
        source = location.get("source") or {}
        records.append(ResearchRecord(
            record_id=work_id or (doi_url or ""),
            title=item.get("display_name") or "",
            abstract=reconstruct_abstract(item.get("abstract_inverted_index")),
            authors=tuple(
                (a.get("author") or {}).get("display_name", "")
                for a in item.get("authorships", []) if (a.get("author") or {}).get("display_name")
            ),
            publication_date=item.get("publication_date") or (str(item["publication_year"]) if item.get("publication_year") else None),
            journal=source.get("display_name"),
            doi=doi_url.removeprefix("https://doi.org/") if doi_url else None,
            source_id="openalex",
            source_url=doi_url or location.get("landing_page_url") or (item.get("id") or None),
            full_text_url=best_oa.get("pdf_url") or location.get("pdf_url"),
            affiliations=tuple(dict.fromkeys(
                institution.get("display_name", "")
                for a in item.get("authorships", []) for institution in a.get("institutions", [])
                if institution.get("display_name")
            )),
            provenance={"retrieval_method": "openalex_works_api", "work_type": item.get("type") or ""},
        ))
    return records


def search_source(source_id: str, query: str, rows: int = 10) -> list[ResearchRecord]:
    connector = {"crossref": search_crossref, "arxiv": search_arxiv, "pmc": search_pmc, "doaj": search_doaj, "core": search_core, "openalex": search_openalex}.get(source_id)
    if connector is None:
        raise ValueError(f"Source {source_id!r} is discovery-only or has no connector configured.")
    return connector(query, rows)
