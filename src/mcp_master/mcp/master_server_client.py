from typing import Optional
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import os
import sys
import asyncio
import httpx
import logging
from subprocess import Popen

model_id_c37 = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
model_id_nova = "us.amazon.nova-lite-v1:0"
model_id_llama = "meta.llama3-3-70b-instruct-v1:0"

module_paths = ["./", "../", "../orchestration"]
file_path = os.path.dirname(__file__)
os.chdir(file_path)

for module_path in module_paths:
    full_path = os.path.normpath(os.path.join(file_path, module_path))
    sys.path.append(full_path)

from config import *

try:
    os.environ["OPENAI_API_KEY"] = api_key = gconfig.get('OPENAI_API_KEY')
    os.environ["OPENAI_BASE_URL"] = base_url = gconfig.get("OPENAI_BASE_URL")
except TypeError as e:
    raise ConfigError("Ensure your OPENAI_API_KEY and OPENAI_BASE_URL are properly configured via set_config().")

from agents import set_agent_config


# --------------------------------------------------------------------------------------------
# Config -------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------------


TOOL_NAME_ORIGIN_SEPARATOR = '09090'
MASTER_TOOL_DESCRIPTION_HEADER = 'Automatically interface with other MCP servers for the following tools:'
MASTER_DISPATCHER_SYSTEM_HEADER = ("You are a tool dispatcher agent who decides which tools to dispatch to based on "
                                   "the user's input. Depending on your answer, question will be routed to the right "
                                   "tools, so your task is crucial.")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# --------------------------------------------------------------------------------------------
# Master Server Client Class -----------------------------------------------------------------
# --------------------------------------------------------------------------------------------


