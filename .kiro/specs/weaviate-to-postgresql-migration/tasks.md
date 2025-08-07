# Implementation Plan

- [ ] 1. Remove Weaviate embedding component and update imports
  - Delete `goldenverba/components/embedding/WeaviateEmbedder.py` file
  - Remove WeaviateEmbedder import from `goldenverba/components/embedding/__init__.py`
  - Clean up compiled Python cache files for WeaviateEmbedder
  - _Requirements: 1.1, 1.4_

- [ ] 2. Remove Weaviate manager class and imports from managers.py
  - Remove `import weaviate` and related Weaviate imports from `goldenverba/components/managers.py`
  - Remove `VerbaWeaviateManager` class definition and all its methods
  - Remove `WeaviateAsyncClient` and other Weaviate-specific imports
  - Update any remaining code that references the removed manager
  - _Requirements: 1.1, 1.4_

- [ ] 3. Update verba_manager_supabase.py to use only PostgreSQL
  - Remove conditional Weaviate manager import and initialization logic
  - Update database manager initialization to always use SupabaseManager
  - Remove any Weaviate-specific error handling or fallback logic
  - Update logging messages to reflect PostgreSQL-only operation
  - _Requirements: 1.1, 3.4_

- [ ] 4. Clean up migration script imports and references
  - Update `migration/migrate_weaviate_to_supabase.py` to handle missing Weaviate dependencies gracefully
  - Add error handling for cases where Weaviate client is not available
  - Ensure script can still be used for reference without breaking the application
  - _Requirements: 1.1, 2.5_

- [ ] 5. Update Docker Compose configuration
  - Remove Weaviate service definition from `docker-compose.yml`
  - Remove Weaviate-related environment variables from Verba service
  - Update service dependencies to remove Weaviate dependency
  - Remove Weaviate volume definition
  - _Requirements: 2.2, 2.3_

- [ ] 6. Clean up environment configuration files
  - Remove `WEAVIATE_URL_VERBA` and `WEAVIATE_API_KEY_VERBA` from `.env.example`
  - Add comments indicating PostgreSQL-only configuration
  - Ensure all required PostgreSQL environment variables are documented
  - _Requirements: 2.3, 3.1_

- [ ] 7. Update package dependencies in setup.py
  - Remove any Weaviate-related dependencies from install_requires
  - Remove weaviate-client from extras_require if present
  - Update package description to reflect PostgreSQL-only architecture
  - _Requirements: 1.2, 2.1_

- [ ] 8. Update requirements-supabase.txt dependencies
  - Move weaviate-client to a separate comment section for migration reference only
  - Ensure all PostgreSQL and Supabase dependencies are properly specified
  - Add comments explaining the purpose of each dependency group
  - _Requirements: 1.2, 2.1_

- [ ] 9. Update API endpoints to remove Weaviate references
  - Review `goldenverba/server/api.py` for any Weaviate-specific comments or logic
  - Update endpoint documentation strings to reflect PostgreSQL backend
  - Remove any Weaviate-specific error handling in API routes
  - _Requirements: 3.3, 4.2_

- [ ] 10. Create comprehensive test script for PostgreSQL functionality
  - Write test script to verify document ingestion with PostgreSQL
  - Add tests for vector search functionality using pgvector
  - Include tests for chat/RAG pipeline end-to-end functionality
  - Add API endpoint testing for all core features
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 11. Update documentation files to reflect PostgreSQL-only setup
  - Update `CLAUDE.md` to remove Weaviate references and update architecture description
  - Modify `.kiro/steering/product.md` to reflect PostgreSQL-only database support
  - Update `.kiro/steering/structure.md` to remove Weaviate from database abstraction description
  - Update `railway-postgres-setup.md` to remove Weaviate migration references
  - _Requirements: 2.4, 5.2_

- [ ] 12. Clean up built frontend assets
  - Remove all files in `goldenverba/server/frontend/out/_next/static/chunks/app/` directory
  - Rebuild frontend assets to ensure no Weaviate references remain in built code
  - Verify that rebuilt assets contain only PostgreSQL-related code
  - _Requirements: 1.1, 5.3_

- [ ] 13. Test Railway deployment with PostgreSQL-only configuration
  - Deploy application to Railway using updated configuration
  - Verify application starts successfully without Weaviate connection attempts
  - Test all API endpoints to ensure they work with PostgreSQL backend
  - Monitor application logs for any Weaviate-related errors
  - _Requirements: 4.1, 4.4_

- [ ] 14. Validate complete RAG pipeline functionality
  - Test document upload and processing with PostgreSQL backend
  - Verify vector embeddings are stored correctly in pgvector
  - Test search functionality returns accurate and relevant results
  - Validate chat interface works end-to-end with PostgreSQL
  - _Requirements: 4.2, 4.3, 6.1, 6.2, 6.3_

- [ ] 15. Perform final cleanup and verification
  - Run comprehensive import check to ensure no broken dependencies
  - Verify no dead code or unused Weaviate-related functions remain
  - Test application performance compared to previous Weaviate implementation
  - Document any performance differences or optimizations needed
  - _Requirements: 5.3, 5.4, 6.5_