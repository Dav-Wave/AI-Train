# PM AI Workshop — Brief Generator

Build arc for the *AI for Lead Product Managers* workshop.  
**100% free API** — powered by Google Gemini. No credit card required.

---

## Get your free API key (2 minutes)

1. Go to **https://aistudio.google.com**
2. Sign in with your Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy it — you'll paste it into `.env` below

That's it. Free tier gives you 1,500 requests/day on Gemini 2.0 Flash. More than enough for this class.

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
├── agent.py          ← Session 2: core agent (Gemini-powered)
├── agent_http.py     ← Session 4: HTTP wrapper for n8n
├── mcp_server.py     ← Session 3: MCP server wrapping agent.py
├── .env.example      ← copy to .env, add your Gemini key
├── requirements.txt
├── n8n/
│   └── workflow.json ← Session 4: import into n8n Cloud
├── evals/
│   └── golden.json   ← Session 5: 5 test cases for your eval suite
└── README.md
```

---

## Setup

```bash
# 1. Clone
git clone https://github.com/[YOUR-HANDLE]/pm-ai-workshop
cd pm-ai-workshop

# 2. Install
pip install -r requirements.txt

# 3. Add your Gemini API key
cp .env.example .env
# Open .env in any editor — paste your key:
# GEMINI_API_KEY=AIza-your-key-here

# 4. Test
python agent.py
# Should print a JSON brief for the demo input
```

---

## Session 2 — Run the agent

```bash
# Demo input (built-in — no arguments needed)
python agent.py

# Your own input
python agent.py --input "Users are dropping off at step 3 of onboarding"

# From a file
python agent.py --file my_feedback.txt

# With context
python agent.py --input "3 enterprise accounts complaining about SSO" \
                --context "product area: auth, team: enterprise"
```

**Example output:**
```json
{
  "problem": "Enterprise admins cannot complete SSO setup without engineering support.",
  "affected": "Enterprise admins at 50+ seat accounts spend 3–5 hrs on setup vs. promised 30 min.",
  "metrics": [
    "SSO setup completion rate increases from ~40% to >85% within 30 days",
    "Support tickets tagged 'SSO setup' decrease by 60% within 60 days"
  ],
  "assumption": "The blocker is UX complexity, not a missing technical capability.",
  "confidence": "medium",
  "missing_context": "Whether SSO failures are tracked in analytics vs. only support tickets"
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
        "GEMINI_API_KEY": "AIza-your-key-here"
      }
    }
  }
}
```

**⚠ Important:**
- Use **absolute paths** — relative paths silently fail
- **Restart Claude Desktop** after every config edit
- Test: ask Claude *"generate a brief for this feedback: [paste text]"*

### Cursor setup

`Ctrl+Shift+P` → *MCP: Add Server* → paste the server config above.

---

## Session 4 — n8n automation

### Import the workflow

1. Go to **app.n8n.cloud** → New workflow
2. Three-dot menu → Import from JSON → select `n8n/workflow.json`
3. Set credentials: Slack, Notion, HTTP endpoint (your agent URL)

### Run the agent as an HTTP server

```bash
# Terminal 1 — start agent HTTP server
python agent_http.py
# Runs on http://localhost:8080

# Terminal 2 — expose it to n8n Cloud
npx ngrok http 8080
# Gives you https://xxxxx.ngrok.app — paste this into n8n HTTP Request node
```

### Test the HTTP server

```bash
# Health check
curl http://localhost:8080/health

# Generate a brief
curl -X POST http://localhost:8080/brief \
  -H "Content-Type: application/json" \
  -d '{"raw_input": "users drop off at step 3 of onboarding"}'
```

---

## Session 5 — Evals

```bash
python -c "
import json
from agent import generate_brief

with open('evals/golden.json') as f:
    cases = json.load(f)

for case in cases:
    result = generate_brief(case['input'])
    required = ['problem', 'affected', 'metrics', 'assumption']
    ok = all(result.get(k) for k in required) and len(result.get('metrics', [])) >= 2
    print(f\"{'PASS' if ok else 'FAIL'}  {case['id']}\")
"
```

Or ask Claude Desktop (with MCP connected): *"run evals"*

---

## Gemini free tier limits

| Model | Free requests/day | Free requests/min |
|-------|-------------------|-------------------|
| Gemini 2.0 Flash | 1,500 | 15 |
| Gemini 1.5 Flash | 1,500 | 15 |

For a class of 20 people running ~50 requests each = 1,000 requests. Well within limits.  
If you hit rate limits: the error message is clear, wait 1 minute, retry.

---

## Troubleshooting

**`GEMINI_API_KEY` not found**  
→ Check `.env` exists (not just `.env.example`) and key has no trailing spaces.

**`json.JSONDecodeError`**  
→ Gemini occasionally adds markdown fences. The code strips them, but if it persists, add `response_mime_type="application/json"` to `generation_config`.

**MCP tool not appearing in Claude Desktop**  
→ Check absolute path in config, restart Claude Desktop, check Python is in PATH.

**n8n can't reach agent**  
→ Confirm ngrok is running and the URL in n8n matches the ngrok output exactly.

---

## Links

| Resource | URL |
|----------|-----|
| Get Gemini API key (free) | https://aistudio.google.com |
| Gemini API docs | https://ai.google.dev/gemini-api/docs |
| MCP spec | https://modelcontextprotocol.io |
| n8n Cloud | https://app.n8n.cloud |
| Braintrust (evals) | https://braintrust.dev |
| Claude Desktop | https://claude.ai/download |

---

Questions? Open an issue on this repo.
