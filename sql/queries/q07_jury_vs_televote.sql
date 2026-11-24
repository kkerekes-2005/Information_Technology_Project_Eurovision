-- Q07. In the finals since 2016, how did the televote rank and the jury rank of each entry differ?
-- Constructs: JOIN, two RANK window functions with PARTITION BY, arithmetic.
-- Parameters: year_from=2016; year_to=2023; min_gap=15
-- Meaning: Ranking each entry twice inside its own year shows which songs the public loved and the juries did not, and the reverse, independent of how many points were available.
WITH ranked AS (
    SELECT song_entry.year,
           country.name AS country,
           song_entry.performer,
           performance.points_tele,
           performance.points_jury,
           RANK() OVER (
               PARTITION BY song_entry.year
               ORDER BY performance.points_tele DESC
           ) AS tele_rank,
           RANK() OVER (
               PARTITION BY song_entry.year
               ORDER BY performance.points_jury DESC
           ) AS jury_rank
    FROM performance
    JOIN round ON round.round_id = performance.round_id
    JOIN song_entry ON song_entry.entry_id = performance.entry_id
    JOIN country ON country.country_code = song_entry.country_code
    WHERE round.round_type = 'final'
      AND performance.points_tele IS NOT NULL
      AND performance.points_jury IS NOT NULL
      AND song_entry.year BETWEEN :year_from AND :year_to
)
SELECT year, country, performer, points_tele, points_jury,
       tele_rank, jury_rank,
       jury_rank - tele_rank AS public_favoured_by
FROM ranked
WHERE jury_rank - tele_rank >= :min_gap
   OR tele_rank - jury_rank >= :min_gap
ORDER BY year, tele_rank;
