<div class="titleblock">
<div class="t1">Eurovision Explorer</div>
<div class="t2">Project B report · Information Technology · Kinga Kerekes · 25 November 2026</div>
</div>

# 1. Introduction

**Domain.** The Eurovision Song Contest is a yearly song competition between mostly European countries, held since 1956. Since 2004 most countries must pass a semi-final; the final is decided by the points the countries give each other, from juries, from the public, or since 2016 from both counted separately. Bookmakers publish odds before each show.

I turned a public dataset of the contest into a normalised PostgreSQL database, loaded it from Python in one transaction, answered questions about it in SQL and presented the answers in a Streamlit application. All analysis is done in SQL; Python only cleans the raw files during the load and passes query results to the charts.

**Questions the database answers.**

| # | Question | # | Question |
|---|---|---|---|
| Q01 | Which countries won most often, and when last? | Q08 | Which countries never appeared in a final? |
| Q02 | Best average place in the final, among countries with many finals? | Q09 | How did top finishes accumulate over time? |
| Q03 | Which countries took part but never won? | Q10 | Is the running order related to the result? |
| Q04 | Which countries give a chosen country the most points? | Q11 | Where did the bookmakers' favourites finish? |
| Q05 | How did a country's final place change over time? | Q12 | Which composers wrote the most entries? |
| Q06 | Which pairs give each other high points both ways? | Q13 | How is a contest added so that all rows are saved or none? |
| Q07 | Where did the public and the juries disagree most? | Q14 | In which decades do lyrics most often contain a given word? |

**Data sources and licences.**

| Source | Used for | Licence |
|---|---|---|
| Spijkervet, J. *The Eurovision Dataset*, release `2023`, github.com/Spijkervet/eurovision-dataset, DOI 10.5281/zenodo.4036457 | `contestants.csv`, `votes.csv`, `betting_offices.csv` | CC BY 4.0 (Zenodo record) |
| eurovisionworld.com, 2024 results | Four example values in Q13, inserted and deleted again | Cited as source |

The dataset is real and open, relational (the three files share year and country), supports ten tables, and its largest table, `vote`, has 51,354 rows. The raw files are downloaded by `scripts/download_data.py` and are not committed.

# 2. Data profile

The raw files were loaded unchanged into all-text tables in a `staging` schema and profiled only with SQL: 40 queries in `sql/profiling.sql`, referred to as P01 to P40.

## 2.1 Files and candidate keys

| File | Rows (P01) | Candidate key | Unique? |
|---|---|---|---|
| `contestants.csv` | 1,734 | year, to_country_id | No: 20 repeated pairs (P06) |
| `votes.csv` | 51,354 | year, round, from_country_id, to_country_id | Yes (P05) |
| `betting_offices.csv` | 9,453 | betting_bm_id, year, page_url, contest_round | Yes (P08) |

Of the 20 repeated pairs, 5 are in 1956, when each country sent two songs, and 15 are 2023 entries written on two rows, one for the semi-final and one for the final (P07).

## 2.2 Nulls, ranges and formats

- **contestants** (P02): `song` is empty in 3 rows, `place_contest` in 56, `composers` in 54, `lyricists` in 749, `lyrics` and `youtube_url` in 12. Final columns are empty for entries that did not reach the final (about 340 rows), semi-final columns for entries without a semi-final (1,129 rows), televote and jury columns before 2016 (over 1,500 rows).
- **votes** (P03): `tele_points` and `jury_points` are empty in about 77% of the rows; they exist only from 2016 (P25). All other columns are complete.
- **betting_offices** (P04): `betting_score` is empty in 46 rows, the country in 324.
- **Ranges** (P19 to P22): contestants 1956 to 2023, votes 1957 to 2023, odds 2015 to 2023; final places 1 to 27; final points 0 to 758; one vote 0 to 24 points; odds 1.0 to 1001.0; longest performer 46, song 47, country name 26 characters.
- **Formats** (P12 to P15): integers written as decimals (`27.0`); four round labels (`final`, `semi-final`, `semi-final-1`, `semi-final-2`); `sf_num` 0, 1 or 2.

