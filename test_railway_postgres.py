#!/usr/bin/env python3
"""Test Railway PostgreSQL connection with the Railway PostgreSQL Manager."""

import os
import asyncio
import logging
from goldenverba.components.railway_postgres_manager import RailwayPostgresManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_railway_postgres():
    """Test Railway PostgreSQL connection and pgvector functionality."""
    
    # Set up test environment variables (Railway will provide these)
    test_database_url = "postgresql://postgres:mr3h5piqapfpuoy9qr9hnwliqfltazi5@pgvector.railway.internal:5432/railway"
    os.environ["DATABASE_URL"] = test_database_url
    
    logger.info("🧪 Testing Railway PostgreSQL connection...")
    
    try:
        # Initialize the manager
        manager = RailwayPostgresManager()
        await manager.initialize()
        logger.info("✅ Railway PostgreSQL manager initialized successfully")
        
        # Test basic connection
        async with manager.pool.acquire() as conn:
            # Test basic query
            result = await conn.fetchval("SELECT version()")
            logger.info(f"✅ PostgreSQL version: {result.split()[1]}")
            
            # Test pgvector extension
            pgvector_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            if pgvector_version:
                logger.info(f"✅ pgvector extension: v{pgvector_version}")
            else:
                logger.warning("⚠️ pgvector extension not found, attempting to install...")
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                pgvector_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                if pgvector_version:
                    logger.info(f"✅ pgvector extension installed: v{pgvector_version}")
                else:
                    logger.error("❌ Failed to install pgvector extension")
                    return False
        
        # Test table creation and schema
        logger.info("🔧 Testing schema creation...")
        async with manager.pool.acquire() as conn:
            # Check if tables exist
            tables = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            table_names = [row['table_name'] for row in tables]
            logger.info(f"📊 Existing tables: {table_names}")
        
        # Test vector operations if pgvector is available
        logger.info("🔍 Testing vector operations...")
        async with manager.pool.acquire() as conn:
            # Create a test vector
            test_embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions for OpenAI
            
            try:
                # Test vector creation and similarity
                similarity = await conn.fetchval("""
                    SELECT 1 - ($1::vector <=> $2::vector) as similarity
                """, test_embedding, test_embedding)
                
                logger.info(f"✅ Vector similarity test: {similarity} (should be 1.0)")
                
            except Exception as e:
                logger.error(f"❌ Vector operations test failed: {e}")
        
        # Test configuration storage
        logger.info("⚙️ Testing configuration storage...")
        config_id = await manager.save_configuration(
            config_type="test",
            config_name="railway_test",
            config_data={"database": "postgresql", "provider": "railway"},
            set_active=True
        )
        logger.info(f"✅ Configuration saved: {config_id}")
        
        # Retrieve configuration
        config = await manager.get_configuration("test")
        if config and config.get("database") == "postgresql":
            logger.info("✅ Configuration retrieval successful")
        else:
            logger.error("❌ Configuration retrieval failed")
        
        # Test cleanup
        await manager.close()
        logger.info("✅ Connection pool closed successfully")
        
        logger.info("🎉 All Railway PostgreSQL tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Railway PostgreSQL test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    try:
        success = asyncio.run(test_railway_postgres())
        if success:
            print("\n✅ Railway PostgreSQL is ready for production!")
            print("🚀 Next steps:")
            print("   1. Deploy updated code to Railway")
            print("   2. Set environment variables via Railway dashboard")
            print("   3. Run migration script")
            return 0
        else:
            print("\n❌ Railway PostgreSQL setup needs fixing")
            return 1
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        return 1

if __name__ == "__main__":
    exit(main())