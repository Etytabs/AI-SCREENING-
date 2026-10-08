"""
Auth Service - Tenant Isolation and Authorization (E02)
Handles multi-tenant authentication, authorization, and access control
"""

from fastapi import FastAPI, HTTPException, Depends, Header, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import sys
import jwt
import hashlib
from enum import Enum

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="Auth Service",
    description="Multi-tenant authentication and authorization",
    version="2.0.0"
)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
SESSION_TIMEOUT_MINUTES = 30


class UserRole(str, Enum):
    ADMIN = "admin"
    REVIEWER = "reviewer"
    SUBMITTER = "submitter"
    VIEWER = "viewer"


class Permission(str, Enum):
    READ_APPLICATIONS = "read_applications"
    WRITE_APPLICATIONS = "write_applications"
    SCREEN_APPLICATIONS = "screen_applications"
    REVIEW_APPLICATIONS = "review_applications"
    MANAGE_TENANT = "manage_tenant"
    MANAGE_USERS = "manage_users"
    VIEW_REPORTS = "view_reports"
    EXPORT_DATA = "export_data"


class Tenant(BaseModel):
    """Tenant model"""
    tenant_id: str
    tenant_name: str
    tenant_type: str  # institution, funding_agency, research_council
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    """User model"""
    user_id: str
    tenant_id: str
    email: EmailStr
    given_name: str
    family_name: str
    role: UserRole
    is_active: bool = True
    permissions: List[Permission] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """Session model"""
    session_id: str
    user_id: str
    tenant_id: str
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str
    tenant_id: str


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
    tenant: Tenant


class TokenValidation(BaseModel):
    """Token validation result"""
    valid: bool
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    role: Optional[UserRole] = None
    permissions: List[Permission] = []
    expires_at: Optional[datetime] = None


# In-memory storage (in production, use database)
tenants = {}
users = {}
sessions = {}


def initialize_default_data():
    """Initialize default tenant and user for NRIF"""
    # Create default NRIF tenant
    if "nrif" not in tenants:
        tenants["nrif"] = {
            "tenant_id": "nrif",
            "tenant_name": "National Research & Innovation Fund",
            "tenant_type": "funding_agency",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
    
    # Create default admin user
    admin_user_id = "admin-nrif-001"
    if admin_user_id not in users:
        users[admin_user_id] = {
            "user_id": admin_user_id,
            "tenant_id": "nrif",
            "email": "admin@nrif.gov",
            "given_name": "System",
            "family_name": "Administrator",
            "role": UserRole.ADMIN,
            "is_active": True,
            "permissions": get_role_permissions(UserRole.ADMIN),
            "created_at": datetime.utcnow()
        }


# Initialize on startup
initialize_default_data()


def hash_password(password: str) -> str:
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_jwt_token(user_id: str, tenant_id: str, role: UserRole) -> str:
    """Generate JWT token"""
    payload = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_role_permissions(role: UserRole) -> List[Permission]:
    """Get permissions for a role"""
    role_permissions = {
        UserRole.ADMIN: [
            Permission.READ_APPLICATIONS,
            Permission.WRITE_APPLICATIONS,
            Permission.SCREEN_APPLICATIONS,
            Permission.REVIEW_APPLICATIONS,
            Permission.MANAGE_TENANT,
            Permission.MANAGE_USERS,
            Permission.VIEW_REPORTS,
            Permission.EXPORT_DATA
        ],
        UserRole.REVIEWER: [
            Permission.READ_APPLICATIONS,
            Permission.REVIEW_APPLICATIONS,
            Permission.VIEW_REPORTS
        ],
        UserRole.SUBMITTER: [
            Permission.READ_APPLICATIONS,
            Permission.WRITE_APPLICATIONS,
            Permission.VIEW_REPORTS
        ],
        UserRole.VIEWER: [
            Permission.READ_APPLICATIONS,
            Permission.VIEW_REPORTS
        ]
    }
    return role_permissions.get(role, [])


def check_permission(user: User, permission: Permission) -> bool:
    """Check if user has permission"""
    return permission in user.permissions


def check_tenant_access(user_tenant_id: str, resource_tenant_id: str) -> bool:
    """Check if user can access resource from another tenant"""
    # Cross-tenant access is denied by default
    # Only admins with proper authorization can access other tenants
    return user_tenant_id == resource_tenant_id


@app.get("/")
async def root():
    return {
        "service": "Auth Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/tenants", response_model=Tenant)
async def create_tenant(tenant: Tenant):
    """Create a new tenant"""
    if tenant.tenant_id in tenants:
        raise HTTPException(status_code=409, detail="Tenant already exists")
    
    tenants[tenant.tenant_id] = tenant.dict()
    return tenant


@app.get("/tenants/{tenant_id}", response_model=Tenant)
async def get_tenant(tenant_id: str):
    """Get tenant by ID"""
    if tenant_id not in tenants:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return Tenant(**tenants[tenant_id])


@app.post("/users", response_model=User)
async def create_user(user: User):
    """Create a new user"""
    if user.user_id in users:
        raise HTTPException(status_code=409, detail="User already exists")
    
    # Set permissions based on role
    user.permissions = get_role_permissions(user.role)
    
    users[user.user_id] = user.dict()
    return user


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**users[user_id])


