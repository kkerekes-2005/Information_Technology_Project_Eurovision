-- Q11. How well did the bookmakers predict the final: where did their favourites finish?
-- Constructs: two chained CTEs, AVG, RANK with PARTITION BY, JOIN of five tables.
-- Parameters: year_from=2015; year_to=2023; max_odds_rank=3
-- Meaning: Comparing the rank given by the average odds with the real place tests whether the betting market is a reliable forecast of the contest.
WITH average_odds AS (
    SELECT betting_odds.entry_id,
           betting_odds.round_id,
           COUNT(betting_odds.odds) AS bookmakers,
           ROUND(AVG(betting_odds.odds), 2) AS average_odds
    FROM betting_odds
    JOIN round ON round.round_id = betting_odds.round_id
    WHERE round.round_type = 'final'
      AND round.year BETWEEN :year_from AND :year_to
    GROUP BY betting_odds.entry_id, betting_odds.round_id
),
ranked AS (
    SELECT entry_id, round_id, bookmakers, average_odds,
           RANK() OVER (
               PARTITION BY round_id
               ORDER BY average_odds
           ) AS odds_rank
    FROM average_odds
)
SELECT song_entry.year,
       country.name AS country,
       song_entry.performer,
       ranked.bookmakers,
       ranked.average_odds,
       ranked.odds_rank,
       performance.place AS real_place
FROM ranked
JOIN performance ON performance.entry_id = ranked.entry_id
                AND performance.round_id = ranked.round_id
JOIN song_entry ON song_entry.entry_id = ranked.entry_id
JOIN country ON country.country_code = song_entry.country_code
WHERE performance.place IS NOT NULL
  AND ranked.odds_rank <= :max_odds_rank
ORDER BY song_entry.year, ranked.odds_rank;
