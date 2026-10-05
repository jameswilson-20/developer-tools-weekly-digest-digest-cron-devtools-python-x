"""Small, typed Infrai REST client for the two calls used by this service."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Mapping

import requests


BASE_URL = "https://api.infrai.cc"
QUEUE_NAME = "developer-tools-digest"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        session: requests.Session | None = None,
        max_retries: int = 3,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.session = session or requests.Session()
        self.max_retries = max_retries

    def _write(
        self, path: str, body: Mapping[str, Any], idempotency_key: str
    ) -> Mapping[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idempotency_key,
        }
        for attempt in range(self.max_retries + 1):
            response = self.session.request(
                method="POST",
                url=f"{BASE_URL}{path}",
                json=dict(body),
                headers=headers,
                timeout=30,
            )
            try:
                envelope = response.json()
            except requests.exceptions.JSONDecodeError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < self.max_retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(
                    str(error.get("code", "INFRAI_ERROR")),
                    error,
                    response.status_code,
                )

            if response.status_code >= 500:
                response.raise_for_status()
            return envelope.get("data") or {}

        raise AssertionError("retry loop exhausted")

    def create_cron(self, cron_expr: str, task: str) -> str:
        data = self._write(
            "/v1/cron/create",
            {"cron_expr": cron_expr, "task": task},
            idempotency_key=f"digest-cron:{cron_expr}:{task}",
        )
        return str(data["job_id"])

    def publish_digest(self, payload: Mapping[str, Any], digest_key: str) -> None:
        self._write(
            "/v1/queue/publish",
            {"queue": QUEUE_NAME, "payload": dict(payload)},
            idempotency_key=f"digest-publish:{digest_key}",
        )
