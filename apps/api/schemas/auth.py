from pydantic import BaseModel, Field

from services.auth.demo_auth import DemoWorkspace


class DemoLoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=128)
    workspace: DemoWorkspace


class DemoIdentity(BaseModel):
    user_id: str
    email: str
    workspace: DemoWorkspace


class DemoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    identity: DemoIdentity
