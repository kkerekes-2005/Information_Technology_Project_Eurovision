"""Clean the raw Eurovision CSV files and split them into the ten target tables.

Standard library only. This module cleans formats and maps keys. It does not
analyse the data: every figure of the project is computed later in SQL.

Use from the loader:
    from src.etl.clean import build_tables
    tables, rules, review = build_tables(contestants_path, votes_path, betting_path)

Use from the terminal, to inspect the cleaned tables as CSV files:
    python src/etl/clean.py --out data/clean --log docs/cleaning-log.md
"""
import argparse
import csv
import os
from collections import Counter
from decimal import Decimal

csv.field_size_limit(10**9)  # the lyrics column is long

# ---------------------------------------------------------------------------
# Fixed decisions. Each one is a documented cleaning rule (docs/cleaning-log.md)
# ---------------------------------------------------------------------------

# R5: one name per country. The left side is a scraping artefact or an old name.
COUNTRY_NAME_FIXES = {
    "North MacedoniaN.Macedonia": "North Macedonia",
    "Czech Republic": "Czechia",
}

# R6: codes used in votes.csv that never appear as a code in contestants.csv.
# "ad" is the ISO 3166 code of Andorra. "wld" is the televote of the
# non-participating countries, introduced in 2023.
MANUAL_COUNTRIES = {"ad": "Andorra", "wld": "Rest of the World"}

# R12: sf_num in contestants.csv to the round labels used in votes.csv.
SF_ROUND = {0: "semi-final", 1: "semi-final-1", 2: "semi-final-2"}
ROUND_ORDER = ["semi-final", "semi-final-1", "semi-final-2", "final"]

# R15: year whose places are a placeholder in the source.
PLACEHOLDER_PLACE_YEAR = 1956

# R14: year of the cancelled contest, whose odds are repeated under each round.
CANCELLED_YEAR = 2020

RULES = {
    "R1": "Empty cell stored as NULL (cells)",
    "R2": "Integer written as decimal text, such as 27.0, converted to integer (cells)",
    "R3": "Leading or trailing spaces removed from text (cells)",
    "R4": "Country name found in contestants.to_country_id replaced by the country code (rows)",
    "R5": "Country name variant replaced by the single name of the country (rows)",
    "R6": "Country added by hand because votes.csv uses a code that contestants.csv never has (countries)",
    "R7": "Vote of a country for itself kept as delivered, always 0 points; nothing is changed. "
          "Queries exclude these rows in SQL (rows kept)",
    "R8": "Redundant columns votes.from_country and votes.to_country not loaded, they repeat the codes (rows)",
    "R9": "Entry written on two source rows, final and semi-final, merged into one entry (source rows merged away)",
    "R10": "Composer or lyricist list split on ';' into one credit per person (entries with a list of several names)",
    "R11": "Two-character sequence \\n in lyrics replaced by a real line break (rows)",
    "R12": "sf_num 0, 1, 2 mapped to the round labels semi-final, semi-final-1, semi-final-2 (rows)",
    "R13": "Betting row linked to its entry through year and the country in page_url; "
           "country_name, country_code, performer, song and betting_sc_id not loaded (rows)",
    "R14": "Odds of the cancelled 2020 contest are identical under final, semi-final-1 and "
           "semi-final-2; only the copy labelled final is loaded (rows removed)",
    "R15": "1956 place set to NULL: the source writes place 2 for every entry, including the "
           "winner, because the 1956 ranking was never published (entries)",
    "R16": "Betting row that matches no entry not loaded, written to betting_unmatched.csv (rows)",
}


class CleaningError(Exception):
    """A value that the cleaning rules do not cover. The load must stop."""


# ---------------------------------------------------------------------------
# Cell cleaning
# ---------------------------------------------------------------------------

def to_text(value, rules):
    """Text without outer spaces. An empty cell becomes None."""
    stripped = value.strip()
    if stripped != value:
        rules["R3"] += 1
    if stripped == "":
        rules["R1"] += 1
        return None
    return stripped


def to_int(value, rules):
    """Integer, also from text such as '27.0'. An empty cell becomes None."""
    text = value.strip()
    if text == "":
        rules["R1"] += 1
        return None
    number = float(text)
    if number != int(number):
        raise CleaningError(f"not a whole number: {value!r}")
    if "." in text:
        rules["R2"] += 1
    return int(number)


def to_decimal(value, rules):
    """Decimal for a NUMERIC column. An empty cell becomes None."""
    text = value.strip()
    if text == "":
        rules["R1"] += 1
        return None
    return Decimal(text)


def slug(country_name):
    """Country name as written in page_url: 'Bosnia & Herzegovina' -> 'bosnia-herzegovina'."""
    return country_name.lower().replace(" & ", "-").replace(" ", "-")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------

