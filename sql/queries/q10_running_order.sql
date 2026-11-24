-- Q10. Is the position in the running order of the final related to the result?
-- Constructs: JOIN, GROUP BY with HAVING, AVG, MIN.
-- Parameters: year_from=2004; year_to=2023; min_performances=10
-- Meaning: If the order did not matter the average place would be the same for every position; a better average for late positions supports the common belief that performing late helps.
SELECT performance.running_order,
       COUNT(*) AS performances,
       ROUND(AVG(performance.place), 2) AS average_place,
       MIN(performance.place) AS best_place
FROM performance
JOIN round ON round.round_id = performance.round_id
WHERE round.round_type = 'final'
  AND performance.place IS NOT NULL
  AND performance.running_order IS NOT NULL
  AND round.year BETWEEN :year_from AND :year_to
GROUP BY performance.running_order
HAVING COUNT(*) >= :min_performances
ORDER BY performance.running_order;
