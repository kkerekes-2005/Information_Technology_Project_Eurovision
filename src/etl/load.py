"""Load the Eurovision data into PostgreSQL in one transaction.

Before running: create the database and run sql/schema.sql (the tables must be empty).

    python src/etl/load.py            clean the raw files and load every table
    python src/etl/load.py --fail     same, with one wrong row, to show the rollback

The whole load is one transaction: either every table is filled or none is.
"""
import argparse

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values

from clean import build_tables


def connect(args):
    try:
        with open(args.password_file) as f:
            password = f.read().strip()
    except FileNotFoundError:
        raise SystemExit(f"File {args.password_file} not found. Create it with only the "
                         "password of the PostgreSQL user inside.")
    try:
        return psycopg2.connect(host=args.host, port=args.port, dbname=args.dbname,
                                user=args.user, password=password)
    except psycopg2.OperationalError as e:
        # Server not running, wrong password or database that does not exist.
        raise SystemExit(f"Could not connect to PostgreSQL: {str(e).strip()}")


def count_rows(conn, table):
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
        return cur.fetchone()[0]


def insert_table(cur, table, columns, rows):
    query = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
        sql.Identifier(table), sql.SQL(", ").join(sql.Identifier(c) for c in columns))
    execute_values(cur, query.as_string(cur), rows, page_size=1000)


def main():
    parser = argparse.ArgumentParser(description="Load the Eurovision data into PostgreSQL.")
    parser.add_argument("--contestants", default="data/raw/contestants.csv")
    parser.add_argument("--votes", default="data/raw/votes.csv")
    parser.add_argument("--betting", default="data/raw/betting_offices.csv")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=5432, type=int)
    parser.add_argument("--dbname", default="eurovision")
    parser.add_argument("--user", default="postgres")
    parser.add_argument("--password-file", default="password.txt")
    parser.add_argument("--fail", action="store_true",
                        help="add one vote for a country that does not exist")
    args = parser.parse_args()

    # 1. Read and clean the raw files. Nothing touches the database yet.
    tables, rules, review = build_tables(args.contestants, args.votes, args.betting)
    if args.fail:
        columns, rows = tables["vote"]
        tables["vote"] = (columns, rows + [(1, "se", "zz", 12, None, None)])

    conn = connect(args)

    # 2. The load only inserts rows, so the tables must exist and be empty.
    try:
        filled = [t for t in tables if count_rows(conn, t) > 0]
    except psycopg2.errors.UndefinedTable:
        conn.close()
        raise SystemExit("The tables do not exist yet. Run sql/schema.sql first.")
    conn.rollback()
    if filled:
        conn.close()
        raise SystemExit(f"These tables already have rows: {', '.join(filled)}. "
                         "Run sql/schema.sql first.")

    # 3. One transaction for all the tables, parents before children.
    try:
        with conn:
            with conn.cursor() as cur:
                for table, (columns, rows) in tables.items():
                    insert_table(cur, table, columns, rows)
                    print(f"inserted {len(rows):6} rows into {table}")
        print("COMMIT: the load is saved.")
    except psycopg2.Error as e:
        # "with conn" has already rolled the transaction back.
        print("ROLLBACK: nothing was loaded.")
        print("Error:", e.diag.message_primary)
        print("Detail:", e.diag.message_detail)

    # 4. Check: rows in each table against the rows that were prepared.
    print()
    print(f"{'table':13} {'prepared':>9} {'in database':>12}")
    for table, (_, rows) in tables.items():
        print(f"{table:13} {len(rows):9} {count_rows(conn, table):12}")
    conn.close()


if __name__ == "__main__":
    main()
