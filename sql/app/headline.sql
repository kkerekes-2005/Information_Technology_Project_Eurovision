-- Headline numbers shown in the cards at the top of the app.
-- Votes of a country for itself (0 points) are not counted.
SELECT (SELECT COUNT(*) FROM contest) AS contests,
       (SELECT COUNT(*) FROM song_entry) AS entries,
       (SELECT COUNT(DISTINCT country_code) FROM song_entry) AS countries,
       (SELECT COUNT(*) FROM vote WHERE from_country <> to_country) AS votes;
