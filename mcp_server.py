"""Optional stdio MCP adapter. All CAD calls run serially on this thread."""
import asyncio, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from runtime import Runtime
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

async def main():
    runtime = Runtime()
    server = Server('sw-codex-share')
    @server.list_tools()
    async def list_tools():
        return list(runtime.tools.values())
    @server.call_tool()
    async def call_tool(name, arguments):
        return [TextContent(type='text', text=json.dumps(runtime.call(name, arguments),ensure_ascii=False))]
    async with stdio_server() as (reader, writer):
        await server.run(reader, writer, server.create_initialization_options())

if __name__ == '__main__':
    asyncio.run(main())
