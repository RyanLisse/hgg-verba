#!/usr/bin/env python3
"""
Test script to verify Weaviate connections for both local Docker and Railway deployments.
"""

import asyncio
import os
import sys
from urllib.parse import urlparse

# Add the goldenverba package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "goldenverba"))

try:
    import weaviate
    from weaviate.auth import AuthApiKey
    from weaviate.config import AdditionalConfig, Timeout
except ImportError:
    print(
        "❌ Weaviate client not installed. Please install with: pip install weaviate-client"
    )
    sys.exit(1)


class WeaviateConnectionTester:
    """Test Weaviate connections using the same logic as Verba."""

    def __init__(self):
        self.timeout_config = AdditionalConfig(
            timeout=Timeout(init=60, query=300, insert=300)
        )

    async def test_local_connection(self, url="http://localhost:8080"):
        """Test connection to local Docker Weaviate instance."""
        print(f"\n🔍 Testing Local Weaviate Connection: {url}")

        try:
            parsed = urlparse(url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 8080

            print(f"   Host: {host}, Port: {port}")

            client = weaviate.use_async_with_local(
                host=host,
                port=port,
                additional_config=self.timeout_config,
            )

            await client.connect()

            if await client.is_ready():
                print("✅ Local Weaviate connection successful!")

                # Get meta information
                meta = await client.get_meta()
                print(f"   Version: {meta.get('version', 'Unknown')}")
                print(f"   Modules: {len(meta.get('modules', {}))}")

                await client.close()
                return True
            else:
                print("❌ Local Weaviate client not ready")
                await client.close()
                return False

        except Exception as e:
            print(f"❌ Local Weaviate connection failed: {str(e)}")
            return False

    async def test_railway_connection(
        self, url="https://weaviate-production-9dce.up.railway.app", api_key=None
    ):
        """Test connection to Railway Weaviate instance."""
        print(f"\n🔍 Testing Railway Weaviate Connection: {url}")

        try:
            parsed = urlparse(url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            secure = parsed.scheme == "https"

            if not host:
                print("❌ Invalid URL - no hostname found")
                return False

            print(f"   Host: {host}, Port: {port}, Secure: {secure}")

            client = weaviate.connect_to_custom(
                http_host=host,
                http_port=port,
                http_secure=secure,
                grpc_host=host,
                grpc_port=50051,  # gRPC port (may not be available for Railway)
                grpc_secure=secure,
                skip_init_checks=True,  # Skip gRPC health checks for Railway
                additional_config=self.timeout_config,
            )

            client.connect()

            if client.is_ready():
                print("✅ Railway Weaviate connection successful!")

                # Get meta information
                meta = client.get_meta()
                print(f"   Version: {meta.get('version', 'Unknown')}")
                print(f"   Modules: {len(meta.get('modules', {}))}")

                client.close()
                return True
            else:
                print("❌ Railway Weaviate client not ready")
                client.close()
                return False

        except Exception as e:
            print(f"❌ Railway Weaviate connection failed: {str(e)}")
            return False

    async def test_both_connections(self):
        """Test both local and Railway connections."""
        print("🚀 Starting Weaviate Connection Tests")
        print("=" * 50)

        # Test local connection
        local_success = await self.test_local_connection()

        # Test Railway connection
        railway_success = await self.test_railway_connection()

        print("\n" + "=" * 50)
        print("📊 Connection Test Summary:")
        print(f"   Local Docker:  {'✅ Success' if local_success else '❌ Failed'}")
        print(f"   Railway:       {'✅ Success' if railway_success else '❌ Failed'}")

        if local_success and railway_success:
            print("\n🎉 Both connections are working! You can use either:")
            print("   • Local: Set WEAVIATE_URL_VERBA=http://localhost:8080")
            print(
                "   • Railway: Set WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app"
            )
        elif local_success:
            print(
                "\n✅ Local connection works. Use: WEAVIATE_URL_VERBA=http://localhost:8080"
            )
        elif railway_success:
            print(
                "\n✅ Railway connection works. Use: WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app"
            )
        else:
            print("\n❌ Both connections failed. Please check your setup.")

        return local_success, railway_success


async def main():
    """Main test function."""
    tester = WeaviateConnectionTester()
    await tester.test_both_connections()


if __name__ == "__main__":
    asyncio.run(main())