## 2.3 Findings and cleaning rules

The cleaning step `src/etl/clean.py` applies these rules while reading the files and counts the rows each one affects (`docs/cleaning-log.md`). Missing values stay NULL; no value is invented.

| Finding (query) | Rule | Affected |
|---|---|---|
| Country "code" is a full country name (P09, P10) | R4: name replaced by its code, so the column can be a foreign key | 259 rows |
| One code written with two names, e.g. Czech Republic and Czechia (P11) | R5: one name per code | 11 rows |
| `ad` and `wld` used in votes but never as a code in contestants (P30) | R6: both countries added | 2 countries |
| Votes of a country for itself, all with 0 points (P23) | R7: kept as delivered; a CHECK allows them only with 0 points and the vote queries exclude them in SQL, so nothing is filtered in Python | 1,975 rows kept |
| `from_country`, `to_country` repeat the code columns (P24) | R8: not loaded | 51,354 rows |
| 2023 entries split over two rows (P06, P07) | R9: merged into one entry with one result per round | 15 rows |
| Several composers or lyricists in one cell (P16) | R10: split into one credit per person | 815 lists |
| Lyrics contain the characters `\n` (P17) | R11: replaced by line breaks | 1,722 rows |
| `sf_num` 0, 1, 2 (P15) | R12: mapped to the round labels of votes | 640 rows |
| Integers written as `27.0` (P12, P13) | R2: converted to integers | 5,687 cells |
| Betting rows do not match by performer and song (P36) | R13: matched through the year and the country in `page_url` | 7,895 rows |
| 2020 odds identical under three round labels (P37, P38) | R14: loaded once | 1,558 rows not loaded |
| Every 1956 entry has place 2, the winner included (P31) | R15: 1956 places set to NULL | 12 entries |
| Empty cells | R1: stored as NULL | 91,837 cells |

The load reconciles with the input: 1,734 contestant rows less 15 merged rows give 1,719 entries; all 51,354 votes are loaded; 9,453 betting rows less 1,558 repeats give 7,895 odds. Two consistency checks passed: where televote and jury points exist, the total is their sum (P26), and the final points of each entry equal the votes it received (P33).

# 3. Design

## 3.1 ER diagram

![Entity-relationship diagram](er-conceptual.png){.wide}

## 3.2 Relational model

Primary keys in **bold**, foreign keys in *italics* with the table they refer to.

- COUNTRY (**country_code**, name)
- CONTEST (**year**)
- ROUND (**round_id**, *year* → CONTEST, round_type)
- SONG_ENTRY (**entry_id**, *year* → CONTEST, *country_code* → COUNTRY, performer, song, place_contest, youtube_url, lyrics)
- PERFORMANCE (***entry_id*** → SONG_ENTRY, ***round_id*** → ROUND, running_order, place, points, points_tele, points_jury)
- VOTE (***round_id*** → ROUND, ***from_country*** → COUNTRY, ***to_country*** → COUNTRY, total_points, tele_points, jury_points)
- PERSON (**person_id**, name)
- ENTRY_CREDIT (***entry_id*** → SONG_ENTRY, ***person_id*** → PERSON, **role**)
- BOOKMAKER (**bookmaker_id**, name)
- BETTING_ODDS (***bookmaker_id*** → BOOKMAKER, ***entry_id*** → SONG_ENTRY, ***round_id*** → ROUND, odds)

Each entity became a table. The 1:N relationships became foreign keys on the N side; the N:N (many-to-many) relationships (performs in, is credited on) and the three-way relationships (votes for, quotes odds for) became tables whose primary key combines the keys they link. All tables are in third normal form; the source files were not (repeated country names, final and semi-final as two groups of columns, lists in one cell).

## 3.3 Justified exceptions

