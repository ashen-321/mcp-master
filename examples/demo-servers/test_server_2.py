import logging
from fastmcp import FastMCP
from mcp.server import Server
from starlette.requests import Request
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
app = FastMCP("test2")
started: bool = False


@app.tool(description="Return num1 (even) to the power of num2")
async def even_exponent(num1: int, num2: int) -> int:
    logging.info(f"Finding {num1}^{num2}")
    return num1 ** num2


def startup():
    global started
    
    if started:
        return

    started = True
    try:
        app.run(transport="streamable-http", host="0.0.0.0", port=8092)
    except KeyboardInterrupt:
        pass
    finally:
        logging.info('Server test_server_2 successfully shut down.')


if __name__ == '__main__':
    startup()
