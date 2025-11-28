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
    """Configure environment variables for SLO Search with OpenRouter and Traefik."""
    
    print("\n=== SLO Search Environment Setup ===\n")
    
    # 1. Project name for Docker and Traefik
    project = check_env(
        "PROJECT",
        default="slo-search",
        comment="Project naam voor Docker containers en Traefik routing"
    )
    assert project.strip() and project.replace('-', '').replace('_', '').isalnum(), \
        "PROJECT moet alfanumeriek zijn (- en _ toegestaan)"
    
    # 2. Hosting domain for Traefik
    domain = check_env(
        "HOSTINGDOMAIN",
        default="localhost",
        comment="Domain voor Traefik routing (bijv. example.com)\n"
                f"API beschikbaar op: {project}-rest-api.{{domain}}\n"
                f"MCP beschikbaar op: {project}-mcp-api.{{domain}}"
    )
    assert domain.strip(), "HOSTINGDOMAIN mag niet leeg zijn"
    
    # 3. Clone curriculum-fo repository if not exists
    curriculum_path = Path("../curriculum-fo")
    if not curriculum_path.exists():
        print(f"\n📦 Cloning curriculum data repository...")
        c.run("git clone https://github.com/slonl/curriculum-fo.git ../curriculum-fo")
        print(f"✓ Curriculum data cloned to {curriculum_path.resolve()}")
    elif not (curriculum_path / "data").exists():
        print(f"\n⚠️  WARNING: Data directory not found in {curriculum_path.resolve()}")
        print("Repository may be incomplete. Try: rm -rf ../curriculum-fo && ew setup\n")
    else:
        print(f"✓ Curriculum data found at {curriculum_path.resolve()}")
    
    # 4. OpenRouter API Key (required)
    check_env(
        "OPENROUTER_API_KEY",
        default="",
        comment="Required: Your OpenRouter API key for embeddings and LLM re-ranking\n"
                "Get one at: https://openrouter.ai/keys"
    )
    
    # 5. Database URI
    check_env(
        "DATABASE_URI",
        default="postgres://slo:slo_password@postgres:5432/slo_search",
        comment="Database connection string\n"
                "PostgreSQL (recommended): postgres://user:pass@host:port/database\n"
                "PostgreSQL: postgres://slo:slo_password@postgres:5432/slo_search"
    )
    
    # 6. Embedding Model
    check_env(
        "EMBEDDING_MODEL",
        default="openai/text-embedding-3-small",
        comment="OpenRouter embedding model (1536 dimensions)\n"
                "Options: openai/text-embedding-3-small, openai/text-embedding-3-large"
    )
    
    # 7. LLM Model for re-ranking
    check_env(
        "LLM_MODEL",
        default="openai/gpt-4o-mini",
        comment="OpenRouter LLM model for search result re-ranking\n"
                "Options: openai/gpt-4o-mini, openai/gpt-4o, anthropic/claude-3.5-sonnet"
    )
    
    # 8. Data Directory
    check_env(
        "DATA_DIR",
        default="/app/data",
        comment="Path to curriculum data directory\n"
                "Docker: /app/data (maps to ../curriculum-fo/data)\n"
                "Local: ./data or /absolute/path/to/curriculum-fo/data"
    )
    
    print(f"\n✅ Setup compleet!")
    print(f"\nTraefik URLs:")
    print(f"  API: https://{project}-rest-api.{domain}")
    print(f"       (legacy: https://slo-search-api.{domain})")
    print(f"  MCP: https://{project}-mcp-api.{domain}")
    print(f"       (legacy: https://slo-search-mcp.{domain})")
    print("\nNext steps:")
    print("  1. Review .env file and update OPENROUTER_API_KEY")
    print("  2. Ensure Traefik broker network exists: docker network create broker")
    print("  3. Start services: docker compose up -d")
    print("  4. Ingest data: docker compose exec rest-api python ingest.py")
    print(f"  5. Test API: curl https://{project}-api.{domain}/api/stats\n")


@task
def validate(c):
    """Validate that all required environment variables are set."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required = {
        "PROJECT": "Project name for Docker/Traefik",
        "HOSTINGDOMAIN": "Domain for Traefik routing",
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
    
    # Check curriculum-fo repository
    curriculum_path = Path("../curriculum-fo")
    if curriculum_path.exists() and (curriculum_path / "data").exists():
        print(f"✓ CURRICULUM_DATA: Repository found at {curriculum_path.resolve()}")
    else:
        print(f"✗ CURRICULUM_DATA: Repository not found at {curriculum_path.resolve()}")
        all_valid = False
    
    if all_valid:
        print("\n✓ All environment variables are configured!\n")
        project = os.getenv("PROJECT", "slo-search")
        domain = os.getenv("HOSTINGDOMAIN", "localhost")
        print(f"API: https://{project}-rest-api.{domain}")
        print(f"     (legacy: https://slo-search-api.{domain})")
        print(f"MCP: https://{project}-mcp-api.{domain}")
        print(f"     (legacy: https://slo-search-mcp.{domain})\n")
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


@task
def ingest(c):
    """Run data ingestion in Docker container."""
    print("\n📥 Starting data ingestion...")
    print("This will generate ~12,873 embeddings via OpenRouter API\n")
    c.run("docker compose exec rest-api python ingest.py")
    print("\n✅ Ingestion complete!")
