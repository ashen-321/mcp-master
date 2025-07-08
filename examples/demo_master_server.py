from src.mcp_master import MasterMCPServer
from src.mcp_master import global_config as gconfig
import asyncio
from os import getenv

gconfig.judge_model_id = ''  # Set this to your judge model ID
gconfig.judge_model_service_url = ''  # Set this to where your judge LLM is hosted
gconfig.OPENAI_API_KEY = getenv('OPENAI_API_KEY')
gconfig.OPENAI_BASE_URL = getenv('OPENAI_BASE_URL')  # Set this to where your other LLMs will be hosted

# Create an MCP server on port 3000 with two test servers
# Ensure both test servers are running by starting them in the terminal before starting demo_master_server.py
server = MasterMCPServer(
    port=3000,
    sub_servers=[
        ("http://localhost:8091/mcp", 'test_server_1'),
        ("http://localhost:8092/mcp", 'test_server_2')
    ]
)
asyncio.run(server.startup())
