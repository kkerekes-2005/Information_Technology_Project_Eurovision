-- Q01. Which countries have won the contest most often, and when did each one last win?
-- Constructs: JOIN of four tables, GROUP BY, COUNT, MAX.
-- Parameters: year_from=1957; year_to=2023
-- Meaning: It ranks the countries by victories within any period, which shows who dominated which era of the contest.
SELECT country.name AS country,
       COUNT(*) AS wins,
       MAX(song_entry.year) AS last_win
FROM performance
JOIN round ON round.round_id = performance.round_id
JOIN song_entry ON song_entry.entry_id = performance.entry_id
JOIN country ON country.country_code = song_entry.country_code
WHERE round.round_type = 'final'
  AND performance.place = 1
  AND song_entry.year BETWEEN :year_from AND :year_to
GROUP BY country.country_code, country.name
ORDER BY wins DESC, last_win DESC;