def build_countries(contestant_rows, rules):
    """Return code -> name and name -> code from the rows that carry a real code."""
    code_to_name = {}
    for row in contestant_rows:
        code = row["to_country_id"].strip()
        if len(code) > 3:
            continue  # a country name in the code column, resolved later (R4)
        name = COUNTRY_NAME_FIXES.get(row["to_country"].strip(), row["to_country"].strip())
        if code_to_name.setdefault(code, name) != name:
            raise CleaningError(f"country code {code} has two names")
    for code, name in MANUAL_COUNTRIES.items():
        if code not in code_to_name:
            code_to_name[code] = name
            rules["R6"] += 1
    name_to_code = {name: code for code, name in code_to_name.items()}
    if len(name_to_code) != len(code_to_name):
        raise CleaningError("two country codes share one name")
    return code_to_name, name_to_code


def country_code_of(row, name_to_code, code_to_name, rules):
    raw_code = row["to_country_id"].strip()
    raw_name = row["to_country"].strip()
    if raw_name in COUNTRY_NAME_FIXES:
        rules["R5"] += 1
    if len(raw_code) <= 3:
        if raw_code not in code_to_name:
            raise CleaningError(f"unknown country code {raw_code!r}")
        return raw_code
    name = COUNTRY_NAME_FIXES.get(raw_code, raw_code)
    if name not in name_to_code:
        raise CleaningError(f"country name without a code: {raw_code!r}")
    rules["R4"] += 1
    return name_to_code[name]


# ---------------------------------------------------------------------------
# contestants.csv -> song_entry, performance, person, entry_credit
# ---------------------------------------------------------------------------

def clean_contestants(rows, code_to_name, name_to_code, rules):
    entries = {}        # (year, code, performer, song) -> entry dictionary
    performances = {}   # (entry_id, year, round_type) -> tuple of results
    people = {}         # name -> person_id
    credits = set()     # (entry_id, person_id, role)

    for row in rows:
        year = to_int(row["year"], rules)
        code = country_code_of(row, name_to_code, code_to_name, rules)
        performer = to_text(row["performer"], rules)
        song = to_text(row["song"], rules)
        place_contest = to_int(row["place_contest"], rules)
        youtube_url = to_text(row["youtube_url"], rules)
        lyrics = to_text(row["lyrics"], rules)
        if lyrics is not None and "\\n" in lyrics:
            lyrics = lyrics.replace("\\n", "\n")
            rules["R11"] += 1
        if year == PLACEHOLDER_PLACE_YEAR and place_contest is not None:
            place_contest = None
            rules["R15"] += 1

        key = (year, code, performer, song)
        if key in entries:
            # R9: second source row of the same entry. Keep every value, lose none.
            entry = entries[key]
            rules["R9"] += 1
            for field, value in (("place_contest", place_contest),
                                 ("youtube_url", youtube_url), ("lyrics", lyrics)):
                if entry[field] is None:
                    entry[field] = value
                elif value is not None and value != entry[field]:
                    raise CleaningError(f"two rows of entry {key} disagree on {field}")
        else:
            entry = {"entry_id": len(entries) + 1, "year": year, "country_code": code,
                     "performer": performer, "song": song, "place_contest": place_contest,
                     "youtube_url": youtube_url, "lyrics": lyrics}
            entries[key] = entry
        entry_id = entry["entry_id"]

        # Final: one performance row when any final column has a value.
        final = (to_int(row["running_final"], rules), to_int(row["place_final"], rules),
                 to_int(row["points_final"], rules), to_int(row["points_tele_final"], rules),
                 to_int(row["points_jury_final"], rules))
        if year == PLACEHOLDER_PLACE_YEAR:
            final = (final[0], None) + final[2:]
        if any(v is not None for v in final):
            add_performance(performances, (entry_id, year, "final"), final)

        # Semi-final: one performance row when the entry was allocated to one.
        sf_num = to_int(row["sf_num"], rules)
        semi = (to_int(row["running_sf"], rules), to_int(row["place_sf"], rules),
                to_int(row["points_sf"], rules), to_int(row["points_tele_sf"], rules),
                to_int(row["points_jury_sf"], rules))
        if sf_num is not None:
            rules["R12"] += 1
            add_performance(performances, (entry_id, year, SF_ROUND[sf_num]), semi)
        elif any(v is not None for v in semi):
            raise CleaningError(f"semi-final results without sf_num: {key}")

        # R10: one credit per person and role.
        for role, column in (("composer", "composers"), ("lyricist", "lyricists")):
            names = [to_text(n, rules) for n in row[column].split(";")] if row[column].strip() else []
            names = [n for n in names if n is not None]
            if not names:
                rules["R1"] += 1
            if len(names) > 1:
                rules["R10"] += 1
            for name in names:
                person_id = people.setdefault(name, len(people) + 1)
                credits.add((entry_id, person_id, role))

    return entries, performances, people, credits


