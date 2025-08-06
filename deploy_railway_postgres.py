#!/usr/bin/env python3
"""
Deploy script for Railway PostgreSQL setup.
This will be executed on Railway with proper dependencies and networking.
"""

import os
import sys
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_railway_postgres():
    """Verify Railway PostgreSQL setup after deployment."""
    
    logger.info("🔍 Verifying Railway PostgreSQL setup...")
    
    # Check environment variables
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("❌ DATABASE_URL not found in environment")
        return False
    
    logger.info(f"✅ DATABASE_URL configured: {database_url.split('@')[0]}@***")
    
    try:
        # Import here to avoid issues if not deployed
        import asyncpg
        from pgvector.asyncpg import register_vector
        
        # Test connection
        conn = await asyncpg.connect(database_url)
        await register_vector(conn)
        
        # Verify pgvector
        pgvector_version = await conn.fetchval("""
            SELECT extversion FROM pg_extension WHERE extname = 'vector'
        """)
        
        if pgvector_version:
            logger.info(f"✅ pgvector v{pgvector_version} available")
        else:
            logger.info("📦 Installing pgvector extension...")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            pgvector_version = await conn.fetchval("""
                SELECT extversion FROM pg_extension WHERE extname = 'vector'
            """)
            logger.info(f"✅ pgvector v{pgvector_version} installed")
        
        # Test Railway PostgreSQL Manager
        logger.info("🧪 Testing Railway PostgreSQL Manager...")
        from goldenverba.components.railway_postgres_manager import RailwayPostgresManager
        
        manager = RailwayPostgresManager()
        await manager.initialize()
        logger.info("✅ Railway PostgreSQL Manager initialized")
        
        # Test configuration
        config_id = await manager.save_configuration(
            config_type="deployment",
            config_name="railway_postgres",
            config_data={
                "database": "postgresql",
                "provider": "railway",
                "pgvector_version": pgvector_version,
                "deployed_at": "2025-01-06"
            },
            set_active=True
        )
        logger.info(f"✅ Configuration saved: {config_id}")
        
        await manager.close()
        await conn.close()
        
        logger.info("🎉 Railway PostgreSQL setup verified successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Missing dependencies: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main verification function."""
    logger.info("🚀 Starting Railway PostgreSQL verification...")
    
    try:
        success = asyncio.run(verify_railway_postgres())
        if success:
            logger.info("✅ Railway PostgreSQL is ready for production!")
            return 0
        else:
            logger.error("❌ Railway PostgreSQL verification failed")
            return 1
    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())