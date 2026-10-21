"""Shared plumbing for the live examples: environment settings, login, time window.

Credentials are read only from environment variables and are never printed.
TLS verification is always on; set COHESITY_CA_BUNDLE for a private certificate authority.
"""
from __future__ import annotations

import os
import sys
import time
from collections.abc import Mapping

from cohesity_rest_helper import CohesityUserAuthentication

GIB = 1024 ** 3
DAY_MSECS = 86_400_000
REQUIRED_VARIABLES = ("COHESITY_HOST", "COHESITY_USER", "COHESITY_PASSWORD")


def read_settings(environ: Mapping[str, str] | None = None) -> dict:
    """Collect connection settings from the environment (``os.environ`` by default)."""
    environ = os.environ if environ is None else environ
    missing = [name for name in REQUIRED_VARIABLES if not environ.get(name)]
    if missing:
        raise SystemExit(
            "Set these environment variables first: " + ", ".join(missing)
            + "\n(optional: COHESITY_DOMAIN, default LOCAL; COHESITY_CA_BUNDLE for a private CA)"
        )
    return {
        "host": environ["COHESITY_HOST"],
        "user": environ["COHESITY_USER"],
        "password": environ["COHESITY_PASSWORD"],
        "domain": environ.get("COHESITY_DOMAIN", "LOCAL"),
        # A CA bundle path, or True for the system trust store. Never False.
        "verify": environ.get("COHESITY_CA_BUNDLE") or True,
    }


def login(settings: dict) -> str:
    """Request a bearer token using the settings from :func:`read_settings`."""
    auth = CohesityUserAuthentication(settings["host"], verify=settings["verify"])
    return auth.get_bearer_token(settings["user"], settings["password"], settings["domain"])


def make_client(client_class, token: str, settings: dict):
    """Build a library object (stats, tenants, cluster or vault client) for this cluster."""
    return client_class(token, settings["host"], verify=settings["verify"])


def time_window(days: int, now_msecs: int | None = None) -> tuple[int, int]:
    """Return ``(start, end)`` in epoch milliseconds covering the last ``days`` days."""
    if days < 1:
        raise SystemExit("--days must be at least 1")
    end = int(time.time() * 1000) if now_msecs is None else now_msecs
    return end - days * DAY_MSECS, end


def gib(value) -> str:
    """Format a byte count as GiB for display."""
    return f"{value / GIB:,.1f} GiB"


def fail(message: str) -> int:
    """Print an error (never credentials) and return a non-zero exit code."""
    print(f"error: {message}", file=sys.stderr)
    return 1
