import asyncio
import logging
from fastmcp import FastMCP, Context
from mcp.server import Server
from starlette.requests import Request
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

from .master_server_client import MasterServerClient
from mcp_master.orchestration import Orchestration
from mcp_master.orchestration.agents import config as agent_config
from mcp_master.orchestration.agent_protocol import MultiAgentState

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
        self.port: int = port

        # ("url", "servername") pairs to connect to servers with
        self.sub_servers = sub_servers

        # Initialize orchestration graph
        self.orch = Orchestration()

        # Initialize request-response memory
        self.memory: dict[int] = {}

        @self.app.tool()
        async def access_sub_mcp(query: str, ctx: Context | None = None):
            # Get session ID of client session using built-in id()
            session_id = None
            if ctx is not None:
                session_id = id(ctx)

            logging.info(f'Collecting tool information from session ID {session_id} for query: {query}')

            # Prepare orchestration invoke config
            agent_config.tools = self.master_server_client.available_tools_flattened
            agent_config.master_server_client = self.master_server_client

            # Invoke orchestration to pick tools
            result = await self.orch.graph.ainvoke(
                {"question": query, 'session_memory': self.memory.get(session_id, [])},
                {"recursion_limit": 30},
            )
            logging.info(f'Orchestration result: {result}')

            # Retrieve tool responses and store to memory
            answer = result.get('external_data')

            if session_id is not None:
                self.store_request_to_memory(session_id, result)

            return answer

    def store_request_to_memory(self, session_id: int, result: MultiAgentState):
        if session_id not in self.memory:
            self.memory[session_id] = []

        self.memory[session_id].extend([
            {"role": "user", "content": result.get('question')},
            {"role": "assistant", "content": result.get('external_data')},
        ])

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
        except KeyboardInterrupt:
            pass
        finally:
            await self.master_server_client.cleanup()
            pass

    async def run_app(self):
        try:
            await self.app.run_async(transport="streamable-http", host="0.0.0.0", port=self.port)
        except KeyboardInterrupt:
            pass

    async def _startup(self):
        await asyncio.gather(self.initialize_interserver_comms(), self.run_app())

    def startup(self):
        try:
            asyncio.run(self._startup())
        except KeyboardInterrupt:
            pass
        finally:
            logging.info('Master MCP server successfully shut down.')


if __name__ == "__main__":
    server = MasterMCPServer(
        port=3000,
        sub_servers=[
            ("http://localhost:8091/mcp", 'test_server_1'),
            ("http://localhost:8092/mcp", 'test_server_2')
        ]
    )
    asyncio.run(server.startup())
