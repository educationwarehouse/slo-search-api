"""Test MCP server functionality."""
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the SLO curriculum search MCP server."""
    
    # Start MCP server as subprocess
    params = StdioServerParameters(
        command='python',
        args=['mcp_server.py']
    )
    
    print("Starting MCP server...")
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            print("Initializing session...")
            await session.initialize()
            
            print("\n=== Test 1: Database Statistics ===")
            result = await session.call_tool('stats', {})
            print(result.content[0].text)
            
            print("\n=== Test 2: Search for 'fotosynthese' ===")
            result = await session.call_tool('search', {
                'query': 'fotosynthese',
                'limit': 5,
                'threshold': 0.6
            })
            print(result.content[0].text)
            
            print("\n=== Test 3: Search goals only ===")
            result = await session.call_tool('search_goals', {
                'query': 'wiskunde',
                'limit': 3
            })
            print(result.content[0].text)
            
            print("\n=== Test 4: Get specific goal ===")
            result = await session.call_tool('get_goal', {
                'doelzin_id': 1
            })
            print(result.content[0].text)
            
            print("\n✓ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
