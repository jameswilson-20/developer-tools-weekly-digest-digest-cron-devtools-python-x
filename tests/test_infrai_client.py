from unittest.mock import Mock

from infrai_client import InfraiClient, QUEUE_NAME


def test_publish_digest_supplies_queue_and_payload() -> None:
    client = InfraiClient(api_key="test-key")
    client._write = Mock(return_value={})
    payload = {"highlights": 3}

    client.publish_digest(payload, "2026-09-04:sdk-maintainers")

    client._write.assert_called_once_with(
        "/v1/queue/publish",
        {"queue": QUEUE_NAME, "payload": payload},
        idempotency_key="digest-publish:2026-09-04:sdk-maintainers",
    )