class MasterServerClient:
    """MCP Client for interacting with an MCP Streamable HTTP server"""

    def __init__(self, app):
        # Initialize session and client objects
        self.sessions = {}
        self._streams_contexts = {}
        self._session_contexts = {}
        self.available_tools = {}
        self.available_tools_flattened = []
        self._sub_server_popens = {}
        self._app = app

    async def check_if_server_running(self, server_url: str, server_filename: str):
        try:
            # Send request to see if the server is already running
            async with httpx.AsyncClient(timeout=30.0) as client:
                logging.info(f"HTTP GET attempt to {server_url}")
                
                response = await client.get(server_url)
                response.raise_for_status()

                # Exit if already running
                return True

        except httpx.HTTPStatusError:
            # Exit if sent a redirect error (normal behavior)
            return True
                
        except (httpx.TimeoutException, httpx.ConnectError) as e:
            logging.warning(f"HTTP request attempt failed: {type(e).__name__}: {e}")

            # Exit if the server is not present in the folder
            os.chdir(file_path)
            server_path = os.path.normpath(os.path.join(file_path, f'{server_filename}.py'))

            if not os.path.exists(server_path):
                return False

            # Run start command to start the server
            logging.info(f"Sending start command for {server_filename}...")
            # No temporary variable to avoid deep copying
            self._sub_server_popens[server_filename] = Popen(['python', f'{server_filename}.py'])

            # Wait for the server to start, abort after 10 seconds
            attempt_count = 1
            async with httpx.AsyncClient(timeout=10.0) as client:
                while True:
                    try:
                        logging.debug(f"HTTP GET attempt to {server_url}")
                        
                        response = await client.get(server_url)
                        response.raise_for_status()
            
                        # Exit if running
                        return True
                        
                    except (httpx.TimeoutException, httpx.ConnectError) as e:
                        # Try again in 0.5 seconds if the request failed
                        logging.warning(f"HTTP request attempt {attempt_count} failed: {type(e).__name__}: {e}")
                        logging.info(f"Waiting 0.5 seconds...")
                        attempt_count += 1
                        await asyncio.sleep(0.5)
                        
                    except (httpx.HTTPStatusError) as e:
                        # Exit if sent a redirect error (normal behavior)
                        return True
                        
                    except Exception as e:
                        # Abort if an unusual error is caught
                        logging.error(f"Unexpected error in HTTP request: {e}")
                        return False
                
        except Exception as e:
            # Abort if an unusual error is caught
            logging.error(f"Unexpected error in HTTP request: {e}")
            return False

    async def connect_to_server(self, server_url: str, server_filename: str, headers: dict = {}):
        """Connect to an MCP server running on streamable HTTP"""
        # Exit if the server is not running despite attempts to start it
        if not await self.check_if_server_running(server_url, server_filename):
            logging.error(f"Failed to connect to server {server_filename} at {server_url}.")
            return
        
        # No temporary variables to avoid deep copying every single instance
        self._streams_contexts[server_filename] = streamablehttp_client(url=server_url, headers=headers)
        read_stream, write_stream, _ = await self._streams_contexts[server_filename].__aenter__()

        self._session_contexts[server_filename] = ClientSession(read_stream, write_stream)
        self.sessions[server_filename] = await self._session_contexts[server_filename].__aenter__()

        await self.sessions[server_filename].initialize()

        # Save tools to class data
        await self.get_available_tools(server_filename)

        logging.info(f"Connected to server {server_filename} at {server_url}.")
    
    async def get_available_tools(self, server_filename: str):
        """Get available tools from the server"""
        try:
            # Fetch tools
            logging.info(f"Fetching available server tools from {server_filename}...")
            response = await self.sessions[server_filename].list_tools()
            logging.info(f"Connected to MCP server {server_filename} with tools {[tool.name for tool in response.tools]}.")
    
            # Format tools for OpenAI
            available_tools = [
                {
                    "type": 'function',
                    "function": {
                        "name": f"{tool.name}{TOOL_NAME_ORIGIN_SEPARATOR}{server_filename}",
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                    "strict": True,
                }
                for tool in response.tools
            ]

            # Save tools
            self.available_tools[server_filename] = available_tools
            self.available_tools_flattened.extend(available_tools)

            # Compile tool descriptions into the master server tool description
            self.compile_tool_descriptions()
            
        except Exception as e:
            logging.error(f'Tool fetch for server {server_filename} failed: {e}')
            
            # Blank list failsafe in case the tool fetch fails
            self.available_tools[server_filename] = []

    def compile_tool_descriptions(self):
        logging.info("Compiling all available tool descriptions...")

        # Generate description based on sub mcp server tool descriptions
        tool_description = MASTER_TOOL_DESCRIPTION_HEADER
        dispatcher_system_message = f'{MASTER_DISPATCHER_SYSTEM_HEADER}\nThere are {len(self.available_tools_flattened)} possible tools to use:'

        for server in self.available_tools:
            for tool in self.available_tools[server]:
                tool_description += f'\n{tool['function']['description']}'
                dispatcher_system_message += f'\n - {tool['function']['name']}: {tool['function']['description']}'

        # Save description directly to tool
        logging.info(f"Compiled description: {tool_description}")
        self._app._tool_manager._tools.get('access_sub_mcp').description = tool_description

        # Save dispatcher node system message to orchestration
        dispatcher_system_message += "Always call at least one tool. Do not attempt to generate your own response to the user's query."
        set_agent_config({'dispatcher_system_message': dispatcher_system_message})
                
    async def call_tool(self, tool_name: str, tool_args: Optional[dict]):
        tool_name, server_filename = tool_name.split(TOOL_NAME_ORIGIN_SEPARATOR)
        logging.info(f"Calling tool {tool_name} from {server_filename} with args {tool_args}...")

        try:
            # Call tool
            result = await self.sessions[server_filename].call_tool(tool_name, tool_args)
            return result
        except Exception:
            # Remove tool from server tool list
            if tool_name in self.available_tools[server_filename]:
                self.available_tools[server_filename].remove(tool_name)
            
            logging.error(f"Tool {tool_name} from {server_filename} is currently unavailable:")
            # raise Exception(e)

    async def server_loop(self):
        while True:
            try:
                await asyncio.sleep(1)
            except Exception as e:
                logging.error(f"\nServer loop error: {str(e)}")

    async def cleanup(self):
        """Properly clean up the sessions and streams"""
        if self._sub_server_popens:
            for popen_id in self._sub_server_popens:
                self._sub_server_popens[popen_id].terminate()
                
        if self._session_contexts:
            for context_id in self._session_contexts:
                await self._session_contexts[context_id].__aexit__(None, None, None)
                
        if self._streams_contexts:
            for context_id in self._session_contexts:
                await self._streams_contexts[context_id].__aexit__(None, None, None)
