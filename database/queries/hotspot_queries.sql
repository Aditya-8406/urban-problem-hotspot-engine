-- Hotspot query placeholders.
SELECT ward_number, category, COUNT(*) AS complaints
FROM complaints
GROUP BY ward_number, category
ORDER BY complaints DESC;
