# Relational model

Derived from the entity-relationship diagram `docs/er-conceptual.png`. The diagram of the resulting tables is `docs/er-diagram.png`. The SQL that creates them is `sql/schema.sql`.

Notation: **bold** = primary key. *italics* = foreign key, with the table it refers to after the arrow. A column that is both is written in bold italics.

## Tables

COUNTRY (**country_code**, name)

CONTEST (**year**)

ROUND (**round_id**, *year* → CONTEST, round_type)

SONG_ENTRY (**entry_id**, *year* → CONTEST, *country_code* → COUNTRY, performer, song, place_contest, youtube_url, lyrics)

PERFORMANCE (***entry_id*** → SONG_ENTRY, ***round_id*** → ROUND, running_order, place, points, points_tele, points_jury)

VOTE (***round_id*** → ROUND, ***from_country*** → COUNTRY, ***to_country*** → COUNTRY, total_points, tele_points, jury_points)

PERSON (**person_id**, name)

ENTRY_CREDIT (***entry_id*** → SONG_ENTRY, ***person_id*** → PERSON, **role**)

BOOKMAKER (**bookmaker_id**, name)

BETTING_ODDS (***bookmaker_id*** → BOOKMAKER, ***entry_id*** → SONG_ENTRY, ***round_id*** → ROUND, odds)

## From the diagram to the tables

| Element of the ER diagram | Rule applied | Result |
|---|---|---|
| Entities COUNTRY, CONTEST, ROUND, SONG ENTRY, PERSON, BOOKMAKER | One table per entity, the key attribute becomes the primary key | Six tables |
| CONTEST has ROUND (1:N) | The key of the 1 side goes to the N side as a foreign key | `round.year` |
| COUNTRY sends SONG ENTRY (1:N) | Same | `song_entry.country_code` |
| SONG ENTRY takes part in CONTEST (N:1) | Same | `song_entry.year` |
| SONG ENTRY performs in ROUND (N:N) | A new table with both keys as its primary key, plus the attributes of the relationship | `performance` |
| PERSON is credited on SONG ENTRY (N:N, attribute role) | A new table. `role` joins the key because one person can be composer and lyricist of the same song | `entry_credit` |
| COUNTRY votes for COUNTRY in ROUND (three ends) | A new table with the three keys as its primary key | `vote` |
| BOOKMAKER quotes odds for SONG ENTRY in ROUND (three ends) | A new table with the three keys as its primary key | `betting_odds` |

## Other constraints

| Table | Constraint |
|---|---|
| country | `name` is unique and not null |
| contest | `year` is 1956 or later |
| round | (`year`, `round_type`) is unique; `round_type` is one of final, semi-final, semi-final-1, semi-final-2 |
| song_entry | (`year`, `country_code`, `performer`, `song`) is unique; `performer` is not null; `place_contest` is above 0 |
| performance | `running_order` and `place` are above 0; the three points columns are 0 or more |
| vote | `total_points` is not null and 0 or more; a country can appear as giver and receiver of the same row only with 0 points |
| person, bookmaker | `name` is unique and not null |
| entry_credit | `role` is composer or lyricist |
| betting_odds | `odds` is 1 or more |

## Normal form

Every table is in third normal form: each has a key, no column holds a list, and every other column depends on the whole key and on nothing else. The three source files were not: `contestants.csv` repeated the country name in every row, stored the final and the semi-final as two groups of columns, and kept composers and lyricists as lists inside one cell.

## Justified exceptions

1. **Surrogate keys `entry_id`, `round_id`, `person_id`.** The natural key of an entry would be (year, country), but in 1956 each country sent two songs, and `song` is empty in three rows. A numeric key is used and the natural combination is protected by a UNIQUE constraint. `round_id` and `person_id` avoid repeating two-column or text keys in every child table.
2. **`vote` refers to countries, not to song entries.** Votes are cast by a country for a country. The entry that received them is found through the year of the round and the receiving country. This would be ambiguous only if a country had two entries in a year with votes; that happens only in 1956, which has no votes.
3. **`vote.total_points` is stored although it can be derived.** From 2016 it equals `tele_points + jury_points` (profile query P26: no exceptions). Before 2016 the two parts do not exist, so the total cannot be removed. It is kept for all years to give the queries one column to read.
4. **`song_entry.place_contest` is stored although part of it can be derived.** For finalists it equals the place in the final. For entries eliminated in a semi-final it is an overall position that cannot be computed from the other columns, so the source value is kept.
5. **`performance.points` is stored although it equals the sum of the votes received.** Profile query P33 shows the two agree for every final. The column is kept because the votes are missing for 1956, 2020 and the 2023 semi-finals, where the points exist only here.
6. **Rows of a country voting for itself are kept.** The source has one such row per country and round, always with 0 points. They carry no information, but removing them would be a filter applied outside SQL. They are loaded as delivered, a CHECK constraint states that such a row can only hold 0 points, and the queries that average votes exclude them with a condition.
7. **`contest` has a single column.** It exists so that rounds and entries of the same year refer to one row, and so that a year can exist before its rounds and entries do (query Q13).
8. **Rounds of 2020.** The 2020 contest was cancelled, yet `round` has three rows for it: the entries had been allocated to semi-finals and bookmakers had published odds. The rows describe planned rounds, not held ones.
