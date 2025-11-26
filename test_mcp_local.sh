#!/bin/bash
# Test MCP server from host with proper database connection

export DATABASE_URI="postgres://slo:slo_password@localhost:5432/slo_search"
export OPENROUTER_API_KEY="${OPENROUTER_API_KEY:-$(grep OPENROUTER_API_KEY .env | cut -d'=' -f2)}"
export EMBEDDING_MODEL="openai/text-embedding-3-small"
export LLM_MODEL="openai/gpt-4o-mini"

echo "Testing MCP server with PostgreSQL at localhost:5432..."
python test_mcp.py
