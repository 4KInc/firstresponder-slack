# FirstResponder — always-on Socket Mode host.
#
# The app is Python (Bolt, Socket Mode) and the Claude Agent SDK drives the
# `claude` CLI as a subprocess, so the image needs BOTH Python 3.12 and Node +
# the Claude Code CLI. This is why the app can't run on Slack's Deno hosted
# platform / serverless — it needs a long-running process with a subprocess.

FROM python:3.12-slim

# Node.js 20 (for the Claude Code CLI the Agent SDK spawns)
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && rm -rf /var/lib/apt/lists/*

# Claude Code CLI — the Agent SDK invokes this headlessly (ANTHROPIC_API_KEY set)
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# App source, incl. the seeded knowledge base (data/firstresponder.db — Jefferson)
COPY . .

# claude CLI writes its config under $HOME; keep it inside the writable workdir.
ENV HOME=/app \
    PYTHONUNBUFFERED=1

# Secrets (ANTHROPIC_API_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_USER_TOKEN)
# are provided at RUN time via env — never baked into the image.
CMD ["python", "app.py"]
