# Eurovision relational database

Project B of the Information Technology course. The Eurovision Song Contest dataset is turned into a normalised PostgreSQL database, loaded from Python in one transaction, queried in SQL and presented in a visualization app.

## Status

Work in progress. Deadline: 25 November 2026.

| Part | State |
|---|---|
| Cleaning of the raw files | Done: `src/etl/clean.py`, results in `docs/cleaning-log.md` |
| Download script | Done: `scripts/download_data.py` (the database itself is created by hand in pgAdmin) |
| SQL data profile | Done: `sql/profiling.sql`, results in `docs/data-profile.md` |
| ER diagram and relational model | Done: `docs/er-conceptual.png` (entities and relationships), `docs/er-diagram.png` (tables), `docs/relational-model.md` |
| Schema (`sql/schema.sql`) | Done |
| Load into PostgreSQL | Done: `src/etl/load.py`, one transaction, `--fail` shows the rollback |
| SQL queries | Done: 14 queries in `sql/queries/`, results in `docs/queries.md` |
| Visualization app | Done: `app/streamlit_app.py`, 8 charts and 5 tables, every filter a SQL parameter |
| Presentation | Done: `docs/eurovision-presentation.pptx`, 13 slides |
| Report | Done: `docs/report.pdf` (built from `docs/report-source.md` by `scripts/build_report.py`) and the editable `docs/report.docx` (`scripts/build_report_docx.py`) |

## Dataset

