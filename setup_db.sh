#!/bin/bash

DB_NAME="hw"
DB_USER="ligence"
DB_PASS="pass"

echo "Creating database and user in PostgreSQL..."

sudo -u postgres psql <<EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Set owner
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;

-- Ensure schema permissions
\c $DB_NAME
GRANT USAGE, CREATE ON SCHEMA public TO $DB_USER;
ALTER SCHEMA public OWNER TO $DB_USER;
EOF

echo "PostgreSQL setup complete."
