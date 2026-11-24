-- Q02. Among the countries with at least a given number of finals, which have the best average place in the final?
-- Constructs: JOIN, GROUP BY with HAVING, AVG, MIN.
-- Parameters: min_finals=20
-- Meaning: An average over many finals measures consistency instead of single victories, and HAVING removes countries with too few finals for the average to mean anything.
SELECT country.name AS country,
       COUNT(*) AS finals,
       ROUND(AVG(performance.place), 2) AS average_place,
       MIN(performance.place) AS best_place
FROM performance
JOIN round ON round.round_id = performance.round_id
JOIN song_entry ON song_entry.entry_id = performance.entry_id
JOIN country ON country.country_code = song_entry.country_code
WHERE round.round_type = 'final'
  AND performance.place IS NOT NULL
GROUP BY country.country_code, country.name
HAVING COUNT(*) >= :min_finals
ORDER BY average_place;
