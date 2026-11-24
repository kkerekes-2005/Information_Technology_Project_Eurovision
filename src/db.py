"""Database access for the queries and the app.

Every other file writes: from db import run_query
and never creates its own engine. Python only sends the SQL with its parameters
and returns the rows. Nothing is calculated here.
"""
from pathlib import Path

from sqlalchemy import URL, create_engine, text

HOST = "localhost"
PORT = 5432
DATABASE = "eurovision"
USER = "postgres"

# Paths are relative to the repository root, wherever the program is started from.
ROOT = Path(__file__).resolve().parent.parent
PASSWORD_FILE = ROOT / "password.txt"

with open(PASSWORD_FILE) as f:
    _password = f.read().strip()

engine = create_engine(
    URL.create("postgresql+psycopg2", USER, _password, HOST, PORT, DATABASE),
    pool_pre_ping=True,
)


def run_query(sql, params=None):
    """Run one SQL statement with named parameters and return a list of dictionaries."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings()]


def read_sql(relative_path):
    """Return the text of a SQL file, for example 'sql/app/countries.sql'."""
    with open(ROOT / relative_path, encoding="utf-8") as f:
        return f.read()


def read_query(name):
    """Return the text of sql/queries/<name>.sql."""
    return read_sql(f"sql/queries/{name}.sql")
