#!/usr/bin/env python3
"""Verify Railway PostgreSQL setup and test connection."""

import asyncio


async def verify_railway_setup():
    """Verify Railway PostgreSQL is working."""

    print("🔍 Verifying Railway PostgreSQL setup...")

    # Check if we can import required modules
    try:
        import asyncpg
        from pgvector.asyncpg import register_vector

        print("✅ Required modules available")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Install with: pip install asyncpg pgvector")
        return False

    # Test connection with Railway internal URL
    database_url = "postgresql://postgres:mr3h5piqapfpuoy9qr9hnwliqfltazi5@pgvector.railway.internal:5432/railway"

    try:
        print("🔌 Testing connection to Railway PostgreSQL...")

        # This will fail locally but should work on Railway
        conn = await asyncpg.connect(database_url)
        await register_vector(conn)

        # Test basic query
        version = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL version: {version.split()[1]}")

        # Test pgvector
        pgvector_version = await conn.fetchval("""
            SELECT extversion FROM pg_extension WHERE extname = 'vector'
        """)

        if pgvector_version:
            print(f"✅ pgvector extension: v{pgvector_version}")
        else:
            print("⚠️ Installing pgvector extension...")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            pgvector_version = await conn.fetchval("""
                SELECT extversion FROM pg_extension WHERE extname = 'vector'
            """)
            print(f"✅ pgvector installed: v{pgvector_version}")

        # Test vector operations
        test_vector = [0.1, 0.2, 0.3]
        similarity = await conn.fetchval(
            """
            SELECT 1 - ($1::vector <=> $2::vector) as similarity
        """,
            test_vector,
            test_vector,
        )
        print(f"✅ Vector similarity test: {similarity}")

        await conn.close()
        print("🎉 Railway PostgreSQL verification complete!")
        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 This is expected when running locally")
        print("🚀 Will work when deployed on Railway platform")
        return False


async def test_railway_postgres_manager():
    """Test our Railway PostgreSQL manager."""
    try:
        from goldenverba.components.railway_postgres_manager import (
            RailwayPostgresManager,
        )

        print("🧪 Testing Railway PostgreSQL Manager...")
        manager = RailwayPostgresManager()
        await manager.initialize()

        # Save a test configuration
        config_id = await manager.save_configuration(
            config_type="test",
            config_name="railway_verification",
            config_data={"status": "verified", "timestamp": "2025-01-06"},
            set_active=True,
        )

        print(f"✅ Configuration saved: {config_id}")

        # Retrieve configuration
        config = await manager.get_configuration("test")
        if config:
            print(f"✅ Configuration retrieved: {config}")

        await manager.close()
        print("✅ Railway PostgreSQL Manager test passed!")
        return True

    except Exception as e:
        print(f"❌ Manager test failed: {e}")
        return False


async def main():
    """Main verification function."""
    print("🚀 Railway PostgreSQL Setup Verification")
    print("=" * 50)

    # Test 1: Basic connection
    connection_ok = await verify_railway_setup()

    # Test 2: Manager functionality
    manager_ok = await test_railway_postgres_manager()

    print("\n" + "=" * 50)
    if connection_ok and manager_ok:
        print("🎉 All tests passed! Railway PostgreSQL is ready!")
        print("\n📋 Next steps:")
        print("   1. ✅ PostgreSQL service configured")
        print("   2. ✅ Environment variables set")
        print("   3. ✅ Application deployed")
        print("   4. 🔄 Run data migration (if needed)")
        print("   5. 🗑️ Remove old Weaviate service")
    else:
        print("⚠️ Some tests failed - check configuration")

    return connection_ok and manager_ok


if __name__ == "__main__":
    exit(0 if asyncio.run(main()) else 1)
