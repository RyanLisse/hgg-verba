# PostgreSQL Migration Guide

This document describes the migration from Supabase to plain PostgreSQL with pgvector extension.

## Overview

The application has been successfully migrated from Supabase-specific features to work with any PostgreSQL instance that has the pgvector extension installed. This removes vendor lock-in and makes the application more flexible.

## Changes Made

### 1. Dependencies Updated
- **Removed**: `supabase`, `weaviate-client`
- **Added**: `psycopg2-binary` for additional PostgreSQL support
- **Kept**: `asyncpg`, `pgvector` for core PostgreSQL functionality
- **Updated**: All other dependencies to latest compatible versions

### 2. API Migration
- **Old**: `api_supabase.py` (Supabase-specific)
- **New**: `api_postgresql.py` (Generic PostgreSQL)
- **CLI Updated**: Points to the new PostgreSQL API

### 3. Database Manager
- **Enhanced**: `postgresql_manager.py` with additional methods
- **Added**: Generic database schema (`database_schema.sql`)
- **Removed**: Dependencies on Supabase-specific managers

### 4. Environment Variables

The application now uses standard PostgreSQL environment variables:

#### Required Variables
```bash
# Database connection (choose one method)

# Method 1: Full database URL
DATABASE_URL=postgresql://username:password@host:port/database

# Method 2: Individual components
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=verba
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Application port (optional, defaults to 8000)
PORT=3000
```

#### Legacy Support
The application still supports Railway-specific environment variables for backward compatibility:
- `RAILWAY_POSTGRES_URL`
- `RAILWAY_POSTGRES_HOST`
- `RAILWAY_POSTGRES_PORT`
- `RAILWAY_POSTGRES_DATABASE`
- `RAILWAY_POSTGRES_USER`
- `RAILWAY_POSTGRES_PASSWORD`

## Database Setup

### Prerequisites
1. PostgreSQL instance (version 12+)
2. pgvector extension installed

### Installation Steps

#### 1. Install pgvector Extension
```sql
-- Connect to your PostgreSQL database and run:
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 2. Initialize Schema
The application will automatically create the required tables and indexes on first startup. The schema includes:

- `verba_documents` - Main documents table
- `verba_chunks` - Document chunks with vector embeddings
- `verba_config` - Application configuration
- `verba_suggestions` - Query suggestions

#### 3. Manual Schema Setup (Optional)
If you prefer to set up the schema manually:

```bash
# Copy the schema file to your PostgreSQL instance
psql -h your_host -U your_user -d your_database -f goldenverba/components/database_schema.sql
```

## Docker Usage

### Build the Image
```bash
docker build -t verba-postgresql .
```

### Run with Environment Variables
```bash
# Using full database URL
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  verba-postgresql

# Using individual components
docker run -p 8000:8000 \
  -e POSTGRES_HOST=your_host \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=verba \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=your_password \
  -e PORT=8000 \
  verba-postgresql
```

### Docker Compose Example
```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: verba
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  verba:
    build: .
    ports:
      - "8000:8000"
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: verba
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      PORT: 8000
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## API Endpoints

The new PostgreSQL API provides the following endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check with database connectivity
- `POST /documents` - Upload documents
- `GET /documents` - List documents with pagination
- `DELETE /documents/{id}` - Delete documents
- `POST /search` - Vector similarity search
- `POST /configurations` - Save configuration
- `GET /configurations/{type}` - Get configuration
- `WebSocket /ws` - Real-time communication

## Migration from Supabase

If you're migrating from an existing Supabase installation:

1. **Export your data** from Supabase
2. **Set up PostgreSQL** with pgvector extension
3. **Import your data** using the new schema
4. **Update environment variables** to point to your PostgreSQL instance
5. **Deploy** the updated application

## Troubleshooting

### Common Issues

1. **"pgvector extension not found"**
   - Install pgvector extension in your PostgreSQL instance
   - Ensure your PostgreSQL version supports extensions

2. **"Connection refused"**
   - Check your database connection parameters
   - Ensure PostgreSQL is running and accessible
   - Verify firewall settings

3. **"Permission denied"**
   - Check database user permissions
   - Ensure the user can create tables and indexes

### Health Check
Use the `/health` endpoint to verify database connectivity:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Performance Considerations

1. **Vector Index**: The application creates IVFFLAT indexes for vector similarity search
2. **Connection Pooling**: Uses asyncpg connection pooling for better performance
3. **Full-text Search**: Includes PostgreSQL full-text search capabilities as fallback

## Security

1. **Use strong passwords** for database connections
2. **Enable SSL** for production deployments
3. **Restrict database access** to application servers only
4. **Regular backups** of your PostgreSQL database

## Support

For issues related to the PostgreSQL migration, check:
1. Database connectivity and credentials
2. pgvector extension installation
3. Application logs for detailed error messages
