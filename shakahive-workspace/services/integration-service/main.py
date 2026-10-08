"""
Integration Service - External Data Connectors (E05)
Connects to Crossref, OpenAlex, and EPO for publication and patent data
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import httpx
import asyncio
from enum import Enum
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="Integration Service",
    description="External data connectors for Crossref, OpenAlex, and EPO",
    version="2.0.0"
)

# Configuration
CROSSREF_API_URL = "https://api.crossref.org"
OPENALEX_API_URL = "https://api.openalex.org"
EPO_API_URL = "https://ops.epo.org"
CROSSREF_API_KEY = os.getenv("CROSSREF_API_KEY", "")
OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "")
EPO_API_KEY = os.getenv("EPO_API_KEY", "")

# Rate limiting
CROSSREF_RATE_LIMIT = 50  # requests per second
OPENALEX_RATE_LIMIT = 100  # requests per second


class DataSource(str, Enum):
    CROSSREF = "crossref"
    OPENALEX = "openalex"
    EPO = "epo"


class QueryRequest(BaseModel):
    """Request for external data query"""
    source: DataSource
    query_type: str  # doi, title, author, patent_number, etc.
    query_value: str
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = 20


class CrossrefResponse(BaseModel):
    """Crossref API response structure"""
    status: str
    message_type: str
    message_version: str
    items: List[Dict[str, Any]]
    total_results: int


class OpenAlexResponse(BaseModel):
    """OpenAlex API response structure"""
    meta: Dict[str, Any]
    results: List[Dict[str, Any]]
    group_by: Optional[List[Dict[str, Any]]] = None


class EpoResponse(BaseModel):
    """EPO API response structure"""
    patent_number: str
    title: str
    abstract: str
    applicants: List[str]
    inventors: List[str]
    filing_date: str
    publication_date: str
    ipc_codes: List[str]


class IntegrationResult(BaseModel):
    """Standardized integration result"""
    source: DataSource
    query_type: str
    query_value: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    cached: bool = False
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)


# In-memory cache (in production, use Redis)
cache = {}


async def query_crossref(
    query_type: str,
    query_value: str,
    filters: Optional[Dict] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Query Crossref API"""
    cache_key = f"crossref:{query_type}:{query_value}"
    
    if cache_key in cache:
        return {"success": True, "data": cache[cache_key], "cached": True}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {}
        if CROSSREF_API_KEY:
            headers["User-Agent"] = f"NOVARAai/2.0 (mailto:admin@novarai.rw; mailto:{CROSSREF_API_KEY})"
        
        if query_type == "doi":
            url = f"{CROSSREF_API_URL}/works/{query_value}"
        elif query_type == "title":
            url = f"{CROSSREF_API_URL}/works"
            params = {
                "query.title": query_value,
                "rows": limit,
                "select": "DOI,title,author,published-online,container-title,type"
            }
        elif query_type == "author":
            url = f"{CROSSREF_API_URL}/works"
            params = {
                "query.author": query_value,
                "rows": limit,
                "select": "DOI,title,author,published-online,container-title,type"
            }
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
        
        if filters:
            params.update(filters)
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Cache result
        cache[cache_key] = data
        
        return {"success": True, "data": data, "cached": False}


