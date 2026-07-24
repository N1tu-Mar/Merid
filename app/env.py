"""Load .env from the repo root into os.environ at import time.

Without this, the backend only sees keys exported in the shell — in practice
it ran with NO keys at all, so Fireworks extraction failed (every upload
became a featureless ESCALATE) and the Daytona sandbox path never executed
(sandboxed=0 on every referral). Imported from app/__init__.py so any entry
point (`uvicorn app.main`, `python -m app.seed`, `python -m evals.run`) gets
the same environment.

Deliberately dependency-free (no python-dotenv): parses simple KEY=VALUE
lines, ignores comments/blanks, and never overrides variables already set in
the real environment (shell always wins).
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def load_env(path: Path = _ENV_PATH) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if key and value and key not in os.environ:
            os.environ[key] = value


def ensure_ca_bundle() -> None:
    """Point the stdlib/requests TLS stack at certifi when the OS has no
    default CA file.

    On a python.org macOS install `ssl.get_default_verify_paths().cafile` is
    None until "Install Certificates.command" has been run. httpx bundles
    certifi so Fireworks calls work regardless, but the Daytona SDK goes
    through urllib3/requests, which fall back to that empty default and fail
    every sandbox create with CERTIFICATE_VERIFY_FAILED — read as "Daytona
    is down" rather than "this laptop has no trust store".

    This does not weaken verification: it selects certifi's standard CA
    bundle, the same set requests would normally use. Never overrides an
    operator's own setting.
    """
    import ssl

    if ssl.get_default_verify_paths().cafile:
        return
    try:
        import certifi
    except ImportError:
        return
    bundle = certifi.where()
    for var in ("SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"):
        os.environ.setdefault(var, bundle)


load_env()
ensure_ca_bundle()
