FROM apache/airflow:3.0.0

# Switch to root temporarily to install system deps if needed
USER root

# Install any OS-level deps (e.g. for pyspark, java if needed later)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    libsasl2-dev \
    libffi-dev \
    libssl-dev \
    && apt-get autoremove -yqq --purge \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Copy and install python deps
COPY requirements-airflow.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Optional: pre-create known dirs (helps with permissions)
RUN mkdir -p /opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins
