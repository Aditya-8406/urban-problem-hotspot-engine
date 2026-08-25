-- Initial database schema placeholder.
-- PostGIS should be enabled in the production database.

CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS wards (
    id SERIAL PRIMARY KEY,
    ward_number INTEGER UNIQUE NOT NULL,
    name TEXT,
    geom geometry(MultiPolygon, 4326)
);

CREATE TABLE IF NOT EXISTS complaints (
    id BIGSERIAL PRIMARY KEY,
    complaint_id TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    complaint_date TIMESTAMP,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    geom geometry(Point, 4326),
    ward_number INTEGER,
    severity INTEGER,
    status TEXT,
    resolution_date TIMESTAMP,
    data_type TEXT,
    source TEXT
);
