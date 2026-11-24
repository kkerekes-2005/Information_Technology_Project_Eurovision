-- Staging tables: the three raw CSV files exactly as they are, every column as TEXT.
-- They exist only to profile the raw data with SQL (sql/profiling.sql).
-- They are not part of the designed model. Filled by scripts/load_staging.py.

CREATE SCHEMA IF NOT EXISTS staging;

DROP TABLE IF EXISTS staging.contestants;
DROP TABLE IF EXISTS staging.votes;
DROP TABLE IF EXISTS staging.betting_offices;

CREATE TABLE staging.contestants (
    year              TEXT,
    to_country_id     TEXT,
    to_country        TEXT,
    performer         TEXT,
    song              TEXT,
    place_contest     TEXT,
    sf_num            TEXT,
    running_final     TEXT,
    running_sf        TEXT,
    place_final       TEXT,
    points_final      TEXT,
    place_sf          TEXT,
    points_sf         TEXT,
    points_tele_final TEXT,
    points_jury_final TEXT,
    points_tele_sf    TEXT,
    points_jury_sf    TEXT,
    composers         TEXT,
    lyricists         TEXT,
    lyrics            TEXT,
    youtube_url       TEXT
);

CREATE TABLE staging.votes (
    year            TEXT,
    round           TEXT,
    from_country_id TEXT,
    to_country_id   TEXT,
    from_country    TEXT,
    to_country      TEXT,
    total_points    TEXT,
    tele_points     TEXT,
    jury_points     TEXT
);

CREATE TABLE staging.betting_offices (
    betting_bm_id TEXT,
    betting_sc_id TEXT,
    betting_name  TEXT,
    betting_score TEXT,
    year          TEXT,
    performer     TEXT,
    song          TEXT,
    page_url      TEXT,
    contest_round TEXT,
    country_name  TEXT,
    country_code  TEXT
);
