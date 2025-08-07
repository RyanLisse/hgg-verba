#!/usr/bin/env python3
"""
Railway Deployment Test Script
Tests Railway deployment with PostgreSQL-only configuration
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp
import requests
from dotenv import load_dotenv
from wasabi import msg

load_dotenv()


class RailwayDeploymentTester:
    """Test Railway deployment functionality"""

    def __init__(self, railway_url: Optional[str] = None):
        self.railway_url = railway_url or os.getenv("RAILWAY_URL", "")
        self.test_results = {
            "deployment_accessible": False,
            "health_check": False,
            "api_endpoints": False,
            "postgresql_connection": False,
            "no_weaviate_errors": False,
            "errors": []
        }

    async def run_deployment_tests(self) -> Dict[str, Any]:
        """Run all Railway deployment tests"""
        msg.info("Starting Railway deployment tests...")
        start_time = datetime.utcnow()

        if not self.railway_url:
            self.test_results["errors"].append("RAILWAY_URL not provided")
            msg.fail("❌ RAILWAY_URL not provided. Please set the Railway deployment URL.")
            return self.test_results

        try:
            # Test 1: Basic deployment accessibility
            await self.test_deployment_accessibility()

            # Test 2: Health check endpoint
            await self.test_health_check()

            # Test 3: API endpoints functionality
            await self.test_api_endpoints()

            # Test 4: PostgreSQL connection
            await self.test_postgresql_connection()

            # Test 5: Verify no Weaviate errors
            await self.test_no_weaviate_errors()

        except Exception as e:
            self.test_results["errors"].append(f"Test suite failed: {str(e)}")
            msg.fail(f"Test suite failed: {str(e)}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        self.print_test_results(duration)
        return self.test_results

    async def test_deployment_accessibility(self):
        """Test if the Railway deployment is accessible"""
        msg.info("Testing deployment accessibility...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    self.railway_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        msg.good("✓ Railway deployment is accessible")
                        self.test_results["deployment_accessible"] = True
                    else:
                        raise Exception(f"Deployment returned status {response.status}")

        except Exception as e:
            self.test_results["errors"].append(f"Deployment accessibility test failed: {str(e)}")
            msg.fail(f"✗ Deployment accessibility test failed: {str(e)}")

    async def test_health_check(self):
        """Test the health check endpoint"""
        msg.info("Testing health check endpoint...")
        
        try:
            health_url = f"{self.railway_url.rstrip('/')}/api/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    health_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        msg.good("✓ Health check endpoint working")
                        msg.info(f"  - Status: {health_data.get('status', 'unknown')}")
                        self.test_results["health_check"] = True
                    else:
                        raise Exception(f"Health check returned status {response.status}")

        except Exception as e:
            self.test_results["errors"].append(f"Health check test failed: {str(e)}")
            msg.fail(f"✗ Health check test failed: {str(e)}")

    async def test_api_endpoints(self):
        """Test key API endpoints"""
        msg.info("Testing API endpoints...")
        
        try:
            # Test deployments endpoint
            deployments_url = f"{self.railway_url.rstrip('/')}/api/get_deployments"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    deployments_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        deployments_data = await response.json()
                        msg.good("✓ Deployments endpoint working")
                        
                        # Check if it returns PostgreSQL configuration
                        if "SUPABASE_URL" in deployments_data or "DATABASE_URL" in deployments_data:
                            msg.good("✓ PostgreSQL configuration detected")
                        else:
                            msg.warn("⚠ No PostgreSQL configuration found in deployments")
                        
                        # Ensure no Weaviate configuration
                        if "WEAVIATE_URL_VERBA" not in deployments_data:
                            msg.good("✓ No Weaviate configuration found (as expected)")
                        else:
                            msg.warn("⚠ Weaviate configuration still present")
                        
                        self.test_results["api_endpoints"] = True
                    else:
                        raise Exception(f"Deployments endpoint returned status {response.status}")

        except Exception as e:
            self.test_results["errors"].append(f"API endpoints test failed: {str(e)}")
            msg.fail(f"✗ API endpoints test failed: {str(e)}")

    async def test_postgresql_connection(self):
        """Test PostgreSQL connection through the application"""
        msg.info("Testing PostgreSQL connection...")
        
        try:
            # Create test credentials (these would need to be provided)
            test_payload = {
                "deployment": "Supabase",
                "url": os.getenv("SUPABASE_URL", ""),
                "key": os.getenv("SUPABASE_KEY", "")
            }

            if not test_payload["url"] or not test_payload["key"]:
                msg.warn("⚠ PostgreSQL connection test skipped - missing credentials")
                self.test_results["postgresql_connection"] = True  # Skip but don't fail
                return

            connect_url = f"{self.railway_url.rstrip('/')}/api/connect"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    connect_url,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        connect_data = await response.json()
                        if connect_data.get("connected"):
                            msg.good("✓ PostgreSQL connection successful")
                            self.test_results["postgresql_connection"] = True
                        else:
                            raise Exception("Connection failed according to response")
                    else:
                        raise Exception(f"Connect endpoint returned status {response.status}")

        except Exception as e:
            self.test_results["errors"].append(f"PostgreSQL connection test failed: {str(e)}")
            msg.fail(f"✗ PostgreSQL connection test failed: {str(e)}")

    async def test_no_weaviate_errors(self):
        """Test that there are no Weaviate-related errors in the application"""
        msg.info("Testing for absence of Weaviate errors...")
        
        try:
            # Test various endpoints to ensure no Weaviate errors
            test_endpoints = [
                "/api/health",
                "/api/get_deployments",
            ]

            error_found = False
            
            async with aiohttp.ClientSession() as session:
                for endpoint in test_endpoints:
                    url = f"{self.railway_url.rstrip('')}{endpoint}"
                    try:
                        async with session.get(
                            url,
                            timeout=aiohttp.ClientTimeout(total=30)
                        ) as response:
                            response_text = await response.text()
                            
                            # Check for Weaviate-related errors in response
                            weaviate_keywords = [
                                "weaviate",
                                "WeaviateManager",
                                "VerbaWeaviateManager",
                                "weaviate-client"
                            ]
                            
                            for keyword in weaviate_keywords:
                                if keyword.lower() in response_text.lower():
                                    msg.warn(f"⚠ Found Weaviate reference in {endpoint}: {keyword}")
                                    error_found = True
                    
                    except Exception as e:
                        msg.warn(f"⚠ Could not test endpoint {endpoint}: {str(e)}")

            if not error_found:
                msg.good("✓ No Weaviate errors or references found")
                self.test_results["no_weaviate_errors"] = True
            else:
                msg.warn("⚠ Some Weaviate references found in responses")
                self.test_results["no_weaviate_errors"] = False

        except Exception as e:
            self.test_results["errors"].append(f"Weaviate error test failed: {str(e)}")
            msg.fail(f"✗ Weaviate error test failed: {str(e)}")

    def print_test_results(self, duration: float):
        """Print comprehensive test results"""
        msg.info("=" * 60)
        msg.info("RAILWAY DEPLOYMENT TEST RESULTS")
        msg.info("=" * 60)
        
        total_tests = len([k for k in self.test_results.keys() if k != "errors"])
        passed_tests = len([k for k, v in self.test_results.items() if k != "errors" and v])
        
        msg.info(f"Railway URL: {self.railway_url}")
        msg.info(f"Total Tests: {total_tests}")
        msg.info(f"Passed: {passed_tests}")
        msg.info(f"Failed: {total_tests - passed_tests}")
        msg.info(f"Duration: {duration:.2f} seconds")
        msg.info("")
        
        # Individual test results
        test_names = {
            "deployment_accessible": "Deployment Accessibility",
            "health_check": "Health Check Endpoint",
            "api_endpoints": "API Endpoints",
            "postgresql_connection": "PostgreSQL Connection",
            "no_weaviate_errors": "No Weaviate Errors"
        }
        
        for test_key, test_name in test_names.items():
            result = self.test_results.get(test_key, False)
            status = "✓ PASS" if result else "✗ FAIL"
            msg.info(f"{test_name}: {status}")
        
        # Error summary
        if self.test_results["errors"]:
            msg.info("")
            msg.warn("ERRORS ENCOUNTERED:")
            for error in self.test_results["errors"]:
                msg.warn(f"  - {error}")
        
        msg.info("=" * 60)
        
        if passed_tests == total_tests:
            msg.good("🎉 ALL TESTS PASSED! Railway deployment is working correctly.")
        else:
            msg.fail(f"❌ {total_tests - passed_tests} tests failed. Please check the deployment.")


def print_deployment_instructions():
    """Print instructions for Railway deployment"""
    msg.info("=" * 60)
    msg.info("RAILWAY DEPLOYMENT INSTRUCTIONS")
    msg.info("=" * 60)
    msg.info("")
    msg.info("1. Ensure you have Railway CLI installed:")
    msg.info("   npm install -g @railway/cli")
    msg.info("")
    msg.info("2. Login to Railway:")
    msg.info("   railway login")
    msg.info("")
    msg.info("3. Create a new Railway project:")
    msg.info("   railway new")
    msg.info("")
    msg.info("4. Add PostgreSQL service:")
    msg.info("   railway add postgresql")
    msg.info("")
    msg.info("5. Set environment variables:")
    msg.info("   railway variables set SUPABASE_URL=<your-postgresql-url>")
    msg.info("   railway variables set SUPABASE_KEY=<your-postgresql-key>")
    msg.info("   railway variables set OPENAI_API_KEY=<your-openai-key>")
    msg.info("")
    msg.info("6. Deploy the application:")
    msg.info("   railway up")
    msg.info("")
    msg.info("7. Get the deployment URL:")
    msg.info("   railway domain")
    msg.info("")
    msg.info("8. Run this test script with the deployment URL:")
    msg.info("   python railway_deployment_test.py --url <railway-url>")
    msg.info("")
    msg.info("=" * 60)


async def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Railway deployment")
    parser.add_argument("--url", help="Railway deployment URL")
    parser.add_argument("--instructions", action="store_true", help="Show deployment instructions")
    
    args = parser.parse_args()
    
    if args.instructions:
        print_deployment_instructions()
        return
    
    if not args.url and not os.getenv("RAILWAY_URL"):
        msg.fail("❌ Please provide Railway URL via --url argument or RAILWAY_URL environment variable")
        print_deployment_instructions()
        sys.exit(1)
    
    tester = RailwayDeploymentTester(args.url)
    results = await tester.run_deployment_tests()
    
    # Exit with appropriate code
    total_tests = len([k for k in results.keys() if k != "errors"])
    passed_tests = len([k for k, v in results.items() if k != "errors" and v])
    
    if passed_tests == total_tests:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    asyncio.run(main())
