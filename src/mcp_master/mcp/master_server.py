import asyncio
import logging
from fastmcp import FastMCP
from mcp.server import Server
from starlette.requests import Request
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route
import os
import sys

module_paths = ["./", "../orchestration"]
file_path = os.path.dirname(__file__)
os.chdir(file_path)

for module_path in module_paths:
    full_path = os.path.normpath(os.path.join(file_path, module_path))
    sys.path.append(full_path)

from master_server_client import MasterServerClient
from orchestration import Orchestration
from agents import set_agent_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Initialize FastMCP server
class MasterMCPServer:
    def __init__(self, port: int = 3000, sub_servers: list[tuple] = []):
        # FastMCP server
        self.app = FastMCP("master_server")

        # Client to access sub-MCP servers
        self.master_server_client = None

        # Hosting port for the master server
        self.port = port

        # ("url", "servername") pairs to connect to servers with
        self.sub_servers = sub_servers

        # Initialize orchestration graph
        self.orch = Orchestration()

        @self.app.tool()
        async def access_sub_mcp(query: str):
            logging.info(f'Collecting tool information for query: {query}')

            set_agent_config({
                "tools": self.master_server_client.available_tools_flattened,
                "master_server_client": self.master_server_client
            })

            result = await self.orch.graph.ainvoke(
                {"question": query},
                {"recursion_limit": 30},
            )
            logging.info(f'Orchestration result: {result}')

            return result.get('external_data')

    def create_starlette_app(self, mcp_server: Server, *, debug: bool = False) -> Starlette:
        """Create a Starlette application that can serve the provided mcp server with SSE."""
        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request) -> None:
            async with sse.connect_sse(
                    request.scope,
                    request.receive,
                    request._send,
            ) as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )

        return Starlette(
            debug=debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

    # Server-server communications
    async def initialize_interserver_comms(self):
        self.master_server_client = MasterServerClient(self.app)

        try:
            for server in self.sub_servers:
                await self.master_server_client.connect_to_server(*server)

            await self.master_server_client.server_loop()
        finally:
            await self.master_server_client.cleanup()
            pass

    async def run_app(self):
        await self.app.run_async(transport="streamable-http", host="0.0.0.0", port=self.port)

    async def startup(self):
        await asyncio.gather(self.initialize_interserver_comms(), self.run_app())


if __name__ == "__main__":
    server = MasterMCPServer(3000, [
        ("http://localhost:8091/mcp", 'test_server_1'),
        ("http://localhost:8092/mcp", 'test_server_2')
    ])
    asyncio.run(server.startup())
