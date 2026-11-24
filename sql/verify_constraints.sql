-- Verification of the constraints after the load.
-- Run after python src/etl/load.py. One step at a time in pgAdmin (select, F5).

-- Step 1. Every constraint of the ten tables, by table and type.
-- Expected: 10 PRIMARY KEY, 13 FOREIGN KEY, 5 UNIQUE.
SELECT table_name, constraint_type, COUNT(*) AS constraints
FROM information_schema.table_constraints
WHERE table_schema = 'public'
  AND constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
GROUP BY table_name, constraint_type
ORDER BY table_name, constraint_type;

-- Step 2. The CHECK constraints written in the schema, with their rule. Expected: 14 rows.
SELECT table_constraints.table_name,
       check_constraints.constraint_name,
       check_constraints.check_clause
FROM information_schema.check_constraints
JOIN information_schema.table_constraints
  ON table_constraints.constraint_name = check_constraints.constraint_name
WHERE table_constraints.table_schema = 'public'
  AND check_constraints.constraint_name NOT LIKE '%not_null'
ORDER BY table_constraints.table_name, check_constraints.constraint_name;

-- Step 3. The NOT NULL columns. Expected: 26 rows.
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND is_nullable = 'NO'
ORDER BY table_name, ordinal_position;

-- Steps 4 to 9. Each statement breaks one rule on purpose and must fail.
-- Run them one by one. Nothing is saved, because a failed statement saves nothing.

-- Step 4. PRIMARY KEY: country 'se' already exists.
INSERT INTO country (country_code, name) VALUES ('se', 'Second Sweden');

-- Step 5. FOREIGN KEY: country 'zz' does not exist.
INSERT INTO vote (round_id, from_country, to_country, total_points) VALUES (1, 'se', 'zz', 5);

-- Step 6. UNIQUE: a second country with the name Sweden.
INSERT INTO country (country_code, name) VALUES ('s2', 'Sweden');

-- Step 7. NOT NULL: an entry without a performer.
INSERT INTO song_entry (entry_id, year, country_code, performer) VALUES (9999, 2023, 'se', NULL);

-- Step 8. CHECK: negative points.
INSERT INTO vote (round_id, from_country, to_country, total_points) VALUES (1, 'se', 'no', -3);

-- Step 9. CHECK: a round type that is not in the list.
INSERT INTO round (round_id, year, round_type) VALUES (9999, 2023, 'heat');
