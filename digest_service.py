"""Build a developer-tools digest and publish it when there is useful news."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Literal, Protocol

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from infrai_client import InfraiClient, InfraiError


class BuildEvent(BaseModel):
    project: str
    status: Literal["passed", "failed"]
    revision: str


class ReleaseOperation(BaseModel):
    package: str
    version: str
    channel: Literal["stable", "preview"] = "stable"


class Diagnostic(BaseModel):
    tool: str
    severity: Literal["info", "warning", "error"]
    message: str


class DigestRequest(BaseModel):
    week_ending: str
    audience: str = Field(min_length=1)
    builds: list[BuildEvent] = Field(default_factory=list)
    releases: list[ReleaseOperation] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class DigestResult(BaseModel):
    outcome: Literal["queued", "skipped"]
    digest_key: str | None = None
    highlights: int


class DigestPublisher(Protocol):
    def publish_digest(self, payload: dict[str, object], digest_key: str) -> None:
        return None


def noteworthy_count(request: DigestRequest) -> int:
    failed_builds = sum(build.status == "failed" for build in request.builds)
    stable_releases = sum(release.channel == "stable" for release in request.releases)
    actionable_diagnostics = sum(
        diagnostic.severity in {"warning", "error"}
        for diagnostic in request.diagnostics
    )
    return failed_builds + stable_releases + actionable_diagnostics


def queue_weekly_digest(
    request: DigestRequest, publisher: DigestPublisher
) -> DigestResult:
    highlights = noteworthy_count(request)
    if highlights == 0:
        return DigestResult(outcome="skipped", highlights=0)

    digest_key = f"{request.week_ending}:{request.audience}"
    payload: dict[str, object] = {
        "digest_key": digest_key,
        "week_ending": request.week_ending,
        "audience": request.audience,
        "highlights": highlights,
        "builds": [event.model_dump() for event in request.builds],
        "releases": [event.model_dump() for event in request.releases],
        "diagnostics": [event.model_dump() for event in request.diagnostics],
        "queued_at": datetime.now(timezone.utc).isoformat(),
    }
    publisher.publish_digest(payload, digest_key)
    return DigestResult(
        outcome="queued", digest_key=digest_key, highlights=highlights
    )


def load_digest_request() -> DigestRequest:
    input_path = Path(os.environ.get("DIGEST_INPUT_FILE", "digest-input.json"))
    return DigestRequest.model_validate_json(input_path.read_text(encoding="utf-8"))


app = FastAPI(title="Developer tools weekly digest")


@app.post("/jobs/weekly-digest", response_model=DigestResult)
def weekly_digest() -> DigestResult:
    try:
        return queue_weekly_digest(load_digest_request(), InfraiClient())
    except InfraiError as error:
        client_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=client_status, detail=error.detail) from error