@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate user and return token"""
    # Find user by email and tenant
    user = None
    for u in users.values():
        if u["email"] == request.email and u["tenant_id"] == request.tenant_id:
            user = u
            break
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=403,
            detail="User account is inactive"
        )
    
    # Check tenant
    if request.tenant_id not in tenants:
        raise HTTPException(
            status_code=404,
            detail="Tenant not found"
        )
    
    tenant = tenants[request.tenant_id]
    if not tenant["is_active"]:
        raise HTTPException(
            status_code=403,
            detail="Tenant is inactive"
        )
    
    # Generate token
    token = generate_jwt_token(
        user["user_id"],
        user["tenant_id"],
        user["role"]
    )
    
    # Create session
    session_id = f"SESSION-{hashlib.md5(token.encode()).hexdigest()[:16]}"
    session = Session(
        session_id=session_id,
        user_id=user["user_id"],
        tenant_id=user["tenant_id"],
        token=token,
        expires_at=datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    )
    sessions[session_id] = session.dict()
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user=User(**user),
        tenant=Tenant(**tenant)
    )


@app.post("/validate", response_model=TokenValidation)
async def validate_token(
    authorization: str = Header(..., alias="Authorization")
):
    """Validate JWT token"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid authorization header")
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    try:
        payload = decode_jwt_token(token)
        
        user_id = payload.get("user_id")
        if user_id not in users:
            raise HTTPException(status_code=404, detail="User not found")
        
        user = users[user_id]
        
        return TokenValidation(
            valid=True,
            user_id=user_id,
            tenant_id=payload.get("tenant_id"),
            role=payload.get("role"),
            permissions=user.get("permissions", []),
            expires_at=datetime.fromtimestamp(payload.get("exp"))
        )
    except HTTPException:
        raise
    except Exception as e:
        return TokenValidation(valid=False)


@app.post("/logout")
async def logout(
    authorization: str = Header(..., alias="Authorization")
):
    """Logout user (invalidate session)"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid authorization header")
    
    token = authorization[7:]
    
    # Remove session
    for session_id, session in list(sessions.items()):
        if session.get("token") == token:
            del sessions[session_id]
    
    return {"message": "Logged out successfully"}


@app.get("/permissions/{user_id}")
async def get_user_permissions(user_id: str):
    """Get user permissions"""
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users[user_id]
    return {
        "user_id": user_id,
        "role": user["role"],
        "permissions": user["permissions"]
    }


@app.post("/check-permission")
async def check_user_permission(
    permission: Permission,
    authorization: str = Header(..., alias="Authorization")
):
    """Check if current user has specific permission"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid authorization header")
    
    token = authorization[7:]
    payload = decode_jwt_token(token)
    
    user_id = payload.get("user_id")
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users[user_id]
    has_permission = check_permission(User(**user), permission)
    
    return {
        "user_id": user_id,
        "permission": permission,
        "has_permission": has_permission
    }


@app.get("/sessions")
async def list_sessions(
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None
):
    """List active sessions (admin only)"""
    filtered_sessions = sessions.values()
    
    if user_id:
        filtered_sessions = [s for s in filtered_sessions if s.get("user_id") == user_id]
    
    if tenant_id:
        filtered_sessions = [s for s in filtered_sessions if s.get("tenant_id") == tenant_id]
    
    return {
        "sessions": [
            {
                "session_id": s["session_id"],
                "user_id": s["user_id"],
                "tenant_id": s["tenant_id"],
                "created_at": s["created_at"],
                "expires_at": s["expires_at"],
                "last_activity": s["last_activity"]
            }
            for s in filtered_sessions
        ],
        "total": len(filtered_sessions)
    }


@app.delete("/sessions/{session_id}")
async def revoke_session(session_id: str):
    """Revoke a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del sessions[session_id]
    return {"message": "Session revoked"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
