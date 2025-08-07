# Railway PostgreSQL Setup Instructions

## Manual Setup Required

Since the Railway CLI requires interactive mode for adding databases, follow these steps:

### 1. Add PostgreSQL Service via Railway Dashboard

1. Go to https://railway.app/project/650652b3-2cd1-478e-9f99-a1abe966843f
2. Click "Create" → "Database" → "PostgreSQL"
3. Name the service: `postgres-verba`
4. Wait for deployment to complete

### 2. Environment Variables Setup

After PostgreSQL service is created, these variables will be automatically available:
```bash
DATABASE_URL=postgresql://postgres:password@host:5432/dbname
POSTGRES_URL=postgresql://postgres:password@host:5432/dbname
POSTGRES_HOST=host
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=dbname
```

### 3. Configure pgvector Extension

Run this command to connect and setup pgvector:
```bash
railway connect postgres-verba
```

Then execute:
```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### 4. Update Environment Variables

Set these additional variables for Verba:
```bash
# Configure pure PostgreSQL backend
railway variables set DATABASE_URL=${{Postgres.DATABASE_URL}}

# Optional: Set specific database name
railway variables set POSTGRES_DB=verba_rag
```

### 5. Deploy Updated Configuration

```bash
# Deploy with new configuration
railway up

# Check deployment logs
railway logs
```

## Automated Setup Script

Run this script after PostgreSQL service is added:

```bash
#!/bin/bash
# railway-postgres-init.sh

echo "🚀 Setting up Railway PostgreSQL for Verba..."

# Connect to PostgreSQL and setup extensions
echo "📦 Installing pgvector extension..."
railway run --service postgres-verba psql $DATABASE_URL -c "
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
SELECT 'pgvector version: ' || extversion FROM pg_extension WHERE extname = 'vector';
"

# Set environment variables
echo "⚙️ Configuring environment variables..."
railway variables set USE_POSTGRESQL=true

echo "✅ Railway PostgreSQL setup complete!"
echo "🔄 Redeploying application..."
railway up
```

## Database Initialization

PostgreSQL will be automatically initialized with the required schema when the application starts. No manual migration is needed for new installations.

## Verification

Test the connection:
```bash
railway run python -c "
from goldenverba.components.railway_postgres_manager import RailwayPostgresManager
import asyncio

async def test():
    manager = RailwayPostgresManager()
    await manager.initialize()
    print('✅ PostgreSQL connection successful!')
    await manager.close()

asyncio.run(test())
"
```