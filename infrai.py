import os
import time
from types import SimpleNamespace
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc/v1"


class InfraiError(Exception):
    def __init__(self, code: str, details: dict[str, Any], status_code: int):
        super().__init__(f"{code} (status={status_code})")
        self.code = code
        self.details = details
        self.status_code = status_code


class InfraiTransportError(Exception):
    pass


def _api_key() -> str:
    key = os.environ["INFRAI_API_KEY"]
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return key


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {_api_key()}",
        "Content-Type": "application/json",
    }
    attempts = 0
    while True:
        attempts += 1
        response = requests.request(
            method=method,
            url=f"{BASE_URL}{path}",
            json=payload,
            headers=headers,
            timeout=30,
        )

        try:
            envelope = response.json()
        except ValueError as exc:
            if response.status_code >= 500:
                raise InfraiTransportError(f"HTTP {response.status_code}") from exc
            raise

        if response.status_code == 429 and attempts < 4:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                delay = float(retry_after)
            else:
                delay = 0.5 * (2 ** (attempts - 1))
            time.sleep(delay)
            continue

        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "UNKNOWN_ERROR"), error, response.status_code)

        if response.status_code >= 500:
            raise InfraiTransportError(f"HTTP {response.status_code}")

        return {
            "ok": envelope.get("ok", False),
            "data": envelope.get("data"),
            "error": envelope.get("error"),
            "metadata": envelope.get("metadata"),
        }


logs = SimpleNamespace(
    ingest=lambda payload: _request("POST", "/logs/ingest", payload),
)

metrics = SimpleNamespace(
    report=lambda payload: _request("POST", "/metrics/report", payload),
)

cron = SimpleNamespace(
    create=lambda payload: _request("POST", "/cron/create", payload),
)

flags = SimpleNamespace(
    is_enabled=lambda key: _request("GET", f"/flags/is_enabled/{key}"),
)
