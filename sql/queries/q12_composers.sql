-- Q12. Which composers have written the most entries, and how did their songs do?
-- Constructs: JOIN through the N:N table entry_credit, GROUP BY with HAVING, aggregates.
-- Parameters: min_entries=6
-- Meaning: It identifies the professional songwriters behind many entries, often for several countries, who are invisible in a list of performers.
SELECT person.name AS composer,
       COUNT(*) AS entries,
       COUNT(DISTINCT song_entry.country_code) AS countries,
       MIN(song_entry.year) AS first_year,
       MAX(song_entry.year) AS last_year,
       MIN(song_entry.place_contest) AS best_place
FROM person
JOIN entry_credit ON entry_credit.person_id = person.person_id
JOIN song_entry ON song_entry.entry_id = entry_credit.entry_id
WHERE entry_credit.role = 'composer'
GROUP BY person.person_id, person.name
HAVING COUNT(*) >= :min_entries
ORDER BY entries DESC, best_place;
