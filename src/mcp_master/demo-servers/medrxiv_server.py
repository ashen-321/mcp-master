from typing import Any, List, Dict, Optional
import asyncio
import logging
from fastmcp import FastMCP
from mcp.server import Server
from starlette.requests import Request
from mcp.server.fastmcp.prompts import base
from starlette.applications import Starlette
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount, Route

from medrxiv_web_search import search_key_words, search_advanced, doi_get_medrxiv_metadata

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize FastMCP server
app = FastMCP("medrxiv")

@app.tool(description="Search medrxiv with keywords")
async def search_medrxiv_key_words(key_words: str, num_results: int = 10) -> List[Dict[str, Any]]:
    logging.info(f"Searching for articles with key words: {key_words}, num_results: {num_results}")
    """
    Search for articles on medRxiv using key words.

    Args:
        key_words: Search query string
        num_results: Number of results to return (default: 10)

    Returns:
        List of dictionaries containing article information
    """

    try:
        results = await asyncio.to_thread(search_key_words, key_words, num_results)
        return results
    except Exception as e:
        return [{"error": f"An error occurred while searching: {str(e)}"}]

@app.tool(description="Search medrxiv with advanced methods")
async def search_medrxiv_advanced(
    term: Optional[str] = None,
    title: Optional[str] = None,
    author1: Optional[str] = None,
    author2: Optional[str] = None,
    abstract_title: Optional[str] = None,
    text_abstract_title: Optional[str] = None,
    section: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    num_results: int = 5
) -> List[Dict[str, Any]]:
    logging.info(f"Performing advanced search with parameters: {locals()}")
    """
    Perform an advanced search for articles on medRxiv.

    Args:
        term: General search term
        title: Search in title
        author1: First author
        author2: Second author
        abstract_title: Search in abstract and title
        text_abstract_title: Search in full text, abstract, and title
        section: Section of medRxiv
        start_date: Start date for search range (format: YYYY-MM-DD)
        end_date: End date for search range (format: YYYY-MM-DD)
        num_results: Number of results to return (default: 10)

    Returns:
        List of dictionaries containing article information
    """
    try:
        results = await asyncio.to_thread(
            search_advanced,
            term, title, author1, author2, abstract_title, text_abstract_title,
            section, start_date, end_date, num_results
        )
        return results
    except Exception as e:
        return [{"error": f"An error occurred while performing advanced search: {str(e)}"}]

@app.tool(description="Search medrxiv with metadata")
async def get_medrxiv_metadata(doi: str) -> Dict[str, Any]:
    logging.info(f"Fetching metadata for DOI: {doi}")
    """
    Fetch metadata for a medRxiv article using its DOI.

    Args:
        doi: DOI of the article

    Returns:
        Dictionary containing article metadata
    """
    try:
        metadata = await asyncio.to_thread(doi_get_medrxiv_metadata, doi)
        return metadata if metadata else {"error": f"No metadata found for DOI: {doi}"}
    except Exception as e:
        return {"error": f"An error occurred while fetching metadata: {str(e)}"}

'''
@app.tool()
async def search_medrxiv(prompt: str="Covid-19", num_results: int=3) -> Dict[str, Any]:
    print(f"In MCP Server search_medrxiv: {prompt}")
    results = await search_medrxiv_key_words(prompt)
    return results
'''

@app.prompt(description="Search medrxiv with prompts")
def get_initial_prompts() -> list[base.Message]:
    return [
        base.UserMessage("You are a helpful assistant that can help with medical research and clinical related questions."),
    ]


def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # noqa: SLF001
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

app.run(transport="streamable-http",host="0.0.0.0",port=8090)
'''
if __name__ == "__main__":
    mcp_server = app._mcp_server  # noqa: WPS437

    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8083, help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)
'''