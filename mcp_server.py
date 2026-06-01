"""
MCP Server — Brief Generator Tool — Session 3
----------------------------------------------
Wraps agent.py as a Model Context Protocol (MCP) tool.
Once connected, any MCP host (Claude Desktop, Cursor, etc.)
can call `generate_brief` as a named tool.

Transport: stdio (host manages the process lifecycle)

Setup:
    1. Add to Claude Desktop config (see README for path):
       {
         "mcpServers": {
           "brief-generator": {
             "command": "python",
             "args": ["/YOUR/ABSOLUTE/PATH/HERE/mcp_server.py"],
             "env": { "ANTHROPIC_API_KEY": "sk-ant-..." }
           }
         }
       }
    2. Restart Claude Desktop
    3. Ask Claude: "generate a brief for this feedback: [paste text]"
"""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import session 2 agent (same directory)
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from agent import generate_brief

app = Server("brief-generator")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    Declare the tools this server exposes.
    The description is what Claude reads to decide WHEN to call this tool.
    Write it like a prompt — be specific about input type and output structure.
    """
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
                        "description": "The raw feedback text — Slack thread, notes, complaints, etc.",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional: product area, team, or any relevant background that helps frame the brief.",
                    },
                },
                "required": ["raw_input"],
            },
        ),
        Tool(
            name="run_evals",
            description=(
                "Runs the golden eval suite against the current prompt version. "
                "Use when you want to check if a prompt change degraded output quality. "
                "Returns pass/fail per test case and an overall score."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to the right implementation."""
    
    if name == "generate_brief":
        raw_input = arguments.get("raw_input", "")
        context = arguments.get("context", "")
        
        if not raw_input:
            return [TextContent(type="text", text=json.dumps({"error": "raw_input is required"}))]
        
        try:
            result = generate_brief(raw_input, context=context)
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    elif name == "run_evals":
        try:
            import os
            eval_path = os.path.join(os.path.dirname(__file__), "evals", "golden.json")
            with open(eval_path) as f:
                cases = json.load(f)
            
            results = []
            passed = 0
            for case in cases:
                try:
                    output = generate_brief(case["input"])
                    # Check required keys are present and non-null
                    required = ["problem", "affected", "metrics", "assumption"]
                    ok = all(output.get(k) for k in required)
                    ok = ok and len(output.get("metrics", [])) >= 2
                    results.append({"id": case["id"], "pass": ok, "output": output})
                    if ok:
                        passed += 1
                except Exception as e:
                    results.append({"id": case["id"], "pass": False, "error": str(e)})
            
            summary = {"total": len(cases), "passed": passed, "score": f"{passed}/{len(cases)}", "results": results}
            return [TextContent(type="text", text=json.dumps(summary, indent=2))]
        except FileNotFoundError:
            return [TextContent(type="text", text=json.dumps({"error": "evals/golden.json not found — see README"}))]
    
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


if __name__ == "__main__":
    asyncio.run(stdio_server(app))
