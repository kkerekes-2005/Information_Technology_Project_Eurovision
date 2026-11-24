-- First and last contest year, for the limits of the year sliders of the app.
SELECT MIN(year) AS first_year, MAX(year) AS last_year
FROM contest;
