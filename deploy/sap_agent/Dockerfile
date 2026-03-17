FROM python:3.11-slim

# Install Java JRE (required for BigTable emulator), netcat, and gcloud CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre-headless \
    netcat-openbsd \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    && echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
       > /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
       | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update && apt-get install -y --no-install-recommends google-cloud-cli \
    && apt-get install -y --no-install-recommends google-cloud-cli-bigtable-emulator \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN adduser --disabled-password --gecos "" myuser

USER myuser
WORKDIR /home/myuser

ENV PATH="/home/myuser/.local/bin:$PATH"
ENV HOME="/home/myuser"

# Install Python dependencies
COPY --chown=myuser:myuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent source into ADK package structure
COPY --chown=myuser:myuser agent.py sap_tools.py bigtable_client.py .env agent.json __init__.py ./agents/sap_agent/

# Copy data loader and data (outside agent package, used at startup)
COPY --chown=myuser:myuser load_bigtable.py .
COPY --chown=myuser:myuser data/ ./data/

# Copy and set up entrypoint
COPY --chown=myuser:myuser entrypoint.sh .
RUN chmod +x entrypoint.sh

ENV PORT=8080
EXPOSE 8080

ENTRYPOINT ["./entrypoint.sh"]
