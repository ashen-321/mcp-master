import argparse
import asyncio
import os

from mcp_client import MCPClient


async def main():
    """Main function to run the MCP client"""
    parser = argparse.ArgumentParser(description="Run MCP Streamable http based Client")
    parser.add_argument("--mcp-localhost-port", type=int, default=3000, help="Localhost port to bind to")
    args = parser.parse_args()

    client = MCPClient()

    try:
        await client.connect_to_streamable_http_server(f"http://localhost:{args.mcp_localhost_port}/mcp")
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
