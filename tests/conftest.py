"""Test isolation.

Every test run gets a fresh throwaway SQLite database instead of the demo's
meridian.db. Without this, tests that insert fixed row IDs (e.g. the intake
demo calls "demo-call-silent" et al.) collide with rows left by a previous
run — an IntegrityError — and they also pollute the real demo database.

The env var must be set BEFORE app.db is imported anywhere, so it lives at
module import time here: pytest loads conftest.py before collecting any test
module, and app.db reads MERIDIAN_DB_URL when its engine is first created.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_TEST_DB = Path(tempfile.gettempdir()) / "meridian_test.db"
# Start each session from a clean slate.
if _TEST_DB.exists():
    _TEST_DB.unlink()
os.environ["MERIDIAN_DB_URL"] = f"sqlite:///{_TEST_DB}"

# Same reasoning, for the extraction cache. Tests stub httpx and vary the
# response for the *same* request payload, which is exactly what that cache
# keys on — leaving it on would serve one test's stubbed answer to another
# and turn real failures into spurious passes. Set before services.extract
# is imported anywhere, for the same reason as the DB URL above.
os.environ["FIREWORKS_CACHE"] = "0"

# The test suite must never reach the network. Once a real key exists in
# .env, app.env loads it and services/referral/extract.py captures it into a
# module constant at import time — so a module-level pop in one test file
# is too late if any earlier module already imported it. That silently
# turned fail-safe tests into live API calls, and one started passing for
# the wrong reason (a real extraction succeeding instead of the absent-key
# path being exercised).
#
# Blanking it here, before anything imports, makes "no key" the default for
# every test. Tests that need a key monkeypatch one in, which is explicit
# and cannot leak across modules.
os.environ["FIREWORKS_API_KEY"] = ""
os.environ["ELEVENLABS_API_KEY"] = ""
os.environ["DAYTONA_API_KEY"] = ""

import pytest

from app.db import init_db


@pytest.fixture(scope="session", autouse=True)
def _isolated_db():
    init_db()
    yield
    if _TEST_DB.exists():
        _TEST_DB.unlink()
