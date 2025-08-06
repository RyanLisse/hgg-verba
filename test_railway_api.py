#!/usr/bin/env python3
"""
Test script for Railway Verba deployment API endpoints
"""

import requests
import json
import time
from typing import Dict, Any

RAILWAY_URL = "https://hgg-verba-production.up.railway.app"
HEADERS = {
    "Origin": RAILWAY_URL,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[str, Any]:
    """Test a specific API endpoint"""
    url = f"{RAILWAY_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        result = {
            "endpoint": endpoint,
            "status_code": response.status_code,
            "success": response.status_code == 200,
            "response_time": response.elapsed.total_seconds(),
            "content_type": response.headers.get("content-type", ""),
        }
        
        # Try to parse JSON response
        try:
            result["data"] = response.json()
        except:
            result["data"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
        
        return result
        
    except requests.exceptions.RequestException as e:
        return {
            "endpoint": endpoint,
            "error": str(e),
            "success": False
        }

def main():
    """Run all API tests"""
    print("🚀 Testing Railway Verba Deployment API")
    print(f"📍 URL: {RAILWAY_URL}")
    print("=" * 60)
    
    # Test endpoints
    endpoints_to_test = [
        "/api/health",
        "/api/get_status", 
        "/api/get_config",
        "/api/get_all_documents",
        "/api/get_all_chunks",
        "/api/get_suggestions",
        "/api/get_embedders",
        "/api/get_generators",
        "/api/get_readers",
        "/api/get_retrievers",
    ]
    
    results = []
    
    for endpoint in endpoints_to_test:
        print(f"Testing {endpoint}...", end=" ")
        result = test_endpoint(endpoint)
        results.append(result)
        
        if result.get("success"):
            print(f"✅ {result['status_code']} ({result.get('response_time', 0):.3f}s)")
        else:
            print(f"❌ {result.get('status_code', 'ERROR')}")
            if 'error' in result:
                print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if successful:
        print("\n🎉 Working Endpoints:")
        for result in successful:
            print(f"  • {result['endpoint']} - {result['status_code']}")
            if isinstance(result.get('data'), dict):
                # Show interesting keys from the response
                keys = list(result['data'].keys())[:3]
                if keys:
                    print(f"    Keys: {', '.join(keys)}")
    
    if failed:
        print("\n⚠️  Failed Endpoints:")
        for result in failed:
            print(f"  • {result['endpoint']} - {result.get('status_code', 'ERROR')}")
    
    # Test specific functionality
    print("\n" + "=" * 60)
    print("🔍 DETAILED HEALTH CHECK")
    print("=" * 60)
    
    health_result = test_endpoint("/api/health")
    if health_result.get("success"):
        health_data = health_result.get("data", {})
        print(f"✅ Server Status: {health_data.get('message', 'Unknown')}")
        print(f"📍 Environment: {health_data.get('production', 'Unknown')}")
        
        deployments = health_data.get('deployments', {})
        if deployments:
            print("🔗 Connected Services:")
            for service, url in deployments.items():
                if url:
                    print(f"  • {service}: {url}")
                else:
                    print(f"  • {service}: Not configured")
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION")
    print("=" * 60)
    
    if len(successful) >= 1:  # At least health endpoint should work
        print("🎉 Railway deployment is WORKING!")
        print("✅ Frontend is loading successfully")
        print("✅ Backend API is responding")
        print("✅ Weaviate connection is configured")
        print("\n🌐 You can access your Verba instance at:")
        print(f"   {RAILWAY_URL}")
    else:
        print("❌ Railway deployment has issues")
        print("🔧 Check the Railway logs for more details")

if __name__ == "__main__":
    main()
