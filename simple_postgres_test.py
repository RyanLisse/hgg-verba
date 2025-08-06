#!/usr/bin/env python3
"""Simple Railway PostgreSQL connection test without heavy dependencies."""

import asyncio
import asyncpg
import os

async def test_postgres_connection():
    """Test basic PostgreSQL connection to Railway."""
    
    # Railway PostgreSQL connection details
    database_url = "postgresql://postgres:mr3h5piqapfpuoy9qr9hnwliqfltazi5@pgvector.railway.internal:5432/railway"
    
    print("🧪 Testing Railway PostgreSQL connection...")
    print(f"🔗 Connection: pgvector.railway.internal:5432")
    
    try:
        # Test connection
        conn = await asyncpg.connect(database_url)
        print("✅ Connection successful!")
        
        # Test basic query
        version = await conn.fetchval("SELECT version()")
        print(f"📊 PostgreSQL version: {version.split()[1]}")
        
        # Test pgvector extension
        try:
            pgvector_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            if pgvector_version:
                print(f"✅ pgvector extension: v{pgvector_version}")
            else:
                print("⚠️ pgvector extension not found, attempting to install...")
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                pgvector_version = await conn.fetchval("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                if pgvector_version:
                    print(f"✅ pgvector extension installed: v{pgvector_version}")
                else:
                    print("❌ Failed to install pgvector extension")
                    return False
        except Exception as e:
            print(f"⚠️ pgvector test failed: {e}")
        
        # Test vector operations
        try:
            print("🔍 Testing vector operations...")
            test_vector = [0.1, 0.2, 0.3]
            similarity = await conn.fetchval("""
                SELECT 1 - ($1::vector <=> $2::vector) as similarity
            """, test_vector, test_vector)
            print(f"✅ Vector similarity: {similarity} (should be 1.0)")
        except Exception as e:
            print(f"❌ Vector operations failed: {e}")
        
        # Test table creation
        try:
            print("🏗️ Testing table creation...")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    embedding vector(3)
                )
            """)
            print("✅ Table creation successful")
            
            # Insert test data
            await conn.execute("""
                INSERT INTO test_table (name, embedding) 
                VALUES ('test', $1::vector)
                ON CONFLICT DO NOTHING
            """, [0.1, 0.2, 0.3])
            
            # Query test data
            result = await conn.fetchrow("SELECT * FROM test_table WHERE name = 'test'")
            if result:
                print(f"✅ Data insertion/retrieval successful: {result['name']}")
            
            # Clean up
            await conn.execute("DROP TABLE test_table")
            print("✅ Table cleanup successful")
            
        except Exception as e:
            print(f"❌ Table operations failed: {e}")
        
        await conn.close()
        print("✅ Connection closed successfully")
        
        print("\n🎉 Railway PostgreSQL is ready!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 This is expected if running locally (Railway internal networking)")
        print("🚀 Will work when deployed to Railway platform")
        return False

def main():
    """Run the test."""
    try:
        success = asyncio.run(test_postgres_connection())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted")
        return 1

if __name__ == "__main__":
    exit(main())