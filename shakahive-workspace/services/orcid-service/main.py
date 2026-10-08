"""
ORCID Service - ORCID Integration (E05)
Handles ORCID authentication and profile retrieval
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import httpx
import json
from urllib.parse import urlencode

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="ORCID Service",
    description="ORCID authentication and profile integration",
    version="2.0.0"
)

# ORCID Configuration
ORCID_API_URL = "https://api.orcid.org"
ORCID_PUBLIC_API_URL = "https://pub.orcid.org"
ORCID_CLIENT_ID = os.getenv("ORCID_CLIENT_ID", "")
ORCID_CLIENT_SECRET = os.getenv("ORCID_CLIENT_SECRET", "")
ORCID_REDIRECT_URI = os.getenv("ORCID_REDIRECT_URI", "http://localhost:8008/callback")

# Scopes
ORCID_SCOPES = [
    "/authenticate",
    "/read-limited",
    "/activities/update",
    "/person/update"
]


class ORCIDProfile(BaseModel):
    """ORCID profile structure"""
    orcid_id: str
    given_names: str
    family_name: str
    email: Optional[str] = None
    affiliation: Optional[str] = None
    education: Optional[List[Dict]] = None
    employment: Optional[List[Dict]] = None
    works: Optional[List[Dict]] = None


class ORCIDAuthRequest(BaseModel):
    """Request for ORCID authentication"""
    scope: str = "/authenticate"
    state: Optional[str] = None


class ORCIDAuthResponse(BaseModel):
    """ORCID authentication response"""
    auth_url: str
    state: str


class ORCIDTokenResponse(BaseModel):
    """ORCID token exchange response"""
    access_token: str
    token_type: str
    expires_in: int
    scope: str
    orcid: str
    name: str


def generate_orcid_auth_url(scope: str, state: Optional[str] = None) -> str:
    """Generate ORCID OAuth authorization URL"""
    params = {
        "client_id": ORCID_CLIENT_ID,
        "response_type": "code",
        "scope": scope,
        "redirect_uri": ORCID_REDIRECT_URI
    }
    
    if state:
        params["state"] = state
    
    return f"https://orcid.org/oauth/authorize?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token"""
    data = {
        "client_id": ORCID_CLIENT_ID,
        "client_secret": ORCID_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": ORCID_REDIRECT_URI
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "https://orcid.org/oauth/token",
            data=data
        )
        response.raise_for_status()
        return response.json()


async def get_orcid_profile(orcid_id: str, access_token: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve ORCID profile"""
    headers = {"Accept": "application/json"}
    
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get person details
        person_response = await client.get(
            f"{ORCID_PUBLIC_API_URL}/v3.0/{orcid_id}/person",
            headers=headers
        )
        person_response.raise_for_status()
        person_data = person_response.json()
        
        # Get works (if token provided)
        works_data = None
        if access_token:
            works_response = await client.get(
                f"{ORCID_API_URL}/v3.0/{orcid_id}/works",
                headers=headers
            )
            if works_response.status_code == 200:
                works_data = works_response.json()
        
        return {
            "person": person_data,
            "works": works_data
        }


def parse_orcid_profile(data: Dict) -> ORCIDProfile:
    """Parse ORCID API response into standardized profile"""
    person = data.get("person", {})
    name = person.get("name", {})
    
    # Extract email
    emails = person.get("emails", {}).get("email", [])
    primary_email = None
    for email in emails:
        if email.get("primary", False):
            primary_email = email.get("email")
            break
        if not primary_email:
            primary_email = email.get("email")
    
    # Extract affiliations
    employments = person.get("employments", {}).get("employment", [])
    affiliations = [
        {
            "organization": emp.get("organization", {}).get("name"),
            "department": emp.get("department-name"),
            "role": emp.get("role-title"),
            "start_date": emp.get("start-date", {}).get("year", {}).get("value"),
            "end_date": emp.get("end-date", {}).get("year", {}).get("value") if emp.get("end-date") else None
        }
        for emp in employments
    ]
    
    # Extract education
    educations = person.get("educations", {}).get("education", [])
    education_list = [
        {
            "organization": edu.get("organization", {}).get("name"),
            "department": edu.get("department-name"),
            "role": edu.get("role-title"),
            "start_date": edu.get("start-date", {}).get("year", {}).get("value"),
            "end_date": edu.get("end-date", {}).get("year", {}).get("value") if edu.get("end-date") else None
        }
        for edu in educations
    ]
    
    # Extract works
    works = data.get("works", {}).get("group", []) if data.get("works") else []
    works_list = []
    for work_group in works:
        for work in work_group.get("work-summary", []):
            works_list.append({
                "title": work.get("title", {}).get("title", {}).get("value"),
                "type": work.get("type"),
                "journal": work.get("journal-title", {}).get("value"),
                "year": work.get("publication-date", {}).get("year", {}).get("value"),
                "doi": work.get("external-ids", {}).get("external-id", [{}])[0].get("external-id-value") if work.get("external-ids") else None
            })
    
    return ORCIDProfile(
        orcid_id=person.get("name", {}).get("path"),
        given_names=name.get("given-names", {}).get("value"),
        family_name=name.get("family-name", {}).get("value"),
        email=primary_email,
        affiliation=affiliations[0]["organization"] if affiliations else None,
        education=education_list,
        employment=affiliations,
        works=works_list
    )


@app.get("/")
async def root():
    return {
        "service": "ORCID Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    """Check ORCID API availability"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(f"{ORCID_PUBLIC_API_URL}/v3.0/0000-0002-1825-0097")
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "orcid_api": "available" if response.status_code == 200 else "unavailable"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "orcid_api": "unreachable",
                "error": str(e)
            }


@app.post("/auth/url", response_model=ORCIDAuthResponse)
async def get_auth_url(request: ORCIDAuthRequest):
    """Generate ORCID authentication URL"""
    if not ORCID_CLIENT_ID:
        raise HTTPException(status_code=500, detail="ORCID client ID not configured")
    
    state = request.state or f"state_{datetime.utcnow().timestamp()}"
    auth_url = generate_orcid_auth_url(request.scope, state)
    
    return ORCIDAuthResponse(
        auth_url=auth_url,
        state=state
    )


@app.post("/auth/token", response_model=ORCIDTokenResponse)
async def exchange_token(code: str):
    """Exchange authorization code for access token"""
    if not ORCID_CLIENT_ID or not ORCID_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="ORCID credentials not configured")
    
    try:
        token_data = await exchange_code_for_token(code)
        
        return ORCIDTokenResponse(
            access_token=token_data.get("access_token"),
            token_type=token_data.get("token_type"),
            expires_in=token_data.get("expires_in"),
            scope=token_data.get("scope"),
            orcid=token_data.get("orcid"),
            name=token_data.get("name")
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Token exchange failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/{orcid_id}", response_model=ORCIDProfile)
async def get_profile(
    orcid_id: str,
    access_token: Optional[str] = Query(None)
):
    """Retrieve ORCID profile"""
    try:
        profile_data = await get_orcid_profile(orcid_id, access_token)
        profile = parse_orcid_profile(profile_data)
        return profile
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="ORCID profile not found")
        raise HTTPException(status_code=e.response.status_code, detail="Failed to retrieve profile")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/{orcid_id}/works")
async def get_works(
    orcid_id: str,
    access_token: str = Query(...)
):
    """Retrieve ORCID works (requires access token)"""
    try:
        profile_data = await get_orcid_profile(orcid_id, access_token)
        works = profile_data.get("works", {}).get("group", [])
        
        return {
            "orcid_id": orcid_id,
            "total_works": len(works),
            "works": works
        }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail="Failed to retrieve works")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate/{orcid_id}")
async def validate_orcid(orcid_id: str):
    """Validate ORCID ID format and existence"""
    # Validate format
    if not orcid_id.startswith("0000-") or len(orcid_id) != 19:
        return {
            "valid": False,
            "reason": "Invalid ORCID format"
        }
    
    # Check existence
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ORCID_PUBLIC_API_URL}/v3.0/{orcid_id}")
            
            if response.status_code == 200:
                return {
                    "valid": True,
                    "orcid_id": orcid_id,
                    "exists": True
                }
            elif response.status_code == 404:
                return {
                    "valid": True,
                    "orcid_id": orcid_id,
                    "exists": False,
                    "reason": "ORCID ID not found"
                }
            else:
                return {
                    "valid": True,
                    "orcid_id": orcid_id,
                    "exists": False,
                    "reason": f"ORCID API returned {response.status_code}"
                }
    except Exception as e:
        return {
            "valid": True,
            "orcid_id": orcid_id,
            "exists": False,
            "reason": f"Validation failed: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
