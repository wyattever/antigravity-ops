# ANTIGRAVITY | CLOUD RUN SENTINEL (LiteLLM Gateway)
# v1.0 | 2026-03-13
FROM python:3.12-slim

WORKDIR /app

# Install LiteLLM and Production Server
RUN pip install litellm[proxy] uvicorn

# Copy the migration backup from M4
COPY acp_db_backup.sql /app/

# Environment Defaults
ENV HOST=0.0.0.0
ENV PORT=8080

# The Forge will inject these from Secret Manager
# ENV AWS_ACCESS_KEY_ID=...
# ENV AWS_SECRET_ACCESS_KEY=...

EXPOSE 8080

# Start the Gateway
CMD ["litellm", "--port", "8080"]
