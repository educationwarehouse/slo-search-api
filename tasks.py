from pathlib import Path
from edwh import tasks, task
from invoke import Context

# REQUIRED: ensure a .env file exists
if not Path(".env").exists():
    with open(Path(".env"), "x") as env_file:
        env_file.close()

context = Context()
check_env = tasks.check_env
generate_password = tasks.generate_password


@task
def setup(c):
    """Configure environment variables for SLO Search with OpenRouter."""
    
    print("\n=== SLO Search Environment Setup ===\n")
    
    # 1. OpenRouter API Key (required)
    check_env(
        "OPENROUTER_API_KEY",
        default="",
        comment="Required: Your OpenRouter API key for embeddings and LLM re-ranking\n"
                "Get one at: https://openrouter.ai/keys"
    )
    
    # 2. Database URI
    check_env(
        "DATABASE_URI",
        default="postgres://slo:slo_password@postgres:5432/slo_search",
        comment="Database connection string\n"
                "PostgreSQL (recommended): postgres://user:pass@host:port/database\n"
                "SQLite (development): sqlite:///slo_search.db"
    )
    
    # 3. Embedding Model
    check_env(
        "EMBEDDING_MODEL",
        default="openai/text-embedding-3-small",
        comment="OpenRouter embedding model (1536 dimensions)\n"
                "Options: openai/text-embedding-3-small, openai/text-embedding-3-large"
    )
    
    # 4. LLM Model for re-ranking
    check_env(
        "LLM_MODEL",
        default="openai/gpt-4o-mini",
        comment="OpenRouter LLM model for search result re-ranking\n"
                "Options: openai/gpt-4o-mini, openai/gpt-4o, anthropic/claude-3.5-sonnet"
    )
    
    # 5. Data Directory
    check_env(
        "DATA_DIR",
        default="/app/data",
        comment="Path to curriculum data directory\n"
                "Docker: /app/data (maps to ../curriculum-fo/data)\n"
                "Local: ./data or /absolute/path/to/curriculum-fo/data"
    )
    
    print("\n✓ Environment setup complete!")
    print("\nNext steps:")
    print("  1. Review .env file and update OPENROUTER_API_KEY")
    print("  2. Start services: docker compose up -d")
    print("  3. Ingest data: docker compose exec api python ingest.py")
    print("  4. Test API: curl http://localhost:8000/api/stats\n")


@task
def validate(c):
    """Validate that all required environment variables are set."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required = {
        "OPENROUTER_API_KEY": "OpenRouter API key",
        "DATABASE_URI": "Database connection string",
        "EMBEDDING_MODEL": "Embedding model name",
        "LLM_MODEL": "LLM model name",
        "DATA_DIR": "Data directory path"
    }
    
    print("\n=== Environment Validation ===\n")
    
    all_valid = True
    for key, description in required.items():
        value = os.getenv(key)
        if value and value != "":
            print(f"✓ {key}: {description}")
        else:
            print(f"✗ {key}: {description} - NOT SET")
            all_valid = False
    
    if all_valid:
        print("\n✓ All environment variables are configured!\n")
    else:
        print("\n✗ Some environment variables are missing. Run: ew setup\n")
    
    return all_valid


@task
def generate_db_password(c, length: int = 20):
    """Generate a secure random password for database."""
    password = generate_password(context, length)
    print(f"\nGenerated password: {password}")
    print(f"\nTo use in DATABASE_URI:")
    print(f"postgres://slo:{password}@postgres:5432/slo_search\n")
