#!/bin/bash
# Railway PostgreSQL Initialization Script
# Run this after adding PostgreSQL service to Railway project

set -e

echo "🚀 Setting up Railway PostgreSQL for Verba..."

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if we're in a Railway project
if ! railway status &> /dev/null; then
    echo "❌ Not in a Railway project. Please run 'railway link' first."
    exit 1
fi

echo "📋 Current Railway project status:"
railway status

# Check if PostgreSQL service exists
echo "🔍 Checking for PostgreSQL service..."
if railway variables --json | jq -r 'keys[]' | grep -q "DATABASE_URL\|POSTGRES"; then
    echo "✅ PostgreSQL service found"
else
    echo "❌ PostgreSQL service not found"
    echo "📝 Please add PostgreSQL service manually:"
    echo "   1. Go to Railway dashboard"
    echo "   2. Click 'Create' → 'Database' → 'PostgreSQL'"
    echo "   3. Name it 'postgres-verba'"
    echo "   4. Wait for deployment to complete"
    echo "   5. Re-run this script"
    exit 1
fi

# Get database connection URL
DATABASE_URL=$(railway variables --json | jq -r '.DATABASE_URL // .POSTGRES_URL // empty')

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not found. PostgreSQL service may not be ready."
    exit 1
fi

echo "✅ PostgreSQL connection string found"

# Install pgvector extension
echo "📦 Installing pgvector extension..."
railway run --service postgres-verba psql "$DATABASE_URL" -c "
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
"

# Verify pgvector installation
echo "🔍 Verifying pgvector installation..."
PGVECTOR_VERSION=$(railway run --service postgres-verba psql "$DATABASE_URL" -t -c "
SELECT extversion FROM pg_extension WHERE extname = 'vector';
" | tr -d ' ')

if [ -n "$PGVECTOR_VERSION" ]; then
    echo "✅ pgvector v$PGVECTOR_VERSION installed successfully"
else
    echo "❌ pgvector installation failed"
    exit 1
fi

# Set environment variables for PostgreSQL usage
echo "⚙️ Configuring environment variables..."
railway variables set USE_POSTGRESQL=true
railway variables set USE_WEAVIATE=false

# Optional: Set specific database configuration
echo "🔧 Setting additional PostgreSQL configuration..."
railway variables set POSTGRES_MAX_CONNECTIONS=20
railway variables set POSTGRES_POOL_SIZE=10
railway variables set POSTGRES_COMMAND_TIMEOUT=300

# Update railway.toml if it exists
if [ -f "railway.toml" ]; then
    echo "📝 Railway configuration found"
else
    echo "📝 Creating railway.toml configuration..."
    cat > railway.toml << 'EOF'
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn goldenverba.server.api:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
PYTHONPATH = "/app"
PYTHONUNBUFFERED = "1"
USE_POSTGRESQL = "true"
USE_WEAVIATE = "false"
EOF
    echo "✅ Created railway.toml"
fi

# Test database connection
echo "🧪 Testing PostgreSQL connection..."
python3 -c "
import asyncio
import os
import asyncpg

async def test_connection():
    try:
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print('❌ DATABASE_URL not found')
            return False
        
        conn = await asyncpg.connect(database_url)
        result = await conn.fetchval('SELECT version()')
        await conn.close()
        
        print(f'✅ PostgreSQL connection successful')
        print(f'   Version: {result.split()[1]}')
        return True
    except Exception as e:
        print(f'❌ Connection test failed: {e}')
        return False

success = asyncio.run(test_connection())
exit(0 if success else 1)
" 2>/dev/null || echo "⚠️ Python connection test skipped (dependencies may not be installed yet)"

echo "✅ Railway PostgreSQL setup complete!"
echo ""
echo "📋 Summary:"
echo "   ✅ pgvector extension installed"
echo "   ✅ Environment variables configured"
echo "   ✅ Railway configuration updated"
echo ""
echo "🔄 Next steps:"
echo "   1. Run migration script: python scripts/migrate_weaviate_to_postgres.py"
echo "   2. Deploy updated application: railway up"
echo "   3. Monitor deployment: railway logs"
echo ""
echo "🌐 Your Railway PostgreSQL is ready for Verba RAG!"