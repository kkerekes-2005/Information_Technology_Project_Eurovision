-- Data profile of the raw files, in SQL.
-- Before running: python scripts/load_staging.py
-- In pgAdmin, select one query with the mouse and press F5 to run only that query.
-- Each query has a number (P01, P02, ...) used in the report.

-- ===========================================================================
-- A. Size of every file
-- ===========================================================================

-- P01. Row count of every file. Three queries, one per file.
SELECT COUNT(*) AS contestants_rows FROM staging.contestants;
SELECT COUNT(*) AS votes_rows FROM staging.votes;
SELECT COUNT(*) AS betting_rows FROM staging.betting_offices;

-- ===========================================================================
-- B. Nulls per column. COUNT(*) counts rows, COUNT(column) ignores NULL.
-- ===========================================================================

-- P02. contestants: values present in each column.
SELECT COUNT(*) AS total_rows,
       COUNT(year) AS with_year,
       COUNT(to_country_id) AS with_country_id,
       COUNT(to_country) AS with_country,
       COUNT(performer) AS with_performer,
       COUNT(song) AS with_song,
       COUNT(place_contest) AS with_place_contest,
       COUNT(sf_num) AS with_sf_num,
       COUNT(running_final) AS with_running_final,
       COUNT(running_sf) AS with_running_sf,
       COUNT(place_final) AS with_place_final,
       COUNT(points_final) AS with_points_final,
       COUNT(place_sf) AS with_place_sf,
       COUNT(points_sf) AS with_points_sf,
       COUNT(points_tele_final) AS with_points_tele_final,
       COUNT(points_jury_final) AS with_points_jury_final,
       COUNT(points_tele_sf) AS with_points_tele_sf,
       COUNT(points_jury_sf) AS with_points_jury_sf,
       COUNT(composers) AS with_composers,
       COUNT(lyricists) AS with_lyricists,
       COUNT(lyrics) AS with_lyrics,
       COUNT(youtube_url) AS with_youtube_url
FROM staging.contestants;

-- P03. votes: values present in each column.
SELECT COUNT(*) AS total_rows,
       COUNT(year) AS with_year,
       COUNT(round) AS with_round,
       COUNT(from_country_id) AS with_from_id,
       COUNT(to_country_id) AS with_to_id,
       COUNT(from_country) AS with_from_country,
       COUNT(to_country) AS with_to_country,
       COUNT(total_points) AS with_total_points,
       COUNT(tele_points) AS with_tele_points,
       COUNT(jury_points) AS with_jury_points
FROM staging.votes;

-- P04. betting_offices: values present in each column.
SELECT COUNT(*) AS total_rows,
       COUNT(betting_bm_id) AS with_bm_id,
       COUNT(betting_sc_id) AS with_sc_id,
       COUNT(betting_name) AS with_name,
       COUNT(betting_score) AS with_score,
       COUNT(year) AS with_year,
       COUNT(performer) AS with_performer,
       COUNT(song) AS with_song,
       COUNT(page_url) AS with_page_url,
       COUNT(contest_round) AS with_round,
       COUNT(country_name) AS with_country_name,
       COUNT(country_code) AS with_country_code
FROM staging.betting_offices;

-- ===========================================================================
-- C. Candidate keys: are they really unique?
-- ===========================================================================

-- P05. votes: (year, round, giver, receiver). No rows means the key is unique.
SELECT year, round, from_country_id, to_country_id, COUNT(*) AS times
FROM staging.votes
GROUP BY year, round, from_country_id, to_country_id
HAVING COUNT(*) > 1;

-- P06. contestants: (year, country). The rows returned are the repeated pairs.
SELECT year, to_country_id, COUNT(*) AS times
FROM staging.contestants
GROUP BY year, to_country_id
HAVING COUNT(*) > 1
ORDER BY year, to_country_id;

-- P07. The repeated pairs of 2023: one row holds the final, the other the semi-final.
SELECT to_country_id, performer, song, sf_num, place_sf, place_final, points_final
FROM staging.contestants
WHERE year = '2023'
  AND to_country_id IN (
      SELECT to_country_id
      FROM staging.contestants
      WHERE year = '2023'
      GROUP BY to_country_id
      HAVING COUNT(*) > 1
  )
ORDER BY to_country_id, place_final;

-- P08. betting_offices: (bookmaker, year, page, round). No rows means unique.
SELECT betting_bm_id, year, page_url, contest_round, COUNT(*) AS times
FROM staging.betting_offices
GROUP BY betting_bm_id, year, page_url, contest_round
HAVING COUNT(*) > 1;

-- ===========================================================================
-- D. Formats and codes
-- ===========================================================================

-- P09. Length of the country code in contestants. A code has 2 letters.
SELECT LENGTH(to_country_id) AS code_length, COUNT(*) AS total_rows
FROM staging.contestants
GROUP BY LENGTH(to_country_id)
ORDER BY code_length;

-- P10. Rows whose "code" is a country name, per year.
SELECT year, COUNT(*) AS rows_with_name_as_code
FROM staging.contestants
WHERE LENGTH(to_country_id) > 3
GROUP BY year
ORDER BY year;

