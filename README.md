# Eurovision relational database

Project B of the Information Technology course. The Eurovision Song Contest dataset is turned into a normalised PostgreSQL database, loaded from Python in one transaction, queried in SQL and presented in a Streamlit application.

Author: Kinga Kerekes (individual project). Submitted on 25 November 2026.

## Deliverables

| Part | Where |
|---|---|
| Report, with the AI adoption report in section 7 | `docs/eurovision-report.docx` (and its PDF export) |
| Presentation | `docs/eurovision-presentation.pptx`, 12 slides |
| ER diagram | `docs/er-conceptual.png` (entities and relationships), `docs/er-diagram.png` (tables and keys) |
| Data profile | `sql/profiling.sql` (P01 to P40), results in `docs/data-profile.md` |
| Cleaning | `src/etl/clean.py`, rows affected by each rule in `docs/cleaning-log.md` |
| Schema | `sql/schema.sql`: ten tables with their constraints |
| Load | `src/etl/load.py`: one transaction, `--fail` shows the rollback |
| Constraints and indexes | `sql/verify_constraints.sql`, `sql/indexes.sql` |
| SQL queries | 14 files in `sql/queries/` |
| Application | `app/streamlit_app.py`: five tabs, eight charts and five tables |

## Dataset

[The Eurovision Dataset](https://github.com/Spijkervet/eurovision-dataset) by Janne Spijkervet, release `2023`, DOI 10.5281/zenodo.4036457. The data comes from the EurovisionWorld fan site.

| File | Rows | Content |
|---|---|---|
| `contestants.csv` | 1,734 | One row per song entry, 1956 to 2023 |
| `votes.csv` | 51,354 | Points given by one country to another in one round |
| `betting_offices.csv` | 9,453 | Bookmaker odds per entry and round, 2015 to 2023 |

The raw files are not part of this repository. `python scripts/download_data.py` downloads them into `data/raw/`.

Licence of the dataset: Creative Commons Attribution 4.0 International (CC BY 4.0), as stated on its Zenodo record. The licence requires attribution, given here and in the report.

## Requirements

- PostgreSQL 16 or later (developed on PostgreSQL 18) and pgAdmin 4
- Python 3.10 or later
- Python packages in `requirements.txt`: `psycopg2-binary`, `sqlalchemy`, `matplotlib`, `streamlit` (Altair, used for the Q07 chart, is installed with Streamlit)

The cleaning step uses only the Python standard library.

## Setup

```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (macOS, Linux)
pip install -r requirements.txt
```

Create a file `password.txt` in the repository root that contains only the password of the PostgreSQL user. It is listed in `.gitignore` and must never be committed.

## Usage

Run the steps in this order. PostgreSQL must be running; pgAdmin is only needed for the steps run by hand.

### 1. Download the raw files

```
python scripts/download_data.py
```

Fetches the three CSV files of release `2023` into `data/raw/`.

### 2. Profile the raw data (optional)

```
python scripts/load_staging.py
```

Copies the three raw files unchanged into all-text tables of the schema `staging` (created by `sql/staging.sql`). Then run the queries of `sql/profiling.sql` in pgAdmin, one at a time. The results are written up in `docs/data-profile.md`.

### 3. Clean the raw files (optional, for inspection)

```
python src/etl/clean.py --out data/clean --log docs/cleaning-log.md
```

Writes one cleaned CSV per table into `data/clean/` and regenerates the cleaning log. No database is needed. The load in step 5 runs the same cleaning by itself.

### 4. Create the tables

In pgAdmin, create a database named `eurovision`, open its Query Tool, open `sql/schema.sql` and run it. The script drops and recreates the ten tables, so it can be run again at any time.

### 5. Load the data

```
python src/etl/load.py
```

Cleans the raw files and inserts every table in one transaction, then prints the rows prepared and the rows in the database for each table. The tables must be empty: run `sql/schema.sql` before every load. Connection options: `--host`, `--port`, `--dbname`, `--user`, `--password-file`.

```
python src/etl/load.py --fail
```

Adds one vote for a country that does not exist. The foreign key rejects it, the transaction is rolled back and every table stays empty.

### 6. Verify the constraints and create the indexes

Both files are run in pgAdmin, one step at a time, after the load.

- `sql/verify_constraints.sql`: lists every constraint, then six inserts that must fail, one per kind of rule.
- `sql/indexes.sql`: `EXPLAIN ANALYZE` of a search on `vote` before and after creating the indexes. Run it again after every new load, because `sql/schema.sql` drops the indexes with the tables.

### 7. Run the queries

```
python scripts/run_queries.py
```

Runs Q01 to Q12 and Q14 with their example parameters and writes `docs/queries.md` with the SQL, a sample of each result and its meaning. Q13 changes data and is run by hand in pgAdmin, part by part.

### 8. Open the app

```
streamlit run app/streamlit_app.py
```

Opens the Eurovision Explorer in the browser: five tabs, eight charts and five tables, each one the result of a query in `sql/queries/`. Every filter is sent to PostgreSQL as a bound parameter. Each chart and table has a "Data and SQL" panel with the rows and the query behind it. The app shows a message instead of crashing when the database is not running or a filter returns no rows.

## Database

Ten tables. The constraints and their justification are in section 3 of the report.

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
.gitignore
.streamlit/config.toml      dark theme of the app
data/raw/                   raw CSV files, downloaded, not committed
data/clean/                 cleaned CSV files from step 3, not committed
scripts/download_data.py    downloads the raw files
scripts/load_staging.py     copies the raw files into the staging schema
scripts/run_queries.py      runs the queries and writes docs/queries.md
sql/staging.sql             all-text tables for the raw files
sql/profiling.sql           data profile queries P01 to P40
sql/schema.sql              tables and constraints
sql/verify_constraints.sql  constraints listed and tested after the load
sql/indexes.sql             indexes and EXPLAIN ANALYZE before and after
sql/queries/                one file per query, Q01 to Q14
sql/app/                    queries the app needs for its menus and headline numbers
src/etl/clean.py            cleaning rules and split into tables
src/etl/load.py             load into PostgreSQL in one transaction
src/db.py                   run_query(): database access for the queries and the app
app/streamlit_app.py        Streamlit application (data and charts)
app/style.py                look of the app: colours, fonts, header, cards
docs/                       report, presentation, ER diagrams, data profile, cleaning log
```

## Project rules

- All analysis is done in SQL in PostgreSQL. pandas, Polars and NumPy are not used.
- Python reads and cleans the raw files during the load, and passes query results to the charts. It does not aggregate or reshape them.
- SQL is written by hand and sent with psycopg2 or SQLAlchemy `text()` with bound parameters. No ORM.
- Missing values stay NULL.
- Raw data and credentials are never committed.

## Use of AI tools

AI assistance (Claude, Anthropic) was used in this project. The tasks, what the AI produced and how it was checked are listed in section 7 of the report.
