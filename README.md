# PM AI Workshop — Brief Generator

Build arc for the *AI for Lead Product Managers* workshop.  
**100% free API** — powered by Groq + Llama 3.3 70B. No credit card. No quota issues.

---

## Get your free API key (2 minutes)

1. Go to **https://console.groq.com**
2. Sign up with your Google account (one click)
3. Click **"API Keys"** in the left sidebar
4. Click **"Create API key"** → copy it

Key starts with `gsk_` and never expires. Free tier: 30 requests/minute, 14,400/day.

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
├── agent.py          ← Session 2: core agent (Groq / Llama 3.3 70B)
├── agent_http.py     ← Session 4: HTTP wrapper for n8n
├── mcp_server.py     ← Session 3: MCP server wrapping agent.py
├── .env.example      ← copy to .env, add your Groq key
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

# 2. Install  (requires Python 3.10+)
pip3 install -r requirements.txt

# 3. Add your Groq API key
cp .env.example .env
# Open .env in any editor — paste your key:
# GROQ_API_KEY=gsk_your-key-here

# 4. Test
python3 agent.py
# Should print a JSON brief for the demo input
```

**Check your Python version first:**
```bash
python3 --version   # needs to say 3.10 or higher
```
If lower: download Python 3.12 from **python.org/downloads**

---

## Session 2 — Run the agent

```bash
# Demo input (built-in — no arguments needed)
python3 agent.py

# Your own input
python3 agent.py --input "Users are dropping off at step 3 of onboarding"

# From a file
python3 agent.py --file my_feedback.txt

# With context
python3 agent.py --input "3 enterprise accounts complaining about SSO" \
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
      "command": "python3",
      "args": ["/YOUR/ABSOLUTE/PATH/HERE/mcp_server.py"],
      "env": {
        "GROQ_API_KEY": "gsk_your-key-here"
      }
    }
  }
}
```

**⚠ Important:**
- Use **absolute paths** — relative paths silently fail
- **Restart Claude Desktop** after every config edit
- Test: ask Claude *"generate a brief for this feedback: [paste text]"*

---

## Session 4 — n8n automation

### Import the workflow

1. Go to **app.n8n.cloud** → New workflow
2. Three-dot menu → Import from JSON → select `n8n/workflow.json`
3. Set credentials: Slack, Notion, HTTP endpoint (your agent URL)

### Run the agent as an HTTP server

```bash
# Terminal 1 — start agent HTTP server
python3 agent_http.py
# Runs on http://localhost:8080

# Terminal 2 — expose it to n8n Cloud
npx ngrok http 8080
# Gives you https://xxxxx.ngrok.app — paste into n8n HTTP Request node
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
python3 -c "
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

---

## Groq free tier limits

| Model | Requests/minute | Requests/day | Tokens/minute |
|-------|----------------|--------------|---------------|
| Llama 3.3 70B | 30 | 14,400 | 6,000 |

A class of 20 people running ~50 requests each = 1,000 requests. Well within limits.

---

## Troubleshooting

**`GROQ_API_KEY not found`**  
→ Check `.env` exists (not just `.env.example`) with no quotes around the value:  
→ Correct: `GROQ_API_KEY=gsk_abc123`  
→ Wrong: `GROQ_API_KEY="gsk_abc123"`

**`python3: command not found`**  
→ Install Python 3.12 from python.org/downloads

**`pip3: command not found`**  
→ Try: `python3 -m pip install -r requirements.txt`

**MCP tool not appearing in Claude Desktop**  
→ Use absolute path in config, restart Claude Desktop fully

**n8n can't reach agent**  
→ Confirm ngrok is running, URL in n8n matches ngrok output exactly

---

## Links

| Resource | URL |
|----------|-----|
| Get Groq API key (free) | https://console.groq.com |
| Groq docs | https://console.groq.com/docs |
| MCP spec | https://modelcontextprotocol.io |
| Claude Desktop | https://claude.ai/download |
| n8n Cloud | https://app.n8n.cloud |
| Braintrust (evals) | https://braintrust.dev |

---

Questions? Open an issue on this repo.
