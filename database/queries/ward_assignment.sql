-- Assign complaints to wards using PostGIS point-in-polygon.
SELECT c.complaint_id, w.ward_number
FROM complaints c
JOIN wards w
  ON ST_Contains(
       w.geom,
       ST_SetSRID(ST_MakePoint(c.longitude, c.latitude), 4326)
     );
