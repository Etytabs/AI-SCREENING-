"""Short-lived, process-local authentication for synthetic product demonstrations."""
import hashlib
import hmac
import os
import secrets
import threading
import time
from dataclasses import dataclass
from enum import StrEnum


class DemoWorkspace(StrEnum):
    APPLICANT = "APPLICANT"
    GRANT_ADMINISTRATOR = "GRANT_ADMINISTRATOR"


@dataclass(frozen=True)
class DemoPrincipal:
    user_id: str
    email: str
    workspace: DemoWorkspace


@dataclass(frozen=True)
class _Session:
    principal: DemoPrincipal
    expires_at: float


class InvalidDemoCredentials(Exception):
    pass


class DemoAuthenticationDisabled(Exception):
    pass


class DemoAuthentication:
    session_ttl_seconds = 15 * 60

    # These are public demonstration credentials, never production credentials.
    _credentials = {
        DemoWorkspace.APPLICANT: (
            "applicant@shakahive.demo",
            "Applicant123!",
            "demo-applicant",
        ),
        DemoWorkspace.GRANT_ADMINISTRATOR: (
            "admin@shakahive.demo",
            "Admin123!",
            "demo-grant-administrator",
        ),
    }

    def __init__(self, *, enabled: bool, environment: str = "development") -> None:
        if enabled and environment.strip().lower() in {"production", "prod"}:
            raise RuntimeError("Demo authentication must not be enabled in production")
        self.enabled = enabled
        self._sessions: dict[str, _Session] = {}
        self._lock = threading.RLock()

    @classmethod
    def from_environment(cls) -> "DemoAuthentication":
        enabled = os.getenv("AI_SCREENING_DEMO_AUTH_ENABLED", "").strip().lower() in {
            "1", "true", "yes", "on",
        }
        environment = os.getenv("AI_SCREENING_ENVIRONMENT", "development")
        return cls(enabled=enabled, environment=environment)

    def create_session(
        self, workspace: DemoWorkspace, email: str, password: str
    ) -> tuple[str, DemoPrincipal]:
        if not self.enabled:
            raise DemoAuthenticationDisabled

        expected_email, expected_password, user_id = self._credentials[workspace]
        email_matches = hmac.compare_digest(
            email.strip().lower().encode("utf-8"), expected_email.encode("utf-8")
        )
        password_matches = hmac.compare_digest(
            password.encode("utf-8"), expected_password.encode("utf-8")
        )
        if not (email_matches and password_matches):
            raise InvalidDemoCredentials

        principal = DemoPrincipal(user_id=user_id, email=expected_email, workspace=workspace)
        token = secrets.token_urlsafe(32)
        now = time.monotonic()
        with self._lock:
            self._purge_expired(now)
            self._sessions[self._token_digest(token)] = _Session(
                principal=principal,
                expires_at=now + self.session_ttl_seconds,
            )
        return token, principal

    def resolve(self, token: str | None) -> DemoPrincipal | None:
        if not self.enabled or not token:
            return None
        now = time.monotonic()
        digest = self._token_digest(token)
        with self._lock:
            session = self._sessions.get(digest)
            if session is None:
                return None
            if session.expires_at <= now:
                del self._sessions[digest]
                return None
            return session.principal

    def revoke(self, token: str | None) -> None:
        if token:
            with self._lock:
                self._sessions.pop(self._token_digest(token), None)

    def _purge_expired(self, now: float) -> None:
        expired = [key for key, session in self._sessions.items() if session.expires_at <= now]
        for key in expired:
            del self._sessions[key]

    @staticmethod
    def _token_digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
