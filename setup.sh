#!/bin/bash

docker-compose down

source .env

if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
  echo "Required environment variables POSTGRES_USER, POSTGRES_PASSWORD, or POSTGRES_DB are not set."
  exit 1
fi

SQL_FILE="./initdb.sql"

cat <<EOF > $SQL_FILE
-- Check if the database exists, create if not
DO
\$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB') THEN
      EXECUTE 'CREATE DATABASE $POSTGRES_DB';
   END IF;
END
\$\$;

-- Check if the user exists, create if not
DO
\$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$POSTGRES_USER') THEN
      EXECUTE 'CREATE USER $POSTGRES_USER WITH PASSWORD ''$POSTGRES_PASSWORD''';
   END IF;
END
\$\$;

-- Grant privileges if the database and user exist
DO
\$\$
BEGIN
   IF EXISTS (SELECT FROM pg_database WHERE datname = '$POSTGRES_DB') AND
      EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = '$POSTGRES_USER') THEN
      EXECUTE 'GRANT ALL ON DATABASE $POSTGRES_DB TO $POSTGRES_USER';
   END IF;
END
\$\$;
EOF

echo "Database initialization file created."

echo "Composing docker containers..."
docker-compose up -d
echo "Waiting for containers...";
until curl --output /dev/null --silent --head --fail http://localhost:8080; do
    printf '.'
    sleep 3
done
printf '\n'
echo "Connected to webserver successfully."
echo "Creating administrator user..."

docker-compose exec airflow-webserver airflow users create \
    --username "$AIRFLOW_WEBSERVER_USER_NAME" \
    --firstname "$AIRFLOW_WEBSERVER_USER_FIRST_NAME" \
    --lastname "$AIRFLOW_WEBSERVER_USER_LAST_NAME" \
    --role "$AIRFLOW_WEBSERVER_USER_ROLE" \
    --email "$AIRFLOW_WEBSERVER_USER_EMAIL" \
    --password "$AIRFLOW_WEBSERVER_USER_PASSWORD"

echo "Login on http://localhost:8080 user=$AIRFLOW_WEBSERVER_USER_NAME password=$AIRFLOW_WEBSERVER_USER_PASSWORD"
echo "Done."