import re
import sqlite3

DB_PATH = "delivery.db"
MAX_ROWS = 50


def validate_query(query: str) -> str:
    """Allow a single SELECT statement and nothing else."""
    q = query.strip().rstrip(";").strip()
    if not re.match(r"(?i)^select\b", q) or ";" in q:
        raise ValueError("Only a single SELECT statement is allowed")
    return q


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def get_schema() -> str:
    con = _connect()
    rows = con.execute("SELECT sql FROM sqlite_master WHERE type='table'").fetchall()
    con.close()
    return "\n".join(r[0] for r in rows if r[0])


def run_query(query: str) -> dict:
    q = validate_query(query)
    con = _connect()
    try:
        cur = con.execute(q)
        columns = [d[0] for d in cur.description]
        return {"columns": columns, "rows": cur.fetchmany(MAX_ROWS)}
    finally:
        con.close()
