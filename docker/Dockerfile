# dbt runner image: pinned base and dependencies, non-root user, project baked in.
FROM python:3.12-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DBT_PROFILES_DIR=/app/dbt \
    DBT_TARGET_PATH=/tmp/target \
    DBT_LOG_PATH=/tmp/logs \
    DBT_SEND_ANONYMOUS_USAGE_STATS=false

COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
    && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin dbt

WORKDIR /app/dbt
COPY --chown=10001:10001 dbt/ /app/dbt/

USER 10001
ENTRYPOINT ["dbt"]
CMD ["build"]
