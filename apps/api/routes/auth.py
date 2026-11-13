from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from apps.api.dependencies import get_demo_auth, request_bearer_token
from apps.api.schemas.auth import DemoIdentity, DemoLoginRequest, DemoLoginResponse
from services.auth.demo_auth import (
    DemoAuthentication,
    DemoAuthenticationDisabled,
    DemoPrincipal,
    InvalidDemoCredentials,
)

router = APIRouter(prefix="/api/v1/auth", tags=["demo-authentication"])
AuthDep = Annotated[DemoAuthentication, Depends(get_demo_auth)]


def _identity(principal: DemoPrincipal) -> DemoIdentity:
    return DemoIdentity(
        user_id=principal.user_id,
        email=principal.email,
        workspace=principal.workspace,
    )


@router.post("/login", response_model=DemoLoginResponse)
def login(
    body: DemoLoginRequest, http_response: Response, auth: AuthDep
) -> DemoLoginResponse:
    try:
        token, principal = auth.create_session(body.workspace, body.email, body.password)
    except DemoAuthenticationDisabled as exc:
        raise HTTPException(status_code=503, detail="Demo authentication is not enabled") from exc
    except InvalidDemoCredentials as exc:
        raise HTTPException(status_code=401, detail="Invalid email, password, or workspace") from exc
    http_response.headers["Cache-Control"] = "no-store"
    return DemoLoginResponse(
        access_token=token,
        expires_in=auth.session_ttl_seconds,
        identity=_identity(principal),
    )


@router.get("/me", response_model=DemoIdentity)
def me(request: Request) -> DemoIdentity:
    principal = getattr(request.state, "demo_principal", None)
    if principal is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return _identity(principal)


@router.post("/logout", status_code=204)
def logout(request: Request, auth: AuthDep) -> Response:
    auth.revoke(request_bearer_token(request))
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
