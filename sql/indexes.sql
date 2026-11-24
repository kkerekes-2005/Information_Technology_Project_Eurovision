-- Indexes on the large table, and the measurement of their effect.
-- Run after the load. sql/schema.sql drops the tables and their indexes with them,
-- so this file is run again after every new load.
-- In pgAdmin run one step at a time (select it, F5) and read the plan in Data Output.

DROP INDEX IF EXISTS idx_vote_to_country;
DROP INDEX IF EXISTS idx_vote_from_country;
DROP INDEX IF EXISTS idx_song_entry_country;

-- Step 1. Before the index: all the votes received by one country.
-- vote has 51,354 rows. Its primary key (round_id, from_country, to_country) starts
-- with round_id, so it cannot be used to search by to_country alone.
-- Expected plan: Seq Scan on vote, with "Rows Removed by Filter".
EXPLAIN ANALYZE
SELECT round_id, from_country, total_points
FROM vote
WHERE to_country = 'ad';

-- Step 2. Create the indexes.
-- to_country and from_country are the columns the vote queries filter and join on
-- (Q04, Q06). song_entry.country_code is the foreign key used by most joins.
CREATE INDEX idx_vote_to_country ON vote (to_country);
CREATE INDEX idx_vote_from_country ON vote (from_country);
CREATE INDEX idx_song_entry_country ON song_entry (country_code);

-- Step 3. After the index: the same query.
-- Expected plan: an Index Scan or Bitmap Index Scan on idx_vote_to_country,
-- and a shorter Execution Time.
EXPLAIN ANALYZE
SELECT round_id, from_country, total_points
FROM vote
WHERE to_country = 'ad';

-- Step 4. A condition that keeps most of the rows: the index is not used.
-- About half of the votes have 0 points, so reading the whole table is cheaper.
-- Expected plan: Seq Scan on vote, although an index could be created on this column.
EXPLAIN ANALYZE
SELECT round_id, from_country, to_country
FROM vote
WHERE total_points = 0;

-- Step 5. The indexes that exist now, including the ones PostgreSQL created
-- by itself for every PRIMARY KEY and UNIQUE constraint.
SELECT tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
