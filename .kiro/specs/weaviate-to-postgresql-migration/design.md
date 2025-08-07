# Design Document

## Overview

This design outlines the complete migration strategy from Weaviate to PostgreSQL with pgvector for the Verba RAG application. The migration involves systematically removing all Weaviate dependencies, cleaning up configuration files, updating environment settings, and ensuring seamless operation with PostgreSQL as the sole vector database backend.

Based on the codebase analysis, the migration affects multiple layers of the application:
- Backend Python code with Weaviate imports and managers
- Frontend built assets containing Weaviate references
- Configuration files (Docker Compose, environment variables)
- Documentation and setup scripts
- Package dependencies in setup.py and requirements files

## Architecture

### Current State Analysis

The current codebase has a dual-database architecture supporting both Weaviate and PostgreSQL:

1. **Database Managers**: `VerbaWeaviateManager` and `SupabaseManager` coexist
2. **Embedding Components**: `WeaviateEmbedder` alongside other embedders
3. **Configuration**: Environment variables for both databases
4. **Docker Setup**: Weaviate service defined in docker-compose.yml
5. **Migration Tools**: Existing migration script from Weaviate to Supabase

### Target State Architecture

The target architecture will be PostgreSQL-only:

1. **Single Database Backend**: Only `SupabaseManager` for all database operations
2. **Embedding Components**: Remove `WeaviateEmbedder`, keep other embedders
3. **Configuration**: Only PostgreSQL/Supabase environment variables
4. **Docker Setup**: Remove Weaviate service, keep only Verba service
5. **Clean Codebase**: No Weaviate imports or references

## Components and Interfaces

### 1. Database Layer Cleanup

**Files to Remove:**
- `goldenverba/components/embedding/WeaviateEmbedder.py`
- `goldenverba/components/embedding/__pycache__/WeaviateEmbedder.cpython-*.pyc`

**Files to Modify:**
- `goldenverba/components/managers.py` - Remove VerbaWeaviateManager class and Weaviate imports
- `goldenverba/components/embedding/__init__.py` - Remove WeaviateEmbedder import
- `goldenverba/verba_manager_supabase.py` - Remove conditional Weaviate manager logic

### 2. Configuration Layer Cleanup

**Files to Modify:**
- `docker-compose.yml` - Remove Weaviate service and dependencies
- `.env.example` - Remove Weaviate environment variables
- `setup.py` - Remove weaviate-client dependency (if present)
- `requirements-supabase.txt` - Remove weaviate-client from optional dependencies

### 3. Frontend Assets Cleanup

**Files to Remove/Rebuild:**
- All files in `goldenverba/server/frontend/out/_next/static/chunks/app/` containing Weaviate references
- These are built assets that will be regenerated after backend cleanup

### 4. Documentation and Scripts Cleanup

**Files to Modify:**
- `CLAUDE.md` - Update Weaviate references to PostgreSQL
- `railway-postgres-setup.md` - Remove Weaviate migration references
- `.kiro/steering/product.md` - Update database description
- `.kiro/steering/structure.md` - Update architecture description

**Files to Keep (for reference):**
- `migration/migrate_weaviate_to_supabase.py` - Keep for historical reference and potential data recovery

## Data Models

### Environment Variables

**Remove:**
- `WEAVIATE_URL_VERBA`
- `WEAVIATE_API_KEY_VERBA`
- `USE_WEAVIATE`

**Keep/Add:**
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_DB_HOST`
- `SUPABASE_DB_PASSWORD`
- `SUPABASE_DB_NAME`
- `SUPABASE_DB_PORT`
- `USE_POSTGRESQL=true`

### Database Manager Interface

The application will use only the `SupabaseManager` class, which implements the same interface as the removed `VerbaWeaviateManager`. This ensures compatibility with existing code that depends on the manager interface.

## Error Handling

### Migration Safety Measures

1. **Backup Strategy**: Ensure Railway PostgreSQL contains all migrated data before removing Weaviate
2. **Rollback Plan**: Keep migration script available for potential data recovery
3. **Validation Steps**: Test all API endpoints before removing Weaviate service
4. **Gradual Removal**: Remove code dependencies first, then configuration, then services

### Error Detection

1. **Import Errors**: Check for broken imports after removing Weaviate classes
2. **Runtime Errors**: Test application startup and core functionality
3. **API Errors**: Verify all endpoints work with PostgreSQL backend
4. **Frontend Errors**: Ensure UI components function correctly

## Testing Strategy

### Pre-Migration Testing

1. **Backup Verification**: Confirm all data exists in PostgreSQL
2. **Functionality Testing**: Test core RAG pipeline with PostgreSQL
3. **Performance Testing**: Verify vector search performance with pgvector

### Post-Migration Testing

1. **Unit Tests**: Run existing test suite to catch broken imports
2. **Integration Tests**: Test full RAG pipeline end-to-end
3. **API Testing**: Verify all endpoints respond correctly
4. **Frontend Testing**: Test UI functionality and document upload/search
5. **Railway Deployment Testing**: Deploy and test in production environment

### Validation Checklist

- [ ] Application starts without Weaviate connection errors
- [ ] Document ingestion works with PostgreSQL
- [ ] Vector search returns accurate results
- [ ] Chat functionality works end-to-end
- [ ] All API endpoints respond correctly
- [ ] Frontend UI functions normally
- [ ] No broken imports or missing dependencies
- [ ] Railway deployment succeeds
- [ ] Performance is comparable to Weaviate implementation

## Implementation Phases

### Phase 1: Code Dependency Removal
- Remove Weaviate imports and classes
- Update manager initialization logic
- Clean up embedding component references

### Phase 2: Configuration Cleanup
- Update Docker Compose configuration
- Clean environment variable files
- Update package dependencies

### Phase 3: Documentation Updates
- Update architecture documentation
- Revise setup instructions
- Update steering files

### Phase 4: Testing and Validation
- Test Railway deployment
- Validate all functionality
- Performance verification

### Phase 5: Final Cleanup
- Remove Weaviate service from Railway
- Clean up built frontend assets
- Final documentation review

## Risk Mitigation

### High-Risk Areas

1. **Manager Initialization**: Ensure proper fallback to SupabaseManager
2. **Frontend Assets**: Built files may need regeneration
3. **Environment Configuration**: Missing variables could break startup
4. **Railway Deployment**: Service dependencies must be updated

### Mitigation Strategies

1. **Incremental Testing**: Test after each major change
2. **Backup Strategy**: Keep Weaviate service until full validation
3. **Rollback Plan**: Document steps to restore Weaviate if needed
4. **Monitoring**: Watch Railway logs during deployment testing