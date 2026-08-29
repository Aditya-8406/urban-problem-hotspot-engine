-- ============================================================
-- Urban Problem Hotspot Engine
-- PostGIS Spatial Database Foundation
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================
-- WARDS
-- ============================================================

CREATE TABLE IF NOT EXISTS wards (
    id SERIAL PRIMARY KEY,

    ward_number INTEGER NOT NULL UNIQUE,

    name TEXT,

    centroid geometry(Point, 4326),

    geom geometry(MultiPolygon, 4326) NOT NULL
);

-- Spatial index for ward boundary queries
CREATE INDEX IF NOT EXISTS idx_wards_geom
ON wards
USING GIST (geom);

-- ============================================================
-- COMPLAINTS
-- ============================================================

CREATE TABLE IF NOT EXISTS complaints (
    id BIGSERIAL PRIMARY KEY,

    complaint_id TEXT UNIQUE NOT NULL,

    category TEXT NOT NULL,

    description TEXT,

    complaint_date TIMESTAMP,

    latitude DOUBLE PRECISION,

    longitude DOUBLE PRECISION,

    -- Geographic point generated from latitude/longitude
    geom geometry(Point, 4326),

    -- Ward assigned using point-in-polygon
    ward_number INTEGER,

    severity INTEGER,

    status TEXT,

    resolution_date TIMESTAMP,

    data_type TEXT,

    source TEXT,

    source_url TEXT
);

-- Spatial index for complaint location queries
CREATE INDEX IF NOT EXISTS idx_complaints_geom
ON complaints
USING GIST (geom);

-- Index for ward-based analytics
CREATE INDEX IF NOT EXISTS idx_complaints_ward
ON complaints (ward_number);

-- Index for temporal analysis
CREATE INDEX IF NOT EXISTS idx_complaints_date
ON complaints (complaint_date);

-- ============================================================
-- WARD RELATIONSHIP
-- ============================================================

ALTER TABLE complaints
DROP CONSTRAINT IF EXISTS fk_complaint_ward;

ALTER TABLE complaints
ADD CONSTRAINT fk_complaint_ward
FOREIGN KEY (ward_number)
REFERENCES wards (ward_number);

-- ============================================================
-- VALIDATION
-- ============================================================

-- Complaints without coordinates are allowed during ingestion,
-- but they must not participate in spatial analysis.

-- Complaints with coordinates should have geometry generated using:
--
-- ST_SetSRID(
--     ST_MakePoint(longitude, latitude),
--     4326
-- )

-- Ward assignment should be performed using:
--
-- ST_Within(complaint.geom, ward.geom)
