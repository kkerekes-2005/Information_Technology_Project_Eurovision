-- Countries that sent at least one entry, for the country menus of the app.
SELECT DISTINCT country.country_code, country.name
FROM country
JOIN song_entry ON song_entry.country_code = country.country_code
ORDER BY country.name;