1. **Surrogate keys** `entry_id`, `round_id`, `person_id`: (year, country) is not unique because of 1956, and `song` is empty in three rows. The natural combination is protected by a UNIQUE constraint.
2. **`vote` refers to countries, not entries**: votes are cast by a country for a country; the entry is found through the year and the receiving country. This would be ambiguous only in 1956, which has no votes.
3. **`total_points` is stored** although from 2016 it equals televote plus jury (P26): before 2016 the parts do not exist.
4. **`place_contest` and `performance.points` are stored**: the overall place of semi-final entries cannot be derived, and points exist where votes are missing (1956, 2020, 2023 semi-finals).
5. **Self-vote rows are kept**: removing them would be a filter outside SQL; a CHECK states they can only hold 0 points.
6. **`contest` has one column**, so that rounds and entries of a year refer to one row and a year can exist before its rounds (Q13).

# 4. Implementation

## 4.1 Order of execution

`scripts/download_data.py` → create the database in pgAdmin → `sql/schema.sql` → `python src/etl/load.py` → `sql/verify_constraints.sql` and `sql/indexes.sql` → `scripts/run_queries.py` → `streamlit run app/streamlit_app.py`. Tools: PostgreSQL 18, pgAdmin 4, Python with psycopg2, SQLAlchemy Core, matplotlib, Altair and Streamlit.

## 4.2 Schema

The schema is created first; the load only inserts rows. Types follow the profile: years, places and points `SMALLINT` (maximum 758), country codes `VARCHAR(3)` (because of `wld`), text sizes above the longest value found, odds `NUMERIC(7,2)`, lyrics `TEXT`.

```sql
{{schema}}
```

## 4.3 Load in one transaction

`src/etl/load.py` takes the ten cleaned tables from `clean.py`, checks that the tables are empty, and inserts all of them with `execute_values` inside one `with conn:` block. It then compares the rows prepared with `COUNT(*)` in each table: all ten matched (country 53, contest 68, round 103, song_entry 1,719, performance 2,038, vote 51,354, person 2,916, entry_credit 3,990, bookmaker 33, betting_odds 7,895).

**Rollback.** `python src/etl/load.py --fail` adds one vote for the non-existent country `zz`. Five tables were inserted before the error; afterwards every table had 0 rows:

```text
ROLLBACK: nothing was loaded.
Error: insert or update on table "vote" violates foreign key constraint "vote_to_country_fkey"
Detail: Key (to_country)=(zz) is not present in table "country".
```

## 4.4 Constraints verified after loading

| Check in `sql/verify_constraints.sql` | Result |
|---|---|
| PRIMARY KEY, FOREIGN KEY, UNIQUE per table | 21 rows: 10 primary keys, 13 foreign keys, 5 unique |
| CHECK constraints with their rule | 14 rows |
| NOT NULL columns | 26 rows |
| Duplicate country `se`; vote for `zz`; second "Sweden" | Rejected by `country_pkey`; `vote_to_country_fkey`; `country_name_key` |
| Entry without performer; vote of -3 points; round type `heat` | Rejected by NOT NULL; `vote_total_points_check`; `round_round_type_check` |

## 4.5 Indexes

| Query on `vote` | Plan | Time |
|---|---|---|
| `WHERE to_country = 'ad'`, no index | Seq Scan, 51,161 rows read and discarded | 6.02 ms |
| Same, after `CREATE INDEX idx_vote_to_country` | Bitmap Index Scan, 193 rows | 0.24 ms |
| `WHERE total_points = 0` (half the table) | Seq Scan, index not used | 7.20 ms |

The index made the selective search about 25 times faster; for a condition half the rows meet, the planner correctly keeps the full scan.

# 5. Queries

All queries were written by me (Kinga Kerekes). Each is a file in `sql/queries/` with named parameters that the application binds to its filters; here the example values are written in. Required constructs: joins (Q01 and most others), GROUP BY with HAVING (Q02, Q03, Q04, Q06, Q10, Q12), subquery (Q03, Q13), window functions (Q04, Q05, Q07, Q09, Q11), CTE (Q04 to Q09, Q11), INSERT, UPDATE and DELETE in a transaction (Q13). Vote averages default to 1975 to 2015, when every country gave 1 to 12 points.

{{include docs/queries.md rows=3}}

# 6. Visualization

The application (`app/streamlit_app.py`, look in `app/style.py`) has five tabs with eight charts and five tables. It connects through `src/db.py`, whose `run_query(sql, params)` sends a query file with SQLAlchemy `text()` and bound parameters and returns the rows.

