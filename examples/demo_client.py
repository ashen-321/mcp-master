from fastmcp import Client
import asyncio

client = Client('http://0.0.0.0:3000/mcp/')

async def call_tool(query: str):
    async with client:
        result = await client.call_tool("access_sub_mcp", {"query": query})
        print(result)

asyncio.run(call_tool("abc123"))
