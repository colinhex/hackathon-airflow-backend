#!/bin/bash

# Function to display a loading spinner
spinner() {
    local pid=$1
    local delay=0.1
    # shellcheck disable=SC1003
    local spin_str='|/-\'
    while ps a | awk '{print $1}' | grep -q "$pid"; do
        local temp=${spin_str#?}
        printf " [%c]  " "$spin_str"
        local spin_str=$temp${spin_str%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Function to center text with a specified padding character
center_text() {
    local text="$1"
    local padding_char="$2"
    local width=$(tput cols)
    local text_length=${#text}
    local padding=$(( (width - text_length) / 2 - 2 ))
    echo ""
    printf '%*s%s%*s\n' "$padding" ' ' "$text" "$padding" ' ' | tr ' ' "$padding_char"
    echo ""
}

center_text "Running Setup Script" "="

echo "Executing Unit Test Script"
./run_tests.sh
EXIT_CODE=$?
if [ "$EXIT_CODE" = "126" ]; then
    echo "- Couldn't run the tests because the run_tests.sh script is not executable."
    echo "- Please run \"chmod +x run_tests.sh\" to make the script executable."
    exit 1
fi
if [ "$EXIT_CODE" -ne "0" ]; then
    echo "- Tests failed. Exiting setup."
    echo "- Make sure the tests pass before continuing."
    exit 1
fi

center_text "Preparing Docker Deployment" "="

echo "Checking if Docker is running..."
if ! docker info > /dev/null 2>&1; then
    echo "- Docker is not running. Please start Docker and try again."
    exit 1
else
    echo "- Docker is running."
fi

echo "Stopping and removing existing containers..."
docker-compose down
echo "Sourcing environment variables..."
source .env
echo "Verifying postgres environment variables exist..."
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
  echo "- Required environment variables POSTGRES_USER, POSTGRES_PASSWORD, or POSTGRES_DB are not set."
  echo "- Make sure they are set."
  exit 1
fi

echo "Creating database initialization file from postgres environment variables... (initdb.sql)"
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
center_text "Running Docker Composer" "="
docker-compose up -d
echo "Waiting for applications to start... (This may take a while on first run. Subsequent runs will be faster.)"
until curl --output /dev/null --silent --head --fail http://localhost:8080; do
    sleep 3 &
    spinner $!
done
until curl --output /dev/null --silent --head --fail http://localhost:8080; do
    sleep 3 &
    spinner $!
done
echo "Connected to airflow webserver instance successfully!"
echo "Creating administrative user..."

docker-compose exec airflow-webserver airflow users create \
    --username "$AIRFLOW_WEBSERVER_USER_NAME" \
    --firstname "$AIRFLOW_WEBSERVER_USER_FIRST_NAME" \
    --lastname "$AIRFLOW_WEBSERVER_USER_LAST_NAME" \
    --role "$AIRFLOW_WEBSERVER_USER_ROLE" \
    --email "$AIRFLOW_WEBSERVER_USER_EMAIL" \
    --password "$AIRFLOW_WEBSERVER_USER_PASSWORD"

center_text "Setup Complete" "="
echo "Setup complete. Airflow is running in Docker. Visit http://localhost:8080 to access the Airflow webserver."
echo "Login with username = $AIRFLOW_WEBSERVER_USER_NAME | password = $AIRFLOW_WEBSERVER_USER_PASSWORD"

