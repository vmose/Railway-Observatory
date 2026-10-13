import csv
import hashlib
import io
import pathlib
import zipfile

import requests

from src.config import auth_headers
from src.db import connect
from src.validation.validate_feed import REQUIRED, validate_zip


def _read_source(source: str) -> bytes:
    if source.startswith(("http://", "https://")):
        r = requests.get(source, headers=auth_headers(), timeout=120)
        r.raise_for_status()
        return r.content
    return pathlib.Path(source).read_bytes()


def load_gtfs(source: str):
    """Download/read a GTFS zip, validate it, and load it into raw.* tables.

    Idempotent: a feed with an identical SHA-256 is skipped. Returns the new
    feed_id, or None if this exact feed was already loaded."""
    data = _read_source(source)
    sha = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        validate_zip(zf)
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO raw.feed_versions (source, sha256) VALUES (%s, %s) "
                "ON CONFLICT (sha256) DO NOTHING RETURNING feed_id",
                (source, sha),
            )
            row = cur.fetchone()
            if row is None:
                return None
            feed_id = row[0]
            for fname, cols in REQUIRED.items():
                table = "raw." + fname[:-4]
                buf = io.StringIO()
                writer = csv.writer(buf)
                with zf.open(fname) as f:
                    for rec in csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig")):
                        writer.writerow([feed_id] + [rec.get(c) or "" for c in cols])
                buf.seek(0)
                cur.copy_expert(
                    f"COPY {table} (feed_id, {', '.join(cols)}) FROM STDIN WITH (FORMAT csv)", buf
                )
            return feed_id
