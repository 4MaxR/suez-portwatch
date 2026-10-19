"""Minimal client for IMF PortWatch's public ArcGIS FeatureServer layers.

Each layer serves at most 1,000 records per request, so `query` pages through results with
resultOffset, ordered by ObjectId so pages never overlap. No API key or sign-in is needed.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from .config import SERVICES

PAGE_SIZE = 1000
MIN_INTERVAL_S = 0.5


class PortWatchError(RuntimeError):
    pass


class Client:
    def __init__(self, timeout: float = 60.0) -> None:
        self.timeout = timeout
        self._last_call = 0.0

    def _request(self, url: str) -> dict:
        error = None
        for attempt in range(6):
            wait = MIN_INTERVAL_S - (time.monotonic() - self._last_call)
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            try:
                with urllib.request.urlopen(url, timeout=self.timeout) as resp:
                    payload = json.load(resp)
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504):
                    time.sleep(2 * (attempt + 1))
                    continue
                raise PortWatchError(f"HTTP {exc.code} for {url}: {exc.read()[:300]!r}") from exc
            except (urllib.error.URLError, TimeoutError):
                time.sleep(2 * (attempt + 1))
                continue
            # ArcGIS reports query errors inside a 200 response. On the large port layer a busy
            # server also answers this way ("Unable to perform query"), so retry before failing.
            if "error" in payload:
                error = payload["error"]
                time.sleep(5 * (attempt + 1))
                continue
            return payload
        raise PortWatchError(f"Gave up after repeated failures: {error or ''} ({url})")

    def layer_info(self, service: str) -> dict:
        return self._request(f"{SERVICES}/{service}/FeatureServer/0?f=json")

    def count(self, service: str, where: str) -> int:
        params = {"where": where, "returnCountOnly": "true", "f": "json"}
        url = f"{SERVICES}/{service}/FeatureServer/0/query?{urllib.parse.urlencode(params)}"
        return int(self._request(url)["count"])

    def query(self, service: str, where: str) -> list[dict]:
        """Every record matching `where`, as a list of attribute dicts.

        Checks the result against returnCountOnly so a silently truncated download fails loudly.
        """
        expected = self.count(service, where)
        rows: list[dict] = []
        while True:
            params = {
                "where": where,
                "outFields": "*",
                "returnGeometry": "false",
                "orderByFields": "ObjectId",
                "resultOffset": str(len(rows)),
                "resultRecordCount": str(PAGE_SIZE),
                "f": "json",
            }
            url = f"{SERVICES}/{service}/FeatureServer/0/query?{urllib.parse.urlencode(params)}"
            payload = self._request(url)
            page = [f["attributes"] for f in payload.get("features", [])]
            rows.extend(page)
            if not page or not payload.get("exceededTransferLimit"):
                break
        if len(rows) != expected:
            raise PortWatchError(f"{service} [{where}]: got {len(rows)} rows, expected {expected}")
        return rows
