import asyncio
import logging
from fastmcp import FastMCP

from .master_server_client import MasterServerClient, SubServer
from ..orchestration import Orchestration
from ..orchestration.agents import config as agent_config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Initialize FastMCP server
class MasterMCPServer:
    def __init__(self, port: int = 3000, sub_servers: list[SubServer] | None = None):
        if sub_servers is None:
            sub_servers = []

        # FastMCP server
        self.app = FastMCP("master_server")

        # Client to access sub-MCP servers
        self.master_server_client = None

        # Hosting port for the master server
        self.port: int = port

        # SubServer instances to connect to servers with
        self.sub_servers = sub_servers

        # Initialize orchestration graph
        self.orch = Orchestration()

        @self.app.tool()
        async def access_sub_mcp(query: str):
            logging.info(f'Collecting tool information for query: {query}')

            # Prepare orchestration invoke config
            agent_config.tools = self.master_server_client.available_tools_flattened
            agent_config.master_server_client = self.master_server_client

            # Invoke orchestration to pick tools
            result = await self.orch.graph.ainvoke(
                {"question": query},
                {"recursion_limit": 30},
            )
            logging.info(f'Orchestration result: {result}')

            # Retrieve tool responses
            answer = result.get('external_data')

            return answer

    # Server-server communications
    async def initialize_interserver_comms(self):
        self.master_server_client = MasterServerClient(self.app)

        try:
            for sub_server in self.sub_servers:
                await self.master_server_client.connect_to_server(sub_server)

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
            SubServer(url="http://localhost:8091/mcp", identifier='test_server_1'),
            SubServer(url="http://localhost:8092/mcp", identifier='test_server_2')
        ]
    )
    server.startup()
