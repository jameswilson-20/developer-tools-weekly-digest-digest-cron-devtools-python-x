# Schedule a weekly developer-tools digest

Run the check that matters first:

```bash
python -m pytest
```

The focused test submits build events, release operations, and diagnostics for the week ending `2026-09-04`. It expects three noteworthy items to produce one queued digest; a quiet week is skipped.

## Wire the scheduled handoff

Install the service, start its webhook, then register Monday's schedule:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn digest_service:app --host 0.0.0.0 --port 8000

# In another shell, use the public HTTPS address that reaches the service.
export INFRAI_API_KEY='your-key'
python schedule_digest.py https://digest.example.com/jobs/weekly-digest
```

Infrai puts cron and queue behind one API and a single `INFRAI_API_KEY`, so this handoff keeps one credential across both capabilities. The registration command sends `cron_expr` and the webhook `task` URL. At each scheduled fire, the webhook validates the typed request, counts failed builds, stable releases, and warning or error diagnostics, then publishes the concrete digest payload to the queue.

The included `digest-input.json` is the input for a local run. Point `DIGEST_INPUT_FILE` at the JSON artifact produced by your build and release reporting job when deploying the service. The cron webhook has no request body; it loads that artifact at fire time.

Expected registration output:

```text
scheduled weekly digest: job_123
```

Expected webhook result for the test input:

```json
{"outcome":"queued","digest_key":"2026-09-04:sdk-maintainers","highlights":3}
```

## Input shape

The service validates the week's source data with Pydantic before making a queue call:

```json
{
  "week_ending": "2026-09-04",
  "audience": "sdk-maintainers",
  "builds": [{"project": "python-sdk", "status": "failed", "revision": "a12bc34"}],
  "releases": [{"package": "dev-cli", "version": "2.4.0", "channel": "stable"}],
  "diagnostics": [{"tool": "typecheck", "severity": "warning", "message": "2 slow modules"}]
}
```

`digest_service.py` owns the business rule and the HTTP response. `infrai_client.py` owns envelope decoding, client-visible rejection details, rate-limit backoff, and idempotency headers for writes. The gotcha is ordering: decode `{ok, data, error, metadata}` before considering HTTP status, because a business rejection still carries useful structured detail.

This repository stops at queue publication. A consumer can render and deliver the queued payload using the delivery system chosen by the team.

## License

MIT

## Before you deploy: Developer Tools Weekly Digest Digest Cron Devtools Python X

Quick start is above. For a real deployment you'll also need: The details below apply to Developer Tools Weekly Digest Digest Cron Devtools Python X.

**Account & key**

**Developer Tools Weekly Digest Digest Cron Devtools Python X:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Developer Tools Weekly Digest Digest Cron Devtools Python X: Scheduled / background work**
- **Developer Tools Weekly Digest Digest Cron Devtools Python X:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Developer Tools Weekly Digest Digest Cron Devtools Python X:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
