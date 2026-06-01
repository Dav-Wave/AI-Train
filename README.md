# PM AI Workshop — Brief Generator

Build arc for the *AI for Lead Product Managers* workshop.  
One repo. Everything you need.

---

## What you'll build

A **PM Brief Generator** that:
1. Takes raw feedback (Slack thread, meeting notes, complaints)
2. Returns a structured brief as JSON (problem, metrics, assumption)
3. Is callable as a named MCP tool from Claude Desktop / Cursor
4. Is wired into an n8n automation: Slack → agent → Notion page + Slack reply

---

## Repo structure

```
pm-ai-workshop/
├── agent.py          ← Session 2: core agent
├── agent_http.py     ← Session 4: HTTP wrapper for n8n
├── mcp_server.py     ← Session 3: MCP server wrapping agent.py
├── .env.example      ← copy to .env, add your API key
├── requirements.txt
├── n8n/
│   └── workflow.json ← Session 4: import into n8n Cloud
├── evals/
│   └── golden.json   ← Session 5: 5 test cases for your eval suite
└── README.md
```

---

## Setup (do this before Session 2)

```bash
# 1. Clone
git clone https://github.com/[YOUR-HANDLE]/pm-ai-workshop
cd pm-ai-workshop

# 2. Install
pip install -r requirements.txt

# 3. Add your API key
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY=sk-ant-...

# 4. Test
python agent.py
# Should print a JSON brief for the demo input
```

Get your API key at: https://console.anthropic.com

---

## Session 2 — Run the agent

```bash
# Demo input (built-in)
python agent.py

# Your own input inline
python agent.py --input "Users are dropping off at step 3 of onboarding"

# From a file
python agent.py --file my_feedback.txt

# With context
python agent.py --input "3 enterprise accounts complaining about SSO" --context "product area: auth, team: enterprise"
```

**Output format:**
```json
{
  "problem": "Enterprise admins cannot complete SSO setup without engineering support, blocking adoption.",
  "affected": "Enterprise admins (50+ seat accounts) spend 3–5 hours on setup vs. promised 30 min.",
  "metrics": [
    "SSO setup completion rate increases from ~40% to >85% within 30 days of launch",
    "Support tickets tagged 'SSO setup' decrease by 60% within 60 days"
  ],
  "assumption": "The blocker is UX complexity, not a missing technical capability in the product.",
  "confidence": "medium",
  "missing_context": "Whether SSO failures are tracked in product analytics vs. just support tickets"
}
```

---

## Session 3 — Connect as MCP tool

### Claude Desktop config

Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`  
(Windows: `%APPDATA%\Claude\claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "brief-generator": {
      "command": "python",
      "args": ["/YOUR/ABSOLUTE/PATH/HERE/mcp_server.py"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

**⚠ Important:**
- Use **absolute paths** — relative paths silently fail
- **Restart Claude Desktop** after every config edit
- Test by asking Claude: *"generate a brief for this feedback: [paste text]"*

### Available tools

Once connected, Claude Desktop has access to:
- `generate_brief` — generate a PM brief from raw feedback
- `run_evals` — run golden eval suite against the current prompt

### Cursor setup

In Cursor: `Ctrl+Shift+P` → *MCP: Add Server* → paste the server config above.

---

## Session 4 — n8n automation

### Import the workflow

1. Go to [app.n8n.cloud](https://app.n8n.cloud) → New workflow
2. Three-dot menu → Import from JSON → select `n8n/workflow.json`
3. Set credentials (Slack, Notion, HTTP)

### Run the agent as an HTTP server (for n8n to call)

```bash
# Terminal 1 — start the agent HTTP server
python agent_http.py
# Runs on http://localhost:8080

# Terminal 2 — expose it publicly for n8n Cloud to reach
npx ngrok http 8080
# Gives you https://xxxxx.ngrok.app — use this as the n8n HTTP Request URL
```

### Health check

```bash
curl http://localhost:8080/health
# {"status": "ok"}

curl -X POST http://localhost:8080/brief \
  -H "Content-Type: application/json" \
  -d '{"raw_input": "users drop off at step 3"}'
```

### Deploy to production (post-workshop)

- **Render.com**: Connect repo, set ANTHROPIC_API_KEY env var, deploy as web service
- **Railway.app**: `railway up` — ~$5/mo
- **Fly.io**: `fly launch` — free tier available

---

## Session 5 — Evals

### Run the eval suite

The MCP server exposes a `run_evals` tool. Ask Claude Desktop:

*"run evals"*

Or run directly:

```python
import json
from agent import generate_brief

with open("evals/golden.json") as f:
    cases = json.load(f)

for case in cases:
    result = generate_brief(case["input"])
    required = ["problem", "affected", "metrics", "assumption"]
    ok = all(result.get(k) for k in required) and len(result.get("metrics", [])) >= 2
    print(f"{'✓' if ok else '✗'} {case['id']}")
```

### Add your own test cases

Edit `evals/golden.json`. Each case needs:
```json
{
  "id": "unique-slug",
  "description": "What this case tests",
  "input": "The raw feedback text",
  "must_contain": ["problem", "affected", "metrics", "assumption"],
  "notes": "What the output should and shouldn't include"
}
```

---

## Prompt versioning

The system prompt is in `agent.py` as `SYSTEM_PROMPT` with a version comment.  
**Treat prompt changes like code changes** — PR, review, changelog entry.

Changelog format:
```
v1.0 — initial build (workshop day)
v1.1 — added confidence field after eval regression on low-quality inputs
v1.2 — tightened assumption constraint after stakeholder review
```

---

## Extending the agent

Ideas for post-workshop iteration:

- Add a `stakeholder_to_involve` field to the brief schema
- Add a `priority_score` field (impact × confidence)
- Chain a second agent call that drafts Jira ticket titles from the brief
- Add a RAG layer that pulls relevant past decisions from Notion before generating
- Add a human-in-the-loop node in n8n that requires PM approval before posting to Notion

---

## Links

| Resource | URL |
|----------|-----|
| Claude API docs | https://docs.anthropic.com |
| MCP spec | https://modelcontextprotocol.io |
| n8n Cloud | https://app.n8n.cloud |
| Braintrust (evals) | https://braintrust.dev |
| Helicone (observability) | https://helicone.ai |
| PromptLayer | https://promptlayer.com |

---

## Questions?

Open an issue on this repo or email [your-email].