[The Eurovision Dataset](https://github.com/Spijkervet/eurovision-dataset) by Janne Spijkervet, release `2023`, DOI 10.5281/zenodo.4036457. The data comes from the EurovisionWorld fan site.

| File | Rows | Content |
|---|---|---|
| `contestants.csv` | 1,734 | One row per song entry, 1956 to 2023 |
| `votes.csv` | 51,354 | Points given by one country to another in one round |
| `betting_offices.csv` | 9,453 | Bookmaker odds per entry and round, 2015 to 2023 |

The raw files are not part of this repository. `python scripts/download_data.py` downloads them into `data/raw/`.

License of the dataset: Creative Commons Attribution 4.0 International (CC BY 4.0), as stated on its Zenodo record. The licence requires attribution, given here and in the report.

## Requirements

- PostgreSQL 16 and pgAdmin 4
- Python 3.10 or later
- Python packages: `psycopg2-binary`, `sqlalchemy`, `matplotlib`, `streamlit` (Altair, used for the Q07 chart, is installed with Streamlit)

The cleaning step uses only the Python standard library.

## Setup

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (macOS, Linux)
pip install psycopg2-binary sqlalchemy matplotlib streamlit
```

Create a file `password.txt` in the repository root that contains only the password of the PostgreSQL user. It is listed in `.gitignore` and must never be committed.

## Usage

### 0. Download the raw files (available)

```
python scripts/download_data.py
```

Fetches the three CSV files of release `2023` into `data/raw/`.

### 1. Clean the raw files (available)

```
python src/etl/clean.py --out data/clean --log docs/cleaning-log.md
```

Reads `data/raw/contestants.csv`, `data/raw/votes.csv` and `data/raw/betting_offices.csv`. Writes one CSV per table into `data/clean/` for inspection and regenerates the cleaning log with the rows affected by each rule. No database is needed. Other file locations can be given with `--contestants`, `--votes` and `--betting`.

### 2. Create the tables (available)

In pgAdmin, create a database named `eurovision`, open its Query Tool, open `sql/schema.sql` and run it. The script drops and recreates the ten tables, so it can be run again at any time.

### 3. Load the data (available)

```
python src/etl/load.py
```

Cleans the raw files and inserts every table in one transaction, then prints the rows prepared and the rows in the database for each table. The tables must be empty: run `sql/schema.sql` before every load. Connection options: `--host`, `--port`, `--dbname`, `--user`, `--password-file`.

```
python src/etl/load.py --fail
```

Adds one vote for a country that does not exist. The foreign key rejects it, the transaction is rolled back and every table stays empty.

### 4. Profile the raw data (available)

```
python scripts/load_staging.py
```

Copies the three raw files unchanged into all-text tables of the schema `staging`. Then run the queries of `sql/profiling.sql` in pgAdmin, one at a time. The results are written up in `docs/data-profile.md`.

### 5. Run the queries (available)

```
python scripts/run_queries.py
```

Runs Q01 to Q12 and Q14 with their example parameters and rewrites `docs/queries.md` with the SQL, a sample of each result and its meaning. Q13 changes data and is run by hand in pgAdmin, part by part. The pasteable SQL of every query is in `docs/queries.md`.

### 6. Verify the constraints and create the indexes (available)

Both files are run in pgAdmin, one step at a time, after the load.

- `sql/verify_constraints.sql`: lists every constraint, then six inserts that must fail, one per kind of rule.
- `sql/indexes.sql`: `EXPLAIN ANALYZE` of a search on `vote` before and after creating the indexes. Run it again after every new load, because `sql/schema.sql` drops the indexes with the tables.

### 7. Open the app (available)

```
streamlit run app/streamlit_app.py
```

Opens the Eurovision explorer in the browser: five tabs, eight charts and five tables, each one the result of a query in `sql/queries/`. Every filter is sent to PostgreSQL as a bound parameter. Each chart and table has a "Data and SQL" panel with the rows it was drawn from and the query behind it. The app shows a message instead of crashing when the database is not running or a filter returns no rows.

### 8. Planned steps

These commands do not exist yet.

```
```

## Database

Ten tables. The constraints and their justification are in `docs/relational-model.md` and in the report.

| Table | Rows after cleaning | Content |
|---|---|---|
| `country` | 53 | Country code and name |
| `contest` | 68 | One row per contest year |
| `round` | 103 | Final and semi-finals of each contest |
| `song_entry` | 1,719 | One song of one country in one contest |
| `performance` | 2,038 | Running order, place and points of an entry in a round |
| `vote` | 51,354 | Points from one country to another in a round |
| `person` | 2,916 | Composers and lyricists |
| `entry_credit` | 3,990 | Which person is credited on which entry, and in which role |
| `bookmaker` | 33 | Betting offices |
| `betting_odds` | 7,895 | Odds of a bookmaker for an entry in a round |

## Known limits of the data

- 1956: no votes and no published ranking. Places are stored as NULL.
- 2020: the contest was cancelled. Entries exist, votes and results do not.
- 2023: the source has no semi-final votes and no results for semi-final 2.
- Televote and jury points are available separately only from 2016.

## Repository layout

```
README.md
requirements.txt
data/raw/               raw CSV files, not committed
data/clean/             cleaned CSV files for inspection, not committed
scripts/                download and create-database scripts (planned)
sql/schema.sql          tables and constraints
sql/staging.sql         all-text tables for the raw files
sql/profiling.sql       data profile queries P01 to P40
sql/verify_constraints.sql  constraints listed and tested after the load
sql/indexes.sql         indexes and EXPLAIN ANALYZE before and after
sql/queries/            one file per query, Q01 to Q14
src/etl/clean.py        cleaning rules and split into tables
src/etl/load.py         load into PostgreSQL in one transaction
src/db.py               run_query(): database access for queries and app
app/streamlit_app.py    Streamlit application (data and charts)
app/style.py            look of the app: colours, fonts, header, cards
.streamlit/config.toml  dark theme of the app
docs/                   plan, data profile, cleaning log, diagrams, relational model, queries, AI adoption table
project-memory/         task board, decisions and changelog of the project
```

## Project rules

- All analysis is done in SQL in PostgreSQL. pandas, Polars and NumPy are not used.
- Python reads and cleans the raw files during the load, and passes query results to the charts. It does not aggregate or reshape them.
- SQL is written by hand and sent with psycopg2 or SQLAlchemy `text()` with bound parameters. No ORM.
- Missing values stay NULL.
- Raw data and credentials are never committed.

## Author

Kinga Kerekes (individual project): data profiling, cleaning, schema, ETL, all fourteen queries, the app, the report and the presentation.

## Use of AI tools

AI assistance was used in this project. The tasks, what the AI produced and how it was checked are listed in the report (section 7).
