# Always-on hosting for FirstResponder

FirstResponder is a **Socket Mode** Bolt app whose agent drives the `claude`
CLI as a subprocess. It needs a **long-running process on a real Linux host** —
not serverless (Vercel) and not Slack's Deno hosted platform. This deploys the
`Dockerfile` at the repo root to a small always-on VM so the sandbox stays live
for judges (judging window: Jul 14 – Aug 6).

No inbound ports are required (Socket Mode is outbound only), so there are no
firewall rules to open.

## Secrets the container needs (env, never baked into the image)
- `ANTHROPIC_API_KEY`
- `SLACK_BOT_TOKEN` (xoxb-)
- `SLACK_APP_TOKEN` (xapp-)
- `SLACK_USER_TOKEN` (xoxp-, optional — enables the RTS SITREP path)

---

## Option A — GCP Compute Engine `e2-micro` (recommended, free tier)

Builds with Cloud Build (no local Docker needed) and runs on an always-free
`e2-micro` VM in `us-central1`.

```bash
# 0) point at your project + enable APIs (one time)
gcloud config set project YOUR_PROJECT_ID
gcloud services enable artifactregistry.googleapis.com cloudbuild.googleapis.com compute.googleapis.com

# 1) create a Docker registry
gcloud artifacts repositories create firstresponder \
  --repository-format=docker --location=us-central1

# 2) build + push the image straight from source (Cloud Build)
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/firstresponder/app:latest

# 3) create the always-free e2-micro VM running the container, secrets as env
gcloud compute instances create-with-container firstresponder \
  --zone=us-central1-a \
  --machine-type=e2-micro \
  --container-image=us-central1-docker.pkg.dev/YOUR_PROJECT_ID/firstresponder/app:latest \
  --container-restart-policy=always \
  --container-env=^:^ANTHROPIC_API_KEY=sk-ant-...:SLACK_BOT_TOKEN=xoxb-...:SLACK_APP_TOKEN=xapp-...:SLACK_USER_TOKEN=xoxp-...
```

`--container-env=^:^k=v:k=v` sets `:` as the separator so token values
containing `,` don't break parsing.

**Verify it's live:**
```bash
gcloud compute ssh firstresponder --zone=us-central1-a \
  --command "docker logs \$(docker ps -q) 2>&1 | tail -20"
# look for: ⚡️ Bolt app is running!
```
Then DM the bot / run `/crisis help` in the sandbox — it should respond with no
laptop running.

**Redeploy after a code change:** re-run steps 2, then
`gcloud compute instances update-container firstresponder --zone=us-central1-a --container-image=...:latest`.

> Note: `e2-micro` has 1 GB RAM. It's fine for demo-level traffic; if agent runs
> OOM under load, bump to `--machine-type=e2-small` (2 GB, ~$13/mo).

---

## Option B — AWS Lightsail Container Service (simple, ~$7/mo)

```bash
# build + push needs local Docker; then:
aws lightsail create-container-service --service-name firstresponder --power nano --scale 1
aws lightsail push-container-image --service-name firstresponder --label app --image firstresponder:latest
# deploy with a containers.json that sets the 4 env vars, then:
aws lightsail create-container-service-deployment --service-name firstresponder --containers file://containers.json
```

A plain EC2 `t4g.micro` + `docker run --restart=always -e ... firstresponder`
works identically if you prefer a VM.

---

## Data note
The Jefferson seed knowledge base (`data/firstresponder.db`) is baked into the
image, so judges get the full demo data immediately. Incidents/uploads created
at runtime persist for the container's lifetime and rehydrate on restart; a
redeploy resets to the seed. To persist across redeploys, mount a volume at
`/app/data`.