async def query_openalex(
    query_type: str,
    query_value: str,
    filters: Optional[Dict] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """Query OpenAlex API"""
    cache_key = f"openalex:{query_type}:{query_value}"
    
    if cache_key in cache:
        return {"success": True, "data": cache[cache_key], "cached": True}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {}
        if OPENALEX_API_KEY:
            headers["User-Agent"] = f"NOVARAai/2.0 (mailto:admin@novarai.rw)"
        
        if query_type == "doi":
            url = f"{OPENALEX_API_URL}/https://doi.org/{query_value}"
        elif query_type == "title":
            url = f"{OPENALEX_API_URL}/works"
            params = {
                "search": query_value,
                "per_page": limit
            }
        elif query_type == "author":
            url = f"{OPENALEX_API_URL}/authors"
            params = {
                "search": query_value,
                "per_page": limit
            }
        elif query_type == "institution":
            url = f"{OPENALEX_API_URL}/institutions"
            params = {
                "search": query_value,
                "per_page": limit
            }
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
        
        if filters:
            params.update(filters)
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Cache result
        cache[cache_key] = data
        
        return {"success": True, "data": data, "cached": False}


async def query_epo(
    query_type: str,
    query_value: str,
    filters: Optional[Dict] = None
) -> Dict[str, Any]:
    """Query EPO API (patent data)"""
    cache_key = f"epo:{query_type}:{query_value}"
    
    if cache_key in cache:
        return {"success": True, "data": cache[cache_key], "cached": True}
    
    # Note: EPO requires OAuth authentication
    # This is a simplified implementation
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {EPO_API_KEY}",
            "Accept": "application/json"
        }
        
        if query_type == "patent_number":
            url = f"{EPO_API_URL}/3.2/rest-services/published-data/publication/docdb/{query_value}"
        elif query_type == "applicant":
            url = f"{EPO_API_URL}/3.2/rest-services/published-data/search"
            params = {"q": f"applicant:{query_value}"}
        else:
            raise ValueError(f"Unsupported query type: {query_type}")
        
        if filters:
            params.update(filters)
        
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Cache result
        cache[cache_key] = data
        
        return {"success": True, "data": data, "cached": False}


def standardize_crossref_data(data: Dict) -> Dict:
    """Standardize Crossref response data"""
    items = data.get("message", {}).get("items", [])
    
    standardized = []
    for item in items:
        standardized.append({
            "source": "crossref",
            "doi": item.get("DOI"),
            "title": item.get("title", [""])[0] if item.get("title") else "",
            "authors": [
                {
                    "given": author.get("given"),
                    "family": author.get("family"),
                    "orcid": author.get("ORCID")
                }
                for author in item.get("author", [])
            ],
            "published_date": item.get("published-online", {}).get("date-parts", [[""]])[0][0],
            "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
            "type": item.get("type"),
            "url": item.get("URL")
        })
    
    return {
        "source": "crossref",
        "total_results": data.get("message", {}).get("total-results", 0),
        "items": standardized
    }


def standardize_openalex_data(data: Dict) -> Dict:
    """Standardize OpenAlex response data"""
    results = data.get("results", [])
    
    standardized = []
    for item in results:
        standardized.append({
            "source": "openalex",
            "doi": item.get("doi"),
            "title": item.get("title"),
            "authors": [
                {
                    "given": author.get("author", {}).get("given_name"),
                    "family": author.get("author", {}).get("family_name"),
                    "orcid": author.get("author", {}).get("orcid")
                }
                for author in item.get("authorships", [])
            ],
            "published_date": item.get("publication_year"),
            "journal": item.get("primary_location", {}).get("source", {}).get("display_name"),
            "type": item.get("type"),
            "citations": item.get("cited_by_count"),
            "concepts": [
                {"name": c.get("display_name"), "score": c.get("score")}
                for c in item.get("concepts", [])[:5]
            ]
        })
    
    return {
        "source": "openalex",
        "total_results": data.get("meta", {}).get("count", 0),
        "items": standardized
    }


def standardize_epo_data(data: Dict) -> Dict:
    """Standardize EPO response data"""
    # Simplified parsing - actual EPO response structure is complex
    return {
        "source": "epo",
        "items": [
            {
                "patent_number": data.get("patent_number"),
                "title": data.get("title"),
                "abstract": data.get("abstract"),
                "applicants": data.get("applicants", []),
                "inventors": data.get("inventors", []),
                "filing_date": data.get("filing_date"),
                "publication_date": data.get("publication_date"),
                "ipc_codes": data.get("ipc_codes", [])
            }
        ]
    }


