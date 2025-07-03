# mcp-master
A Python package for master MCP servers.

<div align="center">

<strong>Python implementation of the Model Context Protocol (MCP)</strong>

[![PyPI][pypi-badge]][pypi-url]
[![MIT licensed][mit-badge]][mit-url]
[![Python Version][python-badge]][python-url]

</div>

<!-- omit in toc -->
## Table of Contents

- [MCP Master](#mcp-master)
  - [Overview](#overview)
  - [Installation](#installation)
  - [Quickstart](#quickstart)
    - [Master MCP Servers](#master-mcp-servers)
    - [Master MCP Clients](#master-mcp-clients)
  - [License](#license)

[pypi-badge]: https://img.shields.io/pypi/v/mcp-master
[pypi-url]: https://pypi.org/project/mcp/
[mit-badge]: https://img.shields.io/badge/license-MIT-blue
[mit-url]: https://github.com/ashen-321/mcp-master/blob/main/LICENSE
[python-badge]: https://img.shields.io/badge/python-3.12%20%7C%203.13-green
[python-url]: https://www.python.org/downloads/

## Overview

The MCP Master package allows the creation of intermediaries between clients and MCP servers. This offloads tool-related reasoning and logic to the master server without requiring client-side modifications. This Python package provides full master MCP support, making it easy to:

- Build MCP master servers that connect clients to multiple MCP servers through the Streamable HTTP transport
- Choose tools via reasoning structures like LangGraph
- Easily scale the available selection of tools

Read about the Model Context Protocol [here](https://github.com/modelcontextprotocol/python-sdk).

## Installation

For projects using pip:
```bash
pip install mcp-master
```

## Quickstart

### Master MCP Servers

A simple master MCP server that connects to two of the included demo servers:

```python
# master_server.py
from mcp_master import MasterMCPServer
import asyncio
from os import getenv

set_config({
    'judge_model_id': "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    'judge_model_service_url': '', # Set this to where your judge LLM is hosted
    'OPENAI_API_KEY': getenv('OPENAI_API_KEY'), 
    'OPENAI_BASE_URL': getenv('OPENAI_BASE_URL'), # Set this to where your other LLMs will be hosted
})

# Create an MCP server on port 3000 with two test servers
# Ensure both test servers are running by starting them in the terminal before starting master_server.py
server = MasterMCPServer(3000, [
    ("http://localhost:8091/mcp", 'test_server_1'),
    ("http://localhost:8092/mcp", 'test_server_2')
])
asyncio.run(server.startup())
```

You can run this server in the terminal by running:
```bash
python master_server.py
```

### Master MCP Clients

[MCP clients](https://modelcontextprotocol.io/quickstart/client) utilizing the streamable-HTTP protocol can connect to master MCP servers without any modification. Details provided in the URL.

For a complete working example, see [the MCP GitHub repository](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/client/streamable_http.py).

## License

This project is licensed under the MIT License - see the LICENSE file for details.