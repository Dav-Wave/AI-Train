"""
MCP Server — Brief Generator Tool — Session 3
----------------------------------------------
Wraps agent.py (Gemini-powered) as a Model Context Protocol tool.
Any MCP host (Claude Desktop, Cursor) can call generate_brief as a named tool.

Transport: stdio

Setup — edit Claude Desktop config:
    {
      "mcpServers": {
        "brief-generator": {
          "command": "python",
          "args": ["/YOUR/ABSOLUTE/PATH/HERE/mcp_server.py"],
          "env": { "GEMINI_API_KEY": "AIza..." }
        }
      }
    }
Restart Claude Desktop. Ask: "generate a brief for this feedback: [paste]"
"""

import asyncio
import json
import sys
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import generate_brief

app = Server("brief-generator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="generate_brief",
            description=(
                "Takes a Slack thread, customer feedback, meeting notes, or any "
                "unstructured product feedback and returns a structured PM brief as JSON. "
                "Use when given raw or messy stakeholder input that needs to be distilled "
                "into a clear problem statement, affected users, success metrics, and a "
                "key assumption to validate. Does NOT suggest solutions or roadmap items."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "raw_input": {
                        "type": "string",
                        "description": "Raw feedback text — Slack thread, notes, complaints, etc.",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional: product area, team, or relevant background.",
                    },
                },
                "required": ["raw_input"],
            },
        ),
        Tool(
            name="run_evals",
            description=(
                "Runs the golden eval suite against the current prompt. "
                "Use after any prompt change to confirm quality hasn't degraded."
            ),
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "generate_brief":
        raw_input = arguments.get("raw_input", "")
        context   = arguments.get("context", "")
        if not raw_input:
            return [TextContent(type="text", text=json.dumps({"error": "raw_input is required"}))]
        try:
            result = generate_brief(raw_input, context=context)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    elif name == "run_evals":
        try:
            eval_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "evals", "golden.json")
            with open(eval_path) as f:
                cases = json.load(f)
            results = []
            passed = 0
            for case in cases:
                try:
                    output = generate_brief(case["input"])
                    required = ["problem", "affected", "metrics", "assumption"]
                    ok = all(output.get(k) for k in required) and len(output.get("metrics", [])) >= 2
                    results.append({"id": case["id"], "pass": ok})
                    if ok:
                        passed += 1
                except Exception as e:
                    results.append({"id": case["id"], "pass": False, "error": str(e)})
            summary = {"total": len(cases), "passed": passed, "score": f"{passed}/{len(cases)}", "results": results}
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        except FileNotFoundError:
            return [TextContent(type="text", text=json.dumps({"error": "evals/golden.json not found"}))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


if __name__ == "__main__":
    asyncio.run(stdio_server(app))
