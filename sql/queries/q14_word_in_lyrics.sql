-- Q14. In which decades do the lyrics most often contain a given word?
-- Constructs: LEFT JOIN of a table with itself, LIKE with a parameter, COUNT(*) against COUNT(column), GROUP BY on an expression.
-- Parameters: pattern=%love%
-- Meaning: The share of entries whose lyrics contain a word shows how a theme or a language rose and fell over the decades; the share is used because the number of entries per decade grew a lot.
SELECT all_entries.year / 10 * 10 AS decade,
       COUNT(*) AS entries_with_lyrics,
       COUNT(matching.entry_id) AS entries_with_word,
       ROUND(100.0 * COUNT(matching.entry_id) / COUNT(*), 1) AS percent
FROM song_entry AS all_entries
LEFT JOIN song_entry AS matching
       ON matching.entry_id = all_entries.entry_id
      AND LOWER(matching.lyrics) LIKE :pattern
WHERE all_entries.lyrics IS NOT NULL
GROUP BY all_entries.year / 10 * 10
ORDER BY decade;
