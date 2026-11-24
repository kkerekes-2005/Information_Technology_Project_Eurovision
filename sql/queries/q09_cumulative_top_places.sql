-- Q09. How did the number of top finishes of chosen countries accumulate over the years?
-- Constructs: CTE, running total with SUM OVER, PARTITION BY and ORDER BY, list parameter with ANY.
-- Parameters: countries=[se,ie,gb,ua]; max_place=5
-- Meaning: A running total turns isolated good results into a curve, so periods of success and long droughts of each country become visible and comparable.
WITH top_finishes AS (
    SELECT country.name AS country,
           song_entry.year,
           COUNT(*) AS top_finishes
    FROM performance
    JOIN round ON round.round_id = performance.round_id
    JOIN song_entry ON song_entry.entry_id = performance.entry_id
    JOIN country ON country.country_code = song_entry.country_code
    WHERE round.round_type = 'final'
      AND performance.place <= :max_place
      AND song_entry.country_code = ANY(:countries)
    GROUP BY country.name, song_entry.year
)
SELECT country, year,
       SUM(top_finishes) OVER (
           PARTITION BY country
           ORDER BY year
       ) AS cumulative_top_finishes
FROM top_finishes
ORDER BY country, year;