-- P11. Country codes written with more than one name.
SELECT to_country_id, to_country, COUNT(*) AS total_rows
FROM staging.contestants
WHERE to_country_id IN (
    SELECT to_country_id
    FROM staging.contestants
    GROUP BY to_country_id
    HAVING COUNT(DISTINCT to_country) > 1
)
GROUP BY to_country_id, to_country
ORDER BY to_country_id, to_country;

-- P12. Integers written as decimals, such as 27.0.
SELECT COUNT(*) AS place_final_decimal
FROM staging.contestants
WHERE place_final LIKE '%.0';

SELECT COUNT(*) AS sf_num_decimal
FROM staging.contestants
WHERE sf_num LIKE '%.0';

-- P13. Same check in votes.
SELECT COUNT(*) AS jury_points_decimal
FROM staging.votes
WHERE jury_points LIKE '%.0';

-- P14. Round labels in votes.
SELECT round, COUNT(*) AS total_rows, MIN(year) AS first_year, MAX(year) AS last_year
FROM staging.votes
GROUP BY round
ORDER BY round;

-- P15. Values of sf_num and the years in which each one is used.
SELECT sf_num, COUNT(*) AS total_rows, MIN(year) AS first_year, MAX(year) AS last_year
FROM staging.contestants
GROUP BY sf_num
ORDER BY sf_num;

-- P16. Lists inside one cell: several composers or lyricists separated by ';'.
SELECT COUNT(*) AS several_composers
FROM staging.contestants
WHERE composers LIKE '%;%';

SELECT COUNT(*) AS several_lyricists
FROM staging.contestants
WHERE lyricists LIKE '%;%';

-- P17. Lyrics with the two characters \n instead of a line break.
SELECT COUNT(*) AS lyrics_with_backslash_n
FROM staging.contestants
WHERE lyrics LIKE '%\\n%';

-- P18. Text with spaces at the start or the end.
SELECT COUNT(*) AS performer_with_spaces
FROM staging.betting_offices
WHERE performer <> TRIM(performer);

-- ===========================================================================
-- E. Value ranges
-- ===========================================================================

-- P19. Years covered by each file.
SELECT MIN(year) AS first_year, MAX(year) AS last_year, COUNT(DISTINCT year) AS years
FROM staging.contestants;

SELECT MIN(year) AS first_year, MAX(year) AS last_year, COUNT(DISTINCT year) AS years
FROM staging.votes;

SELECT MIN(year) AS first_year, MAX(year) AS last_year, COUNT(DISTINCT year) AS years
FROM staging.betting_offices;

-- P20. Ranges of the numbers in contestants.
SELECT MIN(CAST(place_contest AS NUMERIC)) AS min_place_contest,
       MAX(CAST(place_contest AS NUMERIC)) AS max_place_contest,
       MIN(CAST(place_final AS NUMERIC)) AS min_place_final,
       MAX(CAST(place_final AS NUMERIC)) AS max_place_final,
       MIN(CAST(points_final AS NUMERIC)) AS min_points_final,
       MAX(CAST(points_final AS NUMERIC)) AS max_points_final,
       MAX(CAST(running_final AS NUMERIC)) AS max_running_final,
       MAX(CAST(points_sf AS NUMERIC)) AS max_points_sf
FROM staging.contestants;

-- P21. Ranges of the points in votes and of the odds.
SELECT MIN(CAST(total_points AS NUMERIC)) AS min_points,
       MAX(CAST(total_points AS NUMERIC)) AS max_points,
       COUNT(DISTINCT total_points) AS different_values
FROM staging.votes;

SELECT MIN(CAST(betting_score AS NUMERIC)) AS min_odds,
       MAX(CAST(betting_score AS NUMERIC)) AS max_odds
FROM staging.betting_offices;

-- P22. Longest text of each column, to choose the VARCHAR sizes.
SELECT MAX(LENGTH(to_country)) AS country_name,
       MAX(LENGTH(performer)) AS performer,
       MAX(LENGTH(song)) AS song,
       MAX(LENGTH(youtube_url)) AS youtube_url,
       MAX(LENGTH(composers)) AS composers_list,
       MAX(LENGTH(lyrics)) AS lyrics
FROM staging.contestants;

-- ===========================================================================
-- F. Unexpected content
-- ===========================================================================

-- P23. Votes of a country for itself, and the points they carry.
SELECT COUNT(*) AS self_votes, SUM(CAST(total_points AS NUMERIC)) AS points_in_them
FROM staging.votes
WHERE from_country_id = to_country_id;

-- P24. Do from_country / to_country add anything to the code columns?
SELECT COUNT(*) AS rows_where_they_differ
FROM staging.votes
WHERE from_country <> from_country_id OR to_country <> to_country_id;

-- P25. Televote and jury points: from which year, and in how many rows.
SELECT MIN(year) AS first_year_with_split,
       COUNT(tele_points) AS rows_with_tele,
       COUNT(jury_points) AS rows_with_jury
