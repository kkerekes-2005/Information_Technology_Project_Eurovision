-- Q08. Which countries of the database have never appeared in a final, and how many entries did they send?
-- Constructs: CTE, two LEFT JOIN, IS NULL, COUNT(column) after a LEFT JOIN.
-- Parameters: none
-- Meaning: The LEFT JOIN keeps the countries without a match, so it finds both the country that always failed in the semi-finals and the voting-only code that never sent a song.
WITH finalists AS (
    SELECT DISTINCT song_entry.country_code
    FROM performance
    JOIN round ON round.round_id = performance.round_id
    JOIN song_entry ON song_entry.entry_id = performance.entry_id
    WHERE round.round_type = 'final'
)
SELECT country.name AS country,
       COUNT(song_entry.entry_id) AS entries,
       MIN(song_entry.year) AS first_year,
       MAX(song_entry.year) AS last_year
FROM country
LEFT JOIN finalists ON finalists.country_code = country.country_code
LEFT JOIN song_entry ON song_entry.country_code = country.country_code
WHERE finalists.country_code IS NULL
GROUP BY country.country_code, country.name
ORDER BY entries DESC;