- **Charts use only SQL results:** each chart draws the returned rows in their order; a chart with several countries (Q09) runs its query once per country. A *Data and SQL* panel under each chart and table shows the rows and the query. Charts are drawn with matplotlib, except Q07, which uses Altair (installed with Streamlit) so that pointing at a dot shows its country, year and both ranks.
- **Filters are parameters:** sliders, menus and number boxes send their values as bound parameters; menus and limits come from queries in `sql/app/`.
- **No crashes:** inputs have fixed limits; every query runs inside `fetch()`, which shows a message on error; empty results are explained.
- **No SQL injection:** the only free text, the lyrics search, is sent as a LIKE parameter with `%` and `_` escaped.

<div class="grid" markdown="1">

![Header with the headline numbers](screenshots/00_header.png)

![Q01 wins per country; filter: years](screenshots/card_q01.png)

![Q05 place over time; filter: country](screenshots/card_q05.png)

![Q10 running order; filters: years, minimum finals](screenshots/card_q10.png)

![Q09 top finishes; filters: countries, top places](screenshots/card_q09.png)

![Q04 top givers; filters: country, years, number, minimum contests](screenshots/card_q04.png)

![Q06 mutual pairs (table); filters: years, minimum average, minimum contests](screenshots/card_q06.png)

![Q07 public against juries; filters: years, minimum gap](screenshots/card_q07.png)

![Q11 the favourite's place; filter: years](screenshots/card_q11.png)

![Q14 word in lyrics; filter: free text](screenshots/card_q14.png)

![Q12 composers (table); filter: minimum entries](screenshots/card_q12.png)

![Q02 best average place (table); filter: minimum finals](screenshots/card_q02.png)

![Q03 never won (table); filter: minimum entries](screenshots/card_q03.png)

![Q08 never in a final (table)](screenshots/card_q08.png)

![Function: Q01 after changing the years to 1997 to 2023](screenshots/f1_filter_q01_1997.png)

![Function: the Data and SQL panel of Q10](screenshots/f2_data_and_sql_q10.png)

![Function: Andorra in Q05, an explained empty result](screenshots/f3_empty_andorra.png)

![Function: the injection attempt ' OR '1'='1 is searched as text and found nowhere](screenshots/f4_injection_q14.png)

</div>

# 7. AI adoption report

I used Claude (Anthropic) throughout the project.

| Task | Tool | What the AI produced | How I checked it |
|---|---|---|---|
| Project plan | Claude | A plan mapping each requirement to the course sessions, a first schema and a schedule | Compared with the project description and the course slides; changed it where my decisions differed |
| Data cleaning (`clean.py`) | Claude | The cleaning module with its 16 rules and the cleaning log | Ran it on my machine; row counts reconcile with the input files; each rule is backed by a profiling query I ran in pgAdmin |
| Data profile (`profiling.sql`) | Claude | The staging tables, 40 profiling queries and the written profile | Ran the staging load and seven queries in pgAdmin (P01, P05, P06, P09, P23, P31, P33); every result matched |
| Modelling | Claude | ER diagram, table diagram, relational model and exceptions | Reviewed them against the data and asked for changes (`entry` renamed `song_entry`); decided the 1956 and self-vote rules |
| Schema and load | Claude | `schema.sql` and the one-transaction `load.py` with the rollback demonstration | Ran both: counts match in all ten tables; the `--fail` run left every table empty |
| Constraints and indexes | Claude | `verify_constraints.sql` and `indexes.sql` | Ran each step in pgAdmin: 21, 14 and 26 rows, six inserts rejected, the plan changed to an index scan |
| Queries Q01 to Q14 | Claude | First versions of the SQL and the meaning sentences | Ran all queries with the expected row counts; compared results with known facts; the 2024 values in Q13 were checked against eurovisionworld.com; ran Q13 step by step |
| Streamlit application | Claude | The application, its error handling and its styling after a template I chose | Used it with normal and invalid input; found a misleading message for Andorra, which was then fixed; tried the injection string |
| Report and presentation | Claude | Drafts of this report and of the slides | Read in full and corrected before submission |
