-- Q06. Which pairs of countries give each other high points in both directions?
-- Constructs: CTE joined with itself, GROUP BY with HAVING.
-- Parameters: year_from=1975; year_to=2015; min_contests=10; min_average=6
-- Meaning: A high average in both directions over many contests is the pattern known as bloc voting, which a single generous vote cannot produce.
WITH pair_average AS (
    SELECT vote.from_country,
           vote.to_country,
           COUNT(*) AS contests,
           ROUND(AVG(vote.total_points), 2) AS average_points
    FROM vote
    JOIN round ON round.round_id = vote.round_id
    WHERE round.round_type = 'final'
      AND vote.from_country <> vote.to_country
      AND round.year BETWEEN :year_from AND :year_to
    GROUP BY vote.from_country, vote.to_country
    HAVING COUNT(*) >= :min_contests
)
SELECT first_country.name AS country_a,
       second_country.name AS country_b,
       a_to_b.average_points AS a_gives_b,
       b_to_a.average_points AS b_gives_a,
       a_to_b.contests AS contests
FROM pair_average AS a_to_b
JOIN pair_average AS b_to_a
  ON b_to_a.from_country = a_to_b.to_country
 AND b_to_a.to_country = a_to_b.from_country
JOIN country AS first_country ON first_country.country_code = a_to_b.from_country
JOIN country AS second_country ON second_country.country_code = a_to_b.to_country
WHERE a_to_b.from_country < a_to_b.to_country
  AND a_to_b.average_points >= :min_average
  AND b_to_a.average_points >= :min_average
ORDER BY a_to_b.average_points + b_to_a.average_points DESC;