def add_performance(performances, key, values):
    if key in performances and performances[key] != values:
        raise CleaningError(f"two different results for performance {key}")
    performances[key] = values


# ---------------------------------------------------------------------------
# votes.csv -> vote
# ---------------------------------------------------------------------------

def clean_votes(rows, code_to_name, rules):
    votes = []
    for row in rows:
        giver = to_text(row["from_country_id"], rules)
        receiver = to_text(row["to_country_id"], rules)
        if row["from_country"].strip() != giver or row["to_country"].strip() != receiver:
            raise CleaningError("from_country / to_country differ from the code columns")
        rules["R8"] += 1
        for code in (giver, receiver):
            if code not in code_to_name:
                raise CleaningError(f"vote with unknown country code {code!r}")
        total = to_int(row["total_points"], rules)
        if giver == receiver:
            # A country never gives itself points. The source still has one row per
            # country and round with 0 points. It is loaded as it is (rule R7).
            if total != 0:
                raise CleaningError(f"self vote with points: {row}")
            rules["R7"] += 1
        votes.append((to_int(row["year"], rules), to_text(row["round"], rules), giver, receiver,
                      total, to_int(row["tele_points"], rules), to_int(row["jury_points"], rules)))
    return votes


# ---------------------------------------------------------------------------
# betting_offices.csv -> bookmaker, betting_odds
# ---------------------------------------------------------------------------

def clean_betting(rows, entries, code_to_name, rules):
    slug_to_code = {slug(name): code for code, name in code_to_name.items()}
    entry_of = {}  # (year, country_code) -> list of entry_id
    for entry in entries.values():
        entry_of.setdefault((entry["year"], entry["country_code"]), []).append(entry["entry_id"])

    bookmakers = {}
    odds = []
    unmatched = []
    for row in rows:
        year = to_int(row["year"], rules)
        round_type = to_text(row["contest_round"], rules)
        if year == CANCELLED_YEAR and round_type != "final":
            rules["R14"] += 1
            continue
        bookmaker_id = to_int(row["betting_bm_id"], rules)
        name = to_text(row["betting_name"], rules)
        if bookmakers.setdefault(bookmaker_id, name) != name:
            raise CleaningError(f"bookmaker {bookmaker_id} has two names")

        # page_url looks like /eurovision/2015/sweden
        parts = row["page_url"].strip().split("/")
        code = slug_to_code.get(parts[-1])
        candidates = entry_of.get((year, code), [])
        if len(parts) != 4 or int(parts[2]) != year or len(candidates) != 1:
            rules["R16"] += 1
            unmatched.append(row)
            continue
        rules["R13"] += 1
        odds.append((bookmaker_id, candidates[0], year, round_type,
                     to_decimal(row["betting_score"], rules)))
    return bookmakers, odds, unmatched


# ---------------------------------------------------------------------------
# Assemble the ten tables
# ---------------------------------------------------------------------------

def build_tables(contestants_path, votes_path, betting_path):
    """Return (tables, rules, review).

    tables: table name -> (column names, list of tuples), in the order of loading.
    rules:  Counter, rule id -> rows or cells affected.
    review: source rows that could not be loaded.
    """
    rules = Counter({rule: 0 for rule in RULES})
    contestant_rows = read_csv(contestants_path)
    vote_rows = read_csv(votes_path)
    betting_rows = read_csv(betting_path)

    code_to_name, name_to_code = build_countries(contestant_rows, rules)
    entries, performances, people, credits = clean_contestants(
        contestant_rows, code_to_name, name_to_code, rules)
    votes = clean_votes(vote_rows, code_to_name, rules)
    bookmakers, odds, unmatched = clean_betting(betting_rows, entries, code_to_name, rules)

    # Rounds: every (year, round) used by a performance, a vote or an odds row.
    round_keys = {(k[1], k[2]) for k in performances}
    round_keys |= {(v[0], v[1]) for v in votes}
    round_keys |= {(o[2], o[3]) for o in odds}
    for year, round_type in round_keys:
        if round_type not in ROUND_ORDER:
            raise CleaningError(f"unknown round label {round_type!r}")
    ordered = sorted(round_keys, key=lambda k: (k[0], ROUND_ORDER.index(k[1])))
    round_id = {key: number for number, key in enumerate(ordered, start=1)}

    tables = {
        "country": (("country_code", "name"), sorted(code_to_name.items())),
        "contest": (("year",), [(y,) for y in sorted({e["year"] for e in entries.values()})]),
        "round": (("round_id", "year", "round_type"),
                  [(round_id[k], k[0], k[1]) for k in ordered]),
        "song_entry": (("entry_id", "year", "country_code", "performer", "song",
                   "place_contest", "youtube_url", "lyrics"),
                  [tuple(e.values()) for e in entries.values()]),
        "performance": (("entry_id", "round_id", "running_order", "place", "points",
                         "points_tele", "points_jury"),
                        sorted((k[0], round_id[(k[1], k[2])]) + v
                               for k, v in performances.items())),
        "vote": (("round_id", "from_country", "to_country", "total_points",
                  "tele_points", "jury_points"),
                 [(round_id[(v[0], v[1])],) + v[2:] for v in votes]),
        "person": (("person_id", "name"), [(i, n) for n, i in people.items()]),
        "entry_credit": (("entry_id", "person_id", "role"), sorted(credits)),
        "bookmaker": (("bookmaker_id", "name"), sorted(bookmakers.items())),
        "betting_odds": (("bookmaker_id", "entry_id", "round_id", "odds"),
                         [(o[0], o[1], round_id[(o[2], o[3])], o[4]) for o in odds]),
    }
    check_keys(tables)
    source_counts = {"contestants.csv": len(contestant_rows), "votes.csv": len(vote_rows),
                     "betting_offices.csv": len(betting_rows)}
    return tables, rules, {"betting_unmatched": unmatched, "source_counts": source_counts}


