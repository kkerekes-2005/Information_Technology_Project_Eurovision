-- Q13. How is a new contest registered so that either all of its rows are saved or none?
-- Constructs: INSERT, UPDATE and DELETE inside BEGIN ... COMMIT, a failed statement followed by ROLLBACK.
-- Meaning: A contest is only usable when its year, round, entry and result exist together; the transaction guarantees that a failure halfway never leaves a contest without its rows.
--
-- Run each part separately in the pgAdmin Query Tool: select the part and press F5.
-- The ids 104 and 1720 are the next free ones: the load ends at round 103 and entry 1719.
-- The 2024 winner is used as the example (source: eurovisionworld.com/eurovision/2024,
-- checked on 2026-11-15: 591 points, 226 public, 365 jury, running order 21).
-- Part 3 removes it again, so the database ends exactly as the dataset delivered it.

-- Part 1. Register the 2024 contest, its final, the winning entry and its result.
BEGIN;
INSERT INTO contest (year) VALUES (2024);
INSERT INTO round (round_id, year, round_type) VALUES (104, 2024, 'final');
INSERT INTO song_entry (entry_id, year, country_code, performer, song, place_contest)
VALUES (1720, 2024, 'ch', 'Nemo', 'The Code', 1);
INSERT INTO performance (entry_id, round_id, running_order, place, points, points_tele, points_jury)
VALUES (1720, 104, 21, 1, 591, 226, 365);
COMMIT;

-- Check: the four rows are there.
SELECT song_entry.year, country.name, song_entry.performer, song_entry.song,
       performance.place, performance.points
FROM performance
JOIN song_entry ON song_entry.entry_id = performance.entry_id
JOIN country ON country.country_code = song_entry.country_code
WHERE song_entry.year = 2024;

-- Part 2. A transaction that fails halfway. The UPDATE and the first vote are valid.
-- The second vote is Switzerland giving itself 12 points, which the CHECK constraint rejects.
BEGIN;
UPDATE performance SET running_order = 22 WHERE entry_id = 1720 AND round_id = 104;
INSERT INTO vote (round_id, from_country, to_country, total_points) VALUES (104, 'se', 'ch', 12);
INSERT INTO vote (round_id, from_country, to_country, total_points) VALUES (104, 'ch', 'ch', 12);
COMMIT;

-- After the error PostgreSQL ignores every statement until the transaction ends. End it:
ROLLBACK;

-- Check: the valid changes were undone too. running_order is still 21 and there are no votes.
SELECT performance.running_order,
       (SELECT COUNT(*) FROM vote WHERE round_id = 104) AS votes_in_round_104
FROM performance
WHERE entry_id = 1720 AND round_id = 104;

-- Part 3. Remove the 2024 contest again. Children first, because of the foreign keys.
BEGIN;
DELETE FROM performance WHERE round_id = 104;
DELETE FROM song_entry WHERE entry_id = 1720;
DELETE FROM round WHERE round_id = 104;
DELETE FROM contest WHERE year = 2024;
COMMIT;

-- Check: no rows are left for 2024.
SELECT COUNT(*) AS contests_2024 FROM contest WHERE year = 2024;
