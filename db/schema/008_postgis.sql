CREATE EXTENSION IF NOT EXISTS postgis;

ALTER TABLE stop ADD COLUMN location geography(POINT);
UPDATE stop SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);
ALTER TABLE stop DROP COLUMN latitude;
ALTER TABLE stop DROP COLUMN longitude;

ALTER TABLE vehicle ADD COLUMN location geography(POINT);
UPDATE vehicle SET location = ST_SetSRID(ST_MakePoint(longitude, latitude), 4326);
ALTER TABLE vehicle DROP COLUMN latitude;
ALTER TABLE vehicle DROP COLUMN longitude;