def check_keys(tables):
    """The same rules the database will enforce, checked before the load starts."""
    primary_keys = {"country": 1, "contest": 1, "round": 1, "song_entry": 1, "performance": 2,
                    "vote": 3, "person": 1, "entry_credit": 3, "bookmaker": 1, "betting_odds": 3}
    for table, width in primary_keys.items():
        keys = [row[:width] for row in tables[table][1]]
        if len(keys) != len(set(keys)):
            raise CleaningError(f"repeated primary key in {table}")
    countries = {r[0] for r in tables["country"][1]}
    rounds = {r[0] for r in tables["round"][1]}
    entry_ids = {r[0] for r in tables["song_entry"][1]}
    for row in tables["song_entry"][1]:
        if row[2] not in countries:
            raise CleaningError(f"entry with unknown country: {row[:3]}")
    for row in tables["vote"][1]:
        if row[0] not in rounds or row[1] not in countries or row[2] not in countries:
            raise CleaningError(f"vote with a broken reference: {row}")
    for row in tables["betting_odds"][1]:
        if row[1] not in entry_ids or row[2] not in rounds:
            raise CleaningError(f"odds with a broken reference: {row}")


# ---------------------------------------------------------------------------
# Command line: write the cleaned tables and the cleaning log
# ---------------------------------------------------------------------------

def write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in rows:
            writer.writerow(["" if value is None else value for value in row])


def write_log(path, tables, rules, review):
    lines = ["# Cleaning log", "",
             "Generated by `src/etl/clean.py`. Do not edit by hand: run the script again.", "",
             "## Source files", "", "| File | Rows |", "|---|---|"]
    lines += [f"| `{name}` | {count} |" for name, count in review["source_counts"].items()]
    lines += ["", "## Cleaning rules and rows affected", "",
              "| Rule | Description (unit) | Affected |", "|---|---|---|"]
    lines += [f"| {rule} | {text} | {rules[rule]} |" for rule, text in RULES.items()]
    lines += ["", "## Tables produced", "", "| Table | Rows |", "|---|---|"]
    lines += [f"| `{name}` | {len(rows)} |" for name, (_, rows) in tables.items()]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Clean the raw Eurovision CSV files.")
    parser.add_argument("--contestants", default="data/raw/contestants.csv")
    parser.add_argument("--votes", default="data/raw/votes.csv")
    parser.add_argument("--betting", default="data/raw/betting_offices.csv")
    parser.add_argument("--out", default="data/clean", help="folder for the cleaned CSV files")
    parser.add_argument("--log", default="docs/cleaning-log.md")
    args = parser.parse_args()

    tables, rules, review = build_tables(args.contestants, args.votes, args.betting)
    os.makedirs(args.out, exist_ok=True)
    for name, (header, rows) in tables.items():
        write_csv(os.path.join(args.out, f"{name}.csv"), header, rows)
        print(f"{name:13} {len(rows):6} rows")
    unmatched = review["betting_unmatched"]
    if unmatched:
        write_csv(os.path.join(args.out, "betting_unmatched.csv"),
                  list(unmatched[0].keys()), [list(r.values()) for r in unmatched])
    write_log(args.log, tables, rules, review)
    for rule in RULES:
        print(rule, rules[rule])


if __name__ == "__main__":
    main()
