from pathlib import Path
from src.db import connect


def run_sql_files(paths) -> None:
    with connect() as conn, conn.cursor() as cur:
        for p in paths:
            cur.execute(Path(p).read_text())


def run_sql_dir(directory) -> None:
    run_sql_files(sorted(Path(directory).glob("*.sql")))
