# SLO Search API - Setup Guide

Complete step-by-step setup instructions.

## Prerequisites

- Python 3.9+
- PostgreSQL 14+ with pgvector extension
- Git
- ~2GB disk space (embedding model + data)

## Step-by-Step Setup

### 1. Install PostgreSQL + pgvector

**Ubuntu/Debian:**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Install pgvector
sudo apt install postgresql-15-pgvector

# Or build from source:
# cd /tmp
# git clone https://github.com/pgvector/pgvector.git
# cd pgvector
# make
# sudo make install
```

**macOS:**
```bash
brew install postgresql pgvector
```

**Verify:**
```bash
sudo -u postgres psql -c "CREATE EXTENSION vector" postgres
```

### 2. Clone Curriculum Data

```bash
cd /path/to/projects
git clone https://github.com/slonl/curriculum-fo.git
```

### 3. Setup Project

```bash
# Clone or create project directory
cd slo-search

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit if needed (defaults should work)
nano .env
```

### 5. Initialize Database

```bash
# Run setup validation
python setup.py
```

This will:
- Check PostgreSQL connection
- Download embedding model (~100MB first time)
- Create database `slo_search`
- Initialize tables with pgvector

### 6. Ingest Data

```bash
# Load curriculum data and generate embeddings
# Takes ~5-10 minutes for 2642 doelzinnen + 10231 uitwerkingen
python ingest.py
```

Progress output:
