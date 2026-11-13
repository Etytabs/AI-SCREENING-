import pytest

from services.auth.demo_auth import (
    DemoAuthentication,
    DemoAuthenticationDisabled,
    DemoWorkspace,
    InvalidDemoCredentials,
)


def test_demo_credentials_create_workspace_bound_sessions():
    auth = DemoAuthentication(enabled=True)
    applicant_token, applicant = auth.create_session(
        DemoWorkspace.APPLICANT,
        "applicant@shakahive.demo",
        "Applicant123!",
    )
    admin_token, admin = auth.create_session(
        DemoWorkspace.GRANT_ADMINISTRATOR,
        "admin@shakahive.demo",
        "Admin123!",
    )

    assert applicant.workspace == DemoWorkspace.APPLICANT
    assert applicant.user_id == "demo-applicant"
    assert admin.workspace == DemoWorkspace.GRANT_ADMINISTRATOR
    assert admin.user_id == "demo-grant-administrator"
    assert auth.resolve(applicant_token) == applicant
    assert auth.resolve(admin_token) == admin


@pytest.mark.parametrize(
    ("workspace", "email", "password"),
    [
        (DemoWorkspace.APPLICANT, "admin@shakahive.demo", "Admin123!"),
        (DemoWorkspace.GRANT_ADMINISTRATOR, "applicant@shakahive.demo", "Applicant123!"),
        (DemoWorkspace.APPLICANT, "applicant@shakahive.demo", "wrong"),
    ],
)
def test_workspace_mismatch_and_invalid_password_are_rejected(workspace, email, password):
    with pytest.raises(InvalidDemoCredentials):
        DemoAuthentication(enabled=True).create_session(workspace, email, password)


def test_non_ascii_invalid_credentials_are_rejected_without_comparison_error():
    with pytest.raises(InvalidDemoCredentials):
        DemoAuthentication(enabled=True).create_session(
            DemoWorkspace.APPLICANT,
            "applicant@shakahive.demoé",
            "Applicant123!",
        )


def test_demo_auth_can_be_disabled_and_cannot_be_enabled_in_production():
    with pytest.raises(DemoAuthenticationDisabled):
        DemoAuthentication(enabled=False).create_session(
            DemoWorkspace.APPLICANT,
            "applicant@shakahive.demo",
            "Applicant123!",
        )
    with pytest.raises(RuntimeError, match="must not be enabled in production"):
        DemoAuthentication(enabled=True, environment="production")


def test_sessions_expire_and_can_be_revoked(monkeypatch):
    now = [100.0]
    monkeypatch.setattr("services.auth.demo_auth.time.monotonic", lambda: now[0])
    auth = DemoAuthentication(enabled=True)
    token, principal = auth.create_session(
        DemoWorkspace.APPLICANT,
        "applicant@shakahive.demo",
        "Applicant123!",
    )
    assert auth.resolve(token) == principal

    auth.revoke(token)
    assert auth.resolve(token) is None

    token, _ = auth.create_session(
        DemoWorkspace.APPLICANT,
        "applicant@shakahive.demo",
        "Applicant123!",
    )
    now[0] += auth.session_ttl_seconds
    assert auth.resolve(token) is None
