"""Minimal .env reader.

Values already present in the real environment always win, so a container or CI setting is
never overwritten by a developer's local file. No third-party dependency is used.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_env_file(path: Path | str | None = None) -> dict[str, str]:
    """Load KEY=VALUE lines from .env into os.environ. Returns the keys it set."""
    env_path = Path(path) if path else PROJECT_ROOT / ".env"
    if not env_path.is_file():
        return {}
    loaded: dict[str, str] = {}
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip().removeprefix("export ").strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
            loaded[key] = value
    return loaded