@app.get("/")
async def root():
    return {
        "service": "Integration Service",
        "version": "2.0.0",
        "status": "operational",
        "sources": ["crossref", "openalex", "epo"],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check with source availability"""
    health_status = {
        "status": "healthy",
        "sources": {}
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # Check Crossref
        try:
            response = await client.get(f"{CROSSREF_API_URL}/works", params={"rows": 1})
            health_status["sources"]["crossref"] = "available" if response.status_code == 200 else "unavailable"
        except Exception:
            health_status["sources"]["crossref"] = "unreachable"
        
        # Check OpenAlex
        try:
            response = await client.get(f"{OPENALEX_API_URL}/works", params={"per_page": 1})
            health_status["sources"]["openalex"] = "available" if response.status_code == 200 else "unavailable"
        except Exception:
            health_status["sources"]["openalex"] = "unreachable"
        
        # Check EPO (requires auth, so just check base URL)
        try:
            response = await client.get(EPO_API_URL, timeout=5.0)
            health_status["sources"]["epo"] = "available" if response.status_code == 200 else "unavailable"
        except Exception:
            health_status["sources"]["epo"] = "unreachable"
    
    return health_status


@app.post("/query", response_model=IntegrationResult)
async def query_external_source(request: QueryRequest):
    """Query external data source"""
    try:
        if request.source == DataSource.CROSSREF:
            result = await query_crossref(
                request.query_type,
                request.query_value,
                request.filters,
                request.limit
            )
            standardized = standardize_crossref_data(result["data"])
            
        elif request.source == DataSource.OPENALEX:
            result = await query_openalex(
                request.query_type,
                request.query_value,
                request.filters,
                request.limit
            )
            standardized = standardize_openalex_data(result["data"])
            
        elif request.source == DataSource.EPO:
            result = await query_epo(
                request.query_type,
                request.query_value,
                request.filters
            )
            standardized = standardize_epo_data(result["data"])
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported data source")
        
        return IntegrationResult(
            source=request.source,
            query_type=request.query_type,
            query_value=request.query_value,
            success=True,
            data=standardized,
            cached=result.get("cached", False)
        )
        
    except httpx.HTTPStatusError as e:
        return IntegrationResult(
            source=request.source,
            query_type=request.query_type,
            query_value=request.query_value,
            success=False,
            error=f"HTTP error: {e.response.status_code}"
        )
    except Exception as e:
        return IntegrationResult(
            source=request.source,
            query_type=request.query_type,
            query_value=request.query_value,
            success=False,
            error=str(e)
        )


@app.post("/batch-query")
async def batch_query(requests: List[QueryRequest], background_tasks: BackgroundTasks):
    """Batch query multiple sources"""
    results = []
    
    for request in requests:
        result = await query_external_source(request)
        results.append(result)
    
    return {
        "total": len(results),
        "successful": sum(1 for r in results if r.success),
        "failed": sum(1 for r in results if not r.success),
        "results": results
    }


@app.get("/sources/{source}/status")
async def get_source_status(source: DataSource):
    """Get status of a specific data source"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        if source == DataSource.CROSSREF:
            try:
                response = await client.get(f"{CROSSREF_API_URL}/works", params={"rows": 1})
                return {
                    "source": "crossref",
                    "status": "available" if response.status_code == 200 else "unavailable",
                    "rate_limit": CROSSREF_RATE_LIMIT
                }
            except Exception as e:
                return {"source": "crossref", "status": "unreachable", "error": str(e)}
        
        elif source == DataSource.OPENALEX:
            try:
                response = await client.get(f"{OPENALEX_API_URL}/works", params={"per_page": 1})
                return {
                    "source": "openalex",
                    "status": "available" if response.status_code == 200 else "unavailable",
                    "rate_limit": OPENALEX_RATE_LIMIT
                }
            except Exception as e:
                return {"source": "openalex", "status": "unreachable", "error": str(e)}
        
        elif source == DataSource.EPO:
            try:
                response = await client.get(EPO_API_URL, timeout=5.0)
                return {
                    "source": "epo",
                    "status": "available" if response.status_code == 200 else "unavailable",
                    "authenticated": bool(EPO_API_KEY)
                }
            except Exception as e:
                return {"source": "epo", "status": "unreachable", "error": str(e)}


@app.post("/cache/clear")
async def clear_cache():
    """Clear the in-memory cache"""
    cache.clear()
    return {"status": "cache_cleared"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
