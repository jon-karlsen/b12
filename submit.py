"""Application submitter for the B12 Full Stack Engineer role.

Builds a canonical JSON payload, signs it with HMAC-SHA256, POSTs it to the
B12 application endpoint, and prints the returned receipt. Designed to run
from GitHub Actions so the submission itself carries a verifiable CI trail.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SUBMISSION_URL = "https://b12.io/apply/submission"
SIGNING_SECRET = b"hello-there-from-b12"
RECEIPT_PATH = Path("receipt.txt")

APPLICANT_VARS = ("APPLICANT_NAME", "APPLICANT_EMAIL", "RESUME_LINK")
GITHUB_VARS = ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")


def canonical_json(payload: dict[str, str]) -> bytes:
    """Serialize payload with keys sorted, no extra whitespace, UTF-8 encoded."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sign(body: bytes, secret: bytes = SIGNING_SECRET) -> str:
    """Return the value for the X-Signature-256 header."""
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def build_payload(
    *,
    name: str,
    email: str,
    resume_link: str,
    repository_link: str,
    action_run_link: str,
    now: datetime | None = None,
) -> dict[str, str]:
    ts = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
    return {
        "action_run_link": action_run_link,
        "email": email,
        "name": name,
        "repository_link": repository_link,
        "resume_link": resume_link,
        "timestamp": ts,
    }


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        sys.exit(f"missing required env var: {name}")

    return value


def repository_link_from_env() -> str:
    explicit = os.environ.get("REPOSITORY_LINK")
    if explicit:
        return explicit

    server_var, repo_var, _ = GITHUB_VARS
    return f"{_require_env(server_var)}/{_require_env(repo_var)}"


def action_run_link_from_env() -> str:
    explicit = os.environ.get("ACTION_RUN_LINK")
    if explicit:
        return explicit

    server, repo, run_id = (_require_env(v) for v in GITHUB_VARS)
    return f"{server}/{repo}/actions/runs/{run_id}"


def submit(body: bytes, signature: str) -> dict:
    request = urllib.request.Request(
        SUBMISSION_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": signature,
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")
        sys.exit(f"submission failed: HTTP {e.code} {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"submission failed: {e.reason}")


def main() -> int:
    name, email, resume_link = (_require_env(v) for v in APPLICANT_VARS)
    payload = build_payload(
        name=name,
        email=email,
        resume_link=resume_link,
        repository_link=repository_link_from_env(),
        action_run_link=action_run_link_from_env(),
    )
    body = canonical_json(payload)
    signature = sign(body)

    if os.environ.get("DRY_RUN") == "1":
        print("dry run: not sending", file=sys.stderr)
        print(f"POST {SUBMISSION_URL}", file=sys.stderr)
        print(f"X-Signature-256: {signature}", file=sys.stderr)
        print(f"body: {body.decode('utf-8')}", file=sys.stderr)
        return 0

    response = submit(body, signature)
    if not response.get("success"):
        sys.exit(f"submission rejected: {response}")

    receipt = response["receipt"]
    RECEIPT_PATH.write_text(receipt + "\n", encoding="utf-8")
    print(receipt)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
