-- Q03. Which countries have taken part but never won, and how close did they come?
-- Constructs: subquery with NOT IN, JOIN, GROUP BY, aggregates.
-- Parameters: min_entries=10
-- Meaning: It separates the countries that are still waiting for a first victory from the winners, and shows how long and how nearly each has tried.
SELECT country.name AS country,
       COUNT(*) AS entries,
       MIN(song_entry.year) AS first_year,
       MIN(song_entry.place_contest) AS best_place
FROM country
JOIN song_entry ON song_entry.country_code = country.country_code
WHERE country.country_code NOT IN (
    SELECT song_entry.country_code
    FROM performance
    JOIN round ON round.round_id = performance.round_id
    JOIN song_entry ON song_entry.entry_id = performance.entry_id
    WHERE round.round_type = 'final'
      AND performance.place = 1
)
GROUP BY country.country_code, country.name
HAVING COUNT(*) >= :min_entries
ORDER BY entries DESC;
