-- Q04. For a chosen country, which countries give it the most points on average in the final?
-- Constructs: two chained CTEs, GROUP BY with HAVING, RANK with PARTITION BY, top N per group.
-- Parameters: country=se; year_from=1975; year_to=2015; min_contests=10; top_n=5
-- Meaning: It reveals the stable voting friends of a country; the period 1975 to 2015 is used because every country then gave the same 1 to 12 points, so the averages are comparable.
WITH pair_average AS (
    SELECT vote.to_country,
           vote.from_country,
           COUNT(*) AS contests,
           ROUND(AVG(vote.total_points), 2) AS average_points
    FROM vote
    JOIN round ON round.round_id = vote.round_id
    WHERE round.round_type = 'final'
      AND vote.from_country <> vote.to_country
      AND round.year BETWEEN :year_from AND :year_to
    GROUP BY vote.to_country, vote.from_country
    HAVING COUNT(*) >= :min_contests
),
ranked AS (
    SELECT to_country, from_country, contests, average_points,
           RANK() OVER (
               PARTITION BY to_country
               ORDER BY average_points DESC
           ) AS rank_for_receiver
    FROM pair_average
)
SELECT giver.name AS giver,
       ranked.contests,
       ranked.average_points,
       ranked.rank_for_receiver
FROM ranked
JOIN country AS giver ON giver.country_code = ranked.from_country
WHERE ranked.to_country = :country
  AND ranked.rank_for_receiver <= :top_n
ORDER BY ranked.rank_for_receiver, giver.name;
