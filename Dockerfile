FROM apache/airflow:2.10.0-python3.12
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
COPY requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==2.10.0" -r /requirements.txt

# Copy the entrypoint script
COPY --chmod=0755 entrypoint.sh /entrypoint.sh

# Use the entrypoint script as the default command
ENTRYPOINT ["/entrypoint.sh"]
