from mcp_master import MasterMCPServer, SubServer
from mcp_master import global_config as gconfig
from os import getenv, path

gconfig.selector_model_id = ''  # Set this to your tool selector model ID
gconfig.judge_model_id = ''  # Set this to your judge model ID
gconfig.judge_model_service_url = ''  # Set this to where your judge LLM is hosted
gconfig.OPENAI_API_KEY = getenv('OPENAI_API_KEY')
gconfig.OPENAI_BASE_URL = getenv('OPENAI_BASE_URL')  # Set this to where your other LLMs will be hosted, None for default
gconfig.autostart_abspath = path.normpath(path.join(path.dirname(__file__), 'demo-servers'))  # Set this to where your local servers are stored, None to ignore

# Create an MCP server on port 3000 with two test servers
# Ensure both test servers are running by starting them in the terminal before starting demo_master_server.py
server = MasterMCPServer(
    port=3000,
    sub_servers=[
        # Ensure all server identifiers are unique
        # If the server is located locally (as the demo servers are), ensure the server identifier matches the server's file name (without the .py)
        SubServer(url="http://localhost:8091/mcp", identifier='test_server_1'),
        SubServer(url="http://localhost:8092/mcp", identifier='test_server_2')
    ]
)
server.startup()
