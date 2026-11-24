"""Copy the three raw CSV files, unchanged, into the staging tables.

    python scripts/load_staging.py

Runs sql/staging.sql (drops and recreates the staging tables) and then sends each
file with COPY. Nothing is cleaned here: the staging tables are for profiling the
raw data with SQL. Empty cells arrive as NULL.
"""
import argparse

import psycopg2
from psycopg2 import sql

# staging table -> raw file
FILES = {
    "contestants": "contestants.csv",
    "votes": "votes.csv",
    "betting_offices": "betting_offices.csv",
}


def main():
    parser = argparse.ArgumentParser(description="Load the raw CSV files into staging.")
    parser.add_argument("--raw", default="data/raw", help="folder with the three CSV files")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=5432, type=int)
    parser.add_argument("--dbname", default="eurovision")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--password-file", default="password.txt")
    args = parser.parse_args()

    with open(args.password_file) as f:
        password = f.read().strip()
    with open("sql/staging.sql", encoding="utf-8") as f:
        staging_sql = f.read()

    conn = psycopg2.connect(host=args.host, port=args.port, dbname=args.dbname,
                            user=args.user, password=password)
    with conn:
        with conn.cursor() as cur:
            cur.execute(staging_sql)
            for table, file_name in FILES.items():
                name = sql.Identifier("staging", table)
                copy_sql = sql.SQL("COPY {} FROM STDIN WITH (FORMAT csv, HEADER true)")
                with open(f"{args.raw}/{file_name}", encoding="utf-8") as f:
                    cur.copy_expert(copy_sql.format(name), f)
                cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(name))
                print(f"staging.{table:16} {cur.fetchone()[0]:6} rows")
    conn.close()


if __name__ == "__main__":
    main()
