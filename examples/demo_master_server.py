from mcp_master import MasterMCPServer
from mcp_master import global_config as gconfig
from os import getenv

gconfig.selector_model_id = ''  # Set this to your tool selector model ID
gconfig.judge_model_id = ''  # Set this to your judge model ID
gconfig.judge_model_service_url = ''  # Set this to where your judge LLM is hosted
gconfig.OPENAI_API_KEY = getenv('OPENAI_API_KEY')
gconfig.OPENAI_BASE_URL = getenv('OPENAI_BASE_URL')  # Set this to where your other LLMs will be hosted, None for default

# Create an MCP server on port 3000 with two test servers
# Ensure both test servers are running by starting them in the terminal before starting demo_master_server.py
server = MasterMCPServer(
    port=3000,
    sub_servers=[
        # (server url, server identifier) pairs - ensure all server identifiers are unique
        # If the server is located locally (as the demo servers are), ensure the server identifier matches the server's file name (without the .py)
        ("http://localhost:8091/mcp", 'test_server_1'),
        ("http://localhost:8092/mcp", 'test_server_2')
    ]
)
server.startup()
