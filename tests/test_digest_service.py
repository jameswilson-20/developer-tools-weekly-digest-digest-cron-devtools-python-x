from digest_service import DigestRequest, queue_weekly_digest


class RecordingPublisher:
    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, object], str]] = []

    def publish_digest(self, payload: dict[str, object], digest_key: str) -> None:
        self.calls.append((payload, digest_key))


def test_queues_failed_build_stable_release_and_warning() -> None:
    publisher = RecordingPublisher()
    request = DigestRequest.model_validate(
        {
            "week_ending": "2026-09-04",
            "audience": "sdk-maintainers",
            "builds": [
                {"project": "python-sdk", "status": "failed", "revision": "a12bc34"},
                {"project": "cli", "status": "passed", "revision": "d56ef78"},
            ],
            "releases": [
                {"package": "dev-cli", "version": "2.4.0", "channel": "stable"},
                {"package": "dev-cli", "version": "2.5.0b1", "channel": "preview"},
            ],
            "diagnostics": [
                {"tool": "typecheck", "severity": "warning", "message": "2 slow modules"},
                {"tool": "formatter", "severity": "info", "message": "clean"},
            ],
        }
    )

    result = queue_weekly_digest(request, publisher)

    assert result.outcome == "queued"
    assert result.highlights == 3
    assert result.digest_key == "2026-09-04:sdk-maintainers"
    assert len(publisher.calls) == 1
    payload, key = publisher.calls[0]
    assert key == result.digest_key
    assert payload["highlights"] == 3


def test_skips_a_quiet_week() -> None:
    publisher = RecordingPublisher()
    request = DigestRequest.model_validate(
        {
            "week_ending": "2026-09-04",
            "audience": "sdk-maintainers",
            "builds": [
                {"project": "python-sdk", "status": "passed", "revision": "a12bc34"}
            ],
            "releases": [],
            "diagnostics": [
                {"tool": "formatter", "severity": "info", "message": "clean"}
            ],
        }
    )

    result = queue_weekly_digest(request, publisher)

    assert result.outcome == "skipped"
    assert result.highlights == 0
    assert publisher.calls == []
