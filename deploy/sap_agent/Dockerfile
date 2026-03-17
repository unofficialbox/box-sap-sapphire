FROM python:3.11-slim

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
COPY --chown=myuser:myuser agent.py sap_tools.py bigtable_client.py agent.json __init__.py ./agents/sap_agent/

ENV PORT=8080
EXPOSE 8080

CMD adk api_server --port=${PORT} --host=0.0.0.0 --a2a /home/myuser/agents
