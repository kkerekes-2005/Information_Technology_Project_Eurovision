# Data profile of the raw files

Every figure below is the result of a query in `sql/profiling.sql`, run on the staging tables (the raw CSV files loaded unchanged, all columns as text). The query number is given so the result can be reproduced. Results obtained on 2026-11-15 on PostgreSQL 16 with the files of dataset release `2023`.

## 1. Row count of every file (P01)

| File | Rows |
|---|---|
| `contestants.csv` | 1,734 |
| `votes.csv` | 51,354 |
| `betting_offices.csv` | 9,453 |

## 2. Candidate keys

| File | Candidate key | Unique? | Query |
|---|---|---|---|
| votes | year, round, from_country_id, to_country_id | Yes, 0 repeated | P05 |
| contestants | year, to_country_id | No, 20 repeated pairs | P06 |
| betting_offices | betting_bm_id, year, page_url, contest_round | Yes, 0 repeated | P08 |

The 20 repeated pairs of contestants are of two kinds. Five are in 1956, when each country sent two songs: real data, so (year, country) is not a key. Fifteen are in 2023, where the same entry is written on two rows, one with the semi-final result and one with the final result or nothing (P07).

## 3. Nulls per column

contestants, 1,734 rows (P02):

| Column | Values | Missing |
|---|---|---|
| year, to_country_id, to_country, performer | 1,734 | 0 |
| song | 1,731 | 3 |
| place_contest | 1,678 | 56 |
| sf_num | 640 | 1,094 |
| running_final | 1,398 | 336 |
| place_final | 1,397 | 337 |
| points_final | 1,385 | 349 |
| running_sf, place_sf, points_sf | 605 | 1,129 |
| points_tele_final, points_jury_final | 181 | 1,553 |
| points_tele_sf, points_jury_sf | 212 | 1,522 |
| composers | 1,680 | 54 |
| lyricists | 985 | 749 |
| lyrics, youtube_url | 1,722 | 12 |

votes, 51,354 rows (P03): no missing value in the first seven columns. `tele_points` has 11,741 values and `jury_points` 11,715, so about 77% of the rows have neither.

betting_offices, 9,453 rows (P04): `betting_score` is missing in 46 rows, `country_name` and `country_code` in 324 rows. The other columns are complete.

## 4. Value ranges and formats

| Finding | Result | Query |
|---|---|---|
| Years in contestants | 1956 to 2023, 68 years | P19 |
| Years in votes | 1957 to 2023, 66 years | P19 |
| Years in betting_offices | 2015 to 2023, 9 years | P19 |
| place_contest | 1 to 43 | P20 |
| place_final, running_final | 1 to 27 | P20 |
| points_final | 0 to 758 | P20 |
| points_sf | up to 403 | P20 |
| Points of one vote | 0 to 24, 23 different values | P21 |
| Odds | 1.0 to 1001.0 | P21 |
| Longest performer / song / country name | 46 / 47 / 26 characters | P22 |
| Longest lyrics | 3,434 characters | P22 |
| Integers written as decimals (`27.0`) | 482 values of place_final, 640 of sf_num, 962 of jury_points | P12, P13 |
| Round labels in votes | final (37,506 rows, 1957 to 2023), semi-final (3,751, 2004 to 2007), semi-final-1 (4,945, 2008 to 2022), semi-final-2 (5,152, 2008 to 2022) | P14 |
| sf_num | 0.0 in 2004 to 2007, 1.0 and 2.0 from 2008, empty in 1,094 rows | P15 |

## 5. Duplicates, codes without a meaning, unexpected content

| # | Finding | Result | Query | Cleaning rule |
|---|---|---|---|---|
| 1 | The country "code" of contestants is a full country name in some rows | 259 rows of 1,734, in every year from 2004 to 2020 | P09, P10 | R4 |
| 2 | One code written with two names | `cz`: Czech Republic (4) and Czechia (4); `mk`: North Macedonia (9) and North MacedoniaN.Macedonia (2) | P11 | R5 |
| 3 | Codes used in votes that never appear as a code in contestants | `ad`, `wld` | P30 | R6 |
| 4 | Votes of a country for itself | 1,975 rows, 0 points in total | P23 | R7: kept as delivered; a CHECK allows them only with 0 points and the vote queries exclude them in SQL |
| 5 | `from_country` and `to_country` of votes repeat the code columns | differ in 0 rows | P24 | R8 |
| 6 | Entries of 2023 written on two rows | 15 entries | P06, P07 | R9 |
| 7 | Several names in one cell | 577 rows with several composers, 238 with several lyricists | P16 | R10 |
| 8 | Lyrics contain the two characters `\n` instead of line breaks | 1,722 rows | P17 | R11 |
| 9 | The 2020 odds are the same under the three round labels | 779 rows per label, 0 differences | P37, P38 | R14 |
| 10 | Every 1956 entry has place 2, the winner included | 12 of 12 entries | P31 | R15 |
| 11 | `country_code` of the betting file equals `country_name` | differs in 0 rows; it is a name, not a code | P34 | R13 |
| 12 | Betting uses a country name that contestants does not | FYR Macedonia | P35 | R13 |
| 13 | Matching betting rows to entries by performer and song fails | 1,055 rows, 37 entries | P36 | R13 (match by `page_url`) |
| 14 | `betting_sc_id` has no documented meaning | 135 values for 33 bookmakers | P39 | R13 (not loaded) |
| 15 | Performer names with outer spaces in the betting file | 35 rows | P18 | column not loaded |

## 6. Gaps in the source that cannot be repaired

| Finding | Result | Query |
|---|---|---|
| Years with contestants and no votes | 1956, 2020 | P28 |
| 2020 entries without a place | 41 of 41; 35 have a semi-final number | P32 |
| 2023 has no semi-final votes | only `final` rows for 2023 | P29 |
| Televote and jury split | exists from 2016 only | P25 |
| Rows with televote and no jury points | 26, all from `wld` in the 2023 final | P27 |

## 7. Consistency checks that passed

| Check | Result | Query |
|---|---|---|
| Where televote and jury points both exist, total_points is their sum | 0 exceptions | P26 |
| points_final of contestants equals the sum of the final votes received | 0 exceptions | P33 |
| A bookmaker id always has the same name | 0 exceptions | P40 |

## 8. Consequences for the design

- (year, country) cannot be the primary key of the entries: a surrogate key is used.
- Final and semi-final results are separate rows of one table, which also absorbs the split rows of 2023.
- Composers and lyricists need their own table and a link table.
- `total_points` cannot be dropped in favour of televote + jury, because the split exists only from 2016.
- Column sizes: `VARCHAR(100)` for performer and song and `VARCHAR(50)` for country names are above the longest values found.
