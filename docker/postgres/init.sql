-- Initialize PostGIS and pgvector extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a function to generate UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a function to calculate distance between two points
CREATE OR REPLACE FUNCTION calculate_distance(
    lat1 DOUBLE PRECISION,
    lon1 DOUBLE PRECISION,
    lat2 DOUBLE PRECISION,
    lon2 DOUBLE PRECISION
) RETURNS DOUBLE PRECISION AS $$
BEGIN
    RETURN ST_Distance(
        ST_GeogFromText('POINT(' || lon1 || ' ' || lat1 || ')'),
        ST_GeogFromText('POINT(' || lon2 || ' ' || lat2 || ')')
    );
END;
$$ LANGUAGE plpgsql;

-- Create a function to find psychologists within radius
CREATE OR REPLACE FUNCTION find_psychologists_within_radius(
    user_lat DOUBLE PRECISION,
    user_lon DOUBLE PRECISION,
    radius_meters DOUBLE PRECISION
) RETURNS TABLE(
    id INTEGER,
    distance_meters DOUBLE PRECISION
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        ST_Distance(
            ST_GeogFromText('POINT(' || user_lon || ' ' || user_lat || ')'),
            p.location
        ) as distance_meters
    FROM catalogue_psychologist p
    WHERE ST_DWithin(
        ST_GeogFromText('POINT(' || user_lon || ' ' || user_lat || ')'),
        p.location,
        radius_meters
    )
    ORDER BY distance_meters;
END;
$$ LANGUAGE plpgsql;

-- Create indexes for better performance
-- These will be created by Django migrations, but we can add some here too
-- CREATE INDEX IF NOT EXISTS idx_psychologist_location ON catalogue_psychologist USING GIST (location);
-- CREATE INDEX IF NOT EXISTS idx_psychologist_embedding ON catalogue_psychologist USING hnsw (embedding vector_cosine_ops);

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE referwell TO referwell;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO referwell;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO referwell;
