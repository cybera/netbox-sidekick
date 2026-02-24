import json
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional


def now_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


class ClickHouseHTTP:
    def __init__(self, base_url: str, user: str, password: str, database: str):
        parsed = urllib.parse.urlsplit(base_url)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError(
                f"Invalid CLICKHOUSE_URL (expected http(s)://host:port): {base_url!r}"
            )
        self.base_url = urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, "", "", "")
        ).rstrip("/")
        self.user = user
        self.password = password
        self.database = database

    def _request(self, url: str, data: Optional[bytes], content_type: Optional[str] = None) -> str:
        req = urllib.request.Request(url, data=data, method="POST")
        if self.user:
            req.add_header("X-ClickHouse-User", self.user)
        if self.password:
            req.add_header("X-ClickHouse-Key", self.password)
        if content_type:
            req.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                if resp.status >= 400:
                    raise RuntimeError(f"ClickHouse error HTTP {resp.status}: {body}")
                return body
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
            raise RuntimeError(
                "ClickHouse HTTP request failed. "
                f"url={url!r} status={getattr(e, 'code', 'unknown')} body={body!r}. "
                "Verify CLICKHOUSE_URL points to the HTTP interface (usually http://127.0.0.1:8123)."
            ) from e

    def execute(self, query: str) -> str:
        url = f"{self.base_url}/"
        return self._request(url, data=query.encode("utf-8"), content_type="text/plain; charset=utf-8")

    def execute_scalar_u8(self, query: str) -> int:
        out = self.execute(query + "\nFORMAT TabSeparated")
        s = out.strip().split("\t")[0].strip()
        return int(s) if s else 0

    def insert_json_each_row(self, table: str, rows: Iterable[Dict[str, Any]]) -> None:
        payload = "".join(
            json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n" for r in rows
        ).encode("utf-8")
        query = f"INSERT INTO {table} FORMAT JSONEachRow"
        params = {"query": query}
        url = f"{self.base_url}/?{urllib.parse.urlencode(params)}"
        self._request(url, data=payload, content_type="application/json")
