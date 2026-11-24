-- Q05. How did the final place of a country change from each of its finals to the next?
-- Constructs: two chained CTEs, LAG.
-- Parameters: country=se
-- Meaning: The difference with the previous final shows the rises and falls of a country over the years, which a list of places alone hides.
WITH finals AS (
    SELECT song_entry.year,
           song_entry.performer,
           performance.place
    FROM performance
    JOIN round ON round.round_id = performance.round_id
    JOIN song_entry ON song_entry.entry_id = performance.entry_id
    WHERE round.round_type = 'final'
      AND performance.place IS NOT NULL
      AND song_entry.country_code = :country
),
with_previous AS (
    SELECT year, performer, place,
           LAG(place) OVER (ORDER BY year) AS previous_place
    FROM finals
)
SELECT year, performer, place, previous_place,
       previous_place - place AS places_gained
FROM with_previous
ORDER BY year;
