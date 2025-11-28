"""Test MCP server functionality via HTTP streaming."""
import asyncio
import subprocess
import re
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


def discover_mcp_url() -> str:
    """Discover MCP API URL from ew discover output."""
    import json
    
    result = subprocess.run(['ew', 'discover', '--json'], capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    
    # Navigate JSON structure: data -> projects -> services
    for project in data.get('data', {}).get('projects', []):
        for service in project.get('services', []):
            if 'mcp-api' in service.get('name', ''):
                domains = service.get('domains', [])
                # Prefer -mcp-api- domain over -mcp. domain
                for domain in domains:
                    if 'mcp-api' in domain:
                        return f"https://{domain}/mcp"
                if domains:
                    return f"https://{domains[0]}/mcp"
    
    raise RuntimeError("Could not discover MCP API URL from 'ew discover --json'")


async def test_mcp_server():
    """Test the SLO curriculum search MCP server via HTTP streaming."""
    
    # Discover MCP server URL dynamically
    url = discover_mcp_url()
    
    # Create httpx client factory that disables SSL verification for localhost
    import httpx
    from mcp.shared._httpx_utils import create_mcp_http_client
    
    if url.endswith('.localhost/mcp'):
        # Custom factory that disables SSL verification for localhost
        def client_factory(*, headers=None, timeout=None, auth=None):
            return httpx.AsyncClient(verify=False, headers=headers, timeout=timeout, auth=auth)
    else:
        client_factory = create_mcp_http_client
    
    print(f"Connecting to MCP server at {url}...")
    async with streamablehttp_client(url, httpx_client_factory=client_factory) as (read_stream, write_stream, session_callback):
        async with ClientSession(read_stream, write_stream) as session:
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
