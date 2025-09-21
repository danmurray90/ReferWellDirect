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

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE referwell TO referwell;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO referwell;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO referwell;
