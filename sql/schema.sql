-- Eurovision database: physical schema.
-- Run this file in the Query Tool of the database "eurovision" before every load.
-- Children are dropped first and parents are created first, because of the foreign keys.

DROP TABLE IF EXISTS betting_odds;
DROP TABLE IF EXISTS bookmaker;
DROP TABLE IF EXISTS entry_credit;
DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS vote;
DROP TABLE IF EXISTS performance;
DROP TABLE IF EXISTS song_entry;
DROP TABLE IF EXISTS round;
DROP TABLE IF EXISTS contest;
DROP TABLE IF EXISTS country;

-- A participating or voting country. 'wld' (Rest of the World) has three letters.
CREATE TABLE country (
    country_code VARCHAR(3)  PRIMARY KEY,
    name         VARCHAR(50) NOT NULL UNIQUE
);

-- One contest per year.
CREATE TABLE contest (
    year SMALLINT PRIMARY KEY CHECK (year >= 1956)
);

-- The final and the semi-finals of a contest.
CREATE TABLE round (
    round_id   INTEGER     PRIMARY KEY,
    year       SMALLINT    NOT NULL REFERENCES contest (year),
    round_type VARCHAR(12) NOT NULL
               CHECK (round_type IN ('final', 'semi-final', 'semi-final-1', 'semi-final-2')),
    UNIQUE (year, round_type)
);

-- One song of one country in one contest. In 1956 each country sent two songs,
-- so (year, country_code) is not a key.
CREATE TABLE song_entry (
    entry_id      INTEGER      PRIMARY KEY,
    year          SMALLINT     NOT NULL REFERENCES contest (year),
    country_code  VARCHAR(3)   NOT NULL REFERENCES country (country_code),
    performer     VARCHAR(100) NOT NULL,
    song          VARCHAR(100),
    place_contest SMALLINT     CHECK (place_contest > 0),
    youtube_url   VARCHAR(100),
    lyrics        TEXT,
    UNIQUE (year, country_code, performer, song)
);

-- The result of an entry in one round.
CREATE TABLE performance (
    entry_id      INTEGER  NOT NULL REFERENCES song_entry (entry_id),
    round_id      INTEGER  NOT NULL REFERENCES round (round_id),
    running_order SMALLINT CHECK (running_order > 0),
    place         SMALLINT CHECK (place > 0),
    points        SMALLINT CHECK (points >= 0),
    points_tele   SMALLINT CHECK (points_tele >= 0),
    points_jury   SMALLINT CHECK (points_jury >= 0),
    PRIMARY KEY (entry_id, round_id)
);

-- Points given by one country to another in one round.
-- tele_points and jury_points exist only from 2016.
-- The source has one row per country and round for the country itself, always with
-- 0 points. These rows are kept. The last CHECK states the rule behind them:
-- a country cannot give points to itself.
CREATE TABLE vote (
    round_id     INTEGER    NOT NULL REFERENCES round (round_id),
    from_country VARCHAR(3) NOT NULL REFERENCES country (country_code),
    to_country   VARCHAR(3) NOT NULL REFERENCES country (country_code),
    total_points SMALLINT   NOT NULL CHECK (total_points >= 0),
    tele_points  SMALLINT   CHECK (tele_points >= 0),
    jury_points  SMALLINT   CHECK (jury_points >= 0),
    PRIMARY KEY (round_id, from_country, to_country),
    CHECK (from_country <> to_country OR total_points = 0)
);

-- A composer or a lyricist.
CREATE TABLE person (
    person_id INTEGER      PRIMARY KEY,
    name      VARCHAR(100) NOT NULL UNIQUE
);

-- Who is credited on which entry, and in which role (N:N between entry and person).
CREATE TABLE entry_credit (
    entry_id  INTEGER     NOT NULL REFERENCES song_entry (entry_id),
    person_id INTEGER     NOT NULL REFERENCES person (person_id),
    role      VARCHAR(10) NOT NULL CHECK (role IN ('composer', 'lyricist')),
    PRIMARY KEY (entry_id, person_id, role)
);

-- A betting office.
CREATE TABLE bookmaker (
    bookmaker_id INTEGER     PRIMARY KEY,
    name         VARCHAR(50) NOT NULL UNIQUE
);

-- Odds of a bookmaker for an entry in a round. Decimal odds are never below 1.
CREATE TABLE betting_odds (
    bookmaker_id INTEGER      NOT NULL REFERENCES bookmaker (bookmaker_id),
    entry_id     INTEGER      NOT NULL REFERENCES song_entry (entry_id),
    round_id     INTEGER      NOT NULL REFERENCES round (round_id),
    odds         NUMERIC(7,2) CHECK (odds >= 1),
    PRIMARY KEY (bookmaker_id, entry_id, round_id)
);
