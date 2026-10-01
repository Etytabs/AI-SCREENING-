from services.research_sources.models import SourceDefinition

SOURCE_REGISTRY: tuple[SourceDefinition, ...] = (
    SourceDefinition("openalex", "OpenAlex", "api", "https://api.openalex.org", "global scholarly works, authors and institutions", False, True, notes="Open API; a key or polite-pool mailto address raises the rate limit."),
    SourceDefinition("core", "CORE", "api", "https://core.ac.uk", "global open-access research", True, True, notes="API key required."),
    SourceDefinition("crossref", "Crossref", "api", "https://api.crossref.org", "global scholarly metadata", False, True),
    SourceDefinition("doaj", "Directory of Open Access Journals", "oai_pmh", "https://doaj.org", "open-access journals and articles", False, True),
    SourceDefinition("pmc", "PubMed Central", "api", "https://www.ncbi.nlm.nih.gov/pmc", "biomedical full text", True, True),
    SourceDefinition("arxiv", "arXiv", "api", "https://arxiv.org", "physics, mathematics and computer science preprints", True, True),
    SourceDefinition("ajol", "African Journals Online", "discovery", "https://www.ajol.info", "African scholarly journals", True, True, notes="Use authorized feeds or repository access; no scraping connector."),
    SourceDefinition("open_research_africa", "Open Research Africa", "discovery", "https://openresearchafrica.org", "African open research", True, True),
    SourceDefinition("africa_center", "Africa Center for Strategic Studies", "discovery", "https://africacenter.org", "African policy and research papers", True, True),
    SourceDefinition("asc_leiden", "African Studies Centre Leiden E-Journals", "discovery", "https://www.ascleiden.nl", "Africa-related free e-journals", False, True),
    SourceDefinition("african_repositories", "African Repositories Directory", "discovery", "https://www.internationalafricaninstitute.org/repositories", "African repository discovery", False, True),
    SourceDefinition("google_scholar", "Google Scholar", "discovery", "https://scholar.google.com", "scholarly discovery", False, True, notes="Discovery/reference layer; not scraped by this connector."),
)


def get_source(source_id: str) -> SourceDefinition:
    for source in SOURCE_REGISTRY:
        if source.source_id == source_id:
            return source
    raise KeyError(f"Unknown research source: {source_id}")


def list_sources() -> list[SourceDefinition]:
    return list(SOURCE_REGISTRY)