FROM staging.votes
WHERE tele_points IS NOT NULL;

-- P26. Where both exist, is total_points their sum? No rows means always.
SELECT year, round, from_country_id, to_country_id, total_points, tele_points, jury_points
FROM staging.votes
WHERE tele_points IS NOT NULL AND jury_points IS NOT NULL
  AND CAST(total_points AS NUMERIC)
      <> CAST(tele_points AS NUMERIC) + CAST(jury_points AS NUMERIC);

-- P27. Rows with televote but no jury points.
SELECT year, round, from_country_id, COUNT(*) AS total_rows
FROM staging.votes
WHERE tele_points IS NOT NULL AND jury_points IS NULL
GROUP BY year, round, from_country_id;

-- P28. Years that have contestants but no votes.
SELECT DISTINCT year
FROM staging.contestants
WHERE year NOT IN (SELECT year FROM staging.votes)
ORDER BY year;

-- P29. Semi-final votes per year from 2019: 2023 has none.
SELECT year, round, COUNT(*) AS total_rows
FROM staging.votes
WHERE year >= '2019'
GROUP BY year, round
ORDER BY year, round;

-- P30. Country codes used in votes that never appear as a code in contestants.
SELECT DISTINCT v.from_country_id
FROM staging.votes v
LEFT JOIN staging.contestants c ON c.to_country_id = v.from_country_id
WHERE c.to_country_id IS NULL;

-- P31. The places of 1956: every entry has the same place.
SELECT place_contest, place_final, COUNT(*) AS entries
FROM staging.contestants
WHERE year = '1956'
GROUP BY place_contest, place_final;

-- P32. 2020, the cancelled contest: no entry has a place.
SELECT COUNT(*) AS entries_2020,
       COUNT(place_contest) AS with_place,
       COUNT(sf_num) AS with_semi_final_number
FROM staging.contestants
WHERE year = '2020';

-- P33. Do the final points of contestants equal the sum of the votes received?
--      Only rows with a real country code can be compared. No rows means they agree.
WITH received AS (
    SELECT year, to_country_id, SUM(CAST(total_points AS NUMERIC)) AS points_from_votes
    FROM staging.votes
    WHERE round = 'final'
    GROUP BY year, to_country_id
)
SELECT c.year, c.to_country_id, c.points_final, r.points_from_votes
FROM staging.contestants c
JOIN received r ON r.year = c.year AND r.to_country_id = c.to_country_id
WHERE c.points_final IS NOT NULL
  AND CAST(c.points_final AS NUMERIC) <> r.points_from_votes;

-- ===========================================================================
-- G. Betting file
-- ===========================================================================

-- P34. country_code holds the same text as country_name, not a code.
SELECT COUNT(*) AS total_rows,
       COUNT(country_name) AS with_country_name
FROM staging.betting_offices;

SELECT COUNT(*) AS rows_where_code_differs_from_name
FROM staging.betting_offices
WHERE country_code <> country_name;

-- P35. Country names of the betting file that contestants does not use.
SELECT DISTINCT b.country_name
FROM staging.betting_offices b
LEFT JOIN staging.contestants c ON c.to_country = b.country_name
WHERE b.country_name IS NOT NULL AND c.to_country IS NULL;

-- P36. Betting rows that find no contestant with the same year, performer and song.
SELECT COUNT(*) AS rows_without_match,
       COUNT(DISTINCT b.page_url) AS different_entries
FROM staging.betting_offices b
LEFT JOIN staging.contestants c
       ON c.year = b.year
      AND TRIM(c.performer) = TRIM(b.performer)
      AND TRIM(c.song) = TRIM(b.song)
WHERE c.year IS NULL;

-- P37. Rows per year and round. In 2020 the three rounds have the same number.
SELECT year, contest_round, COUNT(*) AS total_rows
FROM staging.betting_offices
GROUP BY year, contest_round
ORDER BY year, contest_round;

-- P38. 2020: odds listed under the final that are missing or different under
--      semi-final-1. A count of 0 means the two sets are the same.
SELECT COUNT(*) AS final_rows_not_repeated
FROM staging.betting_offices f
LEFT JOIN staging.betting_offices s
       ON s.year = '2020'
      AND s.contest_round = 'semi-final-1'
      AND s.betting_bm_id = f.betting_bm_id
      AND s.page_url = f.page_url
WHERE f.year = '2020'
  AND f.contest_round = 'final'
  AND (s.betting_bm_id IS NULL OR s.betting_score <> f.betting_score);

-- P39. betting_sc_id: a code without a documented meaning.
SELECT COUNT(DISTINCT betting_sc_id) AS different_sc_ids,
       COUNT(DISTINCT betting_bm_id) AS different_bookmakers
FROM staging.betting_offices;

-- P40. Does a bookmaker id always carry the same name? No rows means yes.
SELECT betting_bm_id, COUNT(DISTINCT betting_name) AS names
FROM staging.betting_offices
GROUP BY betting_bm_id
HAVING COUNT(DISTINCT betting_name) > 1;
