#!/bin/bash
set -e
module=$1

if [ "$module" = "webserver" ]; then
  echo "Running DB migrations..."
  airflow db migrate
else
  echo "Waiting for migrations to complete..."
  sleep 30
fi

echo "Starting Airflow $module..."
exec airflow "$module"