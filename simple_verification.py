#!/usr/bin/env python3
"""
Simple Migration Verification Script
Basic checks without external dependencies
"""

import os
import sys
from pathlib import Path


def check_weaviate_references():
    """Check for remaining Weaviate references"""
    print("🔍 Checking for Weaviate references...")
    
    project_root = Path(__file__).parent
    files_to_check = [
        "goldenverba/server/api.py",
        "goldenverba/verba_manager_supabase.py", 
        "goldenverba/components/managers.py",
        ".env.example",
        "docker-compose.yml"
    ]
    
    weaviate_refs = []
    
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            continue
            
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'weaviate' in line.lower():
                    # Skip comments about removal/migration
                    if any(keyword in line.lower() for keyword in [
                        'removed', 'migrated', 'deprecated', 'no longer', 
                        'migration', 'reference only', 'kept for reference'
                    ]):
                        continue
                    
                    weaviate_refs.append({
                        'file': file_path,
                        'line': i,
                        'content': line.strip()
                    })
        except Exception as e:
            print(f"  ⚠️  Could not check {file_path}: {str(e)}")
    
    if not weaviate_refs:
        print("  ✅ No problematic Weaviate references found")
        return True
    else:
        print(f"  ❌ Found {len(weaviate_refs)} Weaviate references:")
        for ref in weaviate_refs[:5]:  # Show first 5
            print(f"    - {ref['file']}:{ref['line']}")
        return False


def check_imports():
    """Check critical imports"""
    print("🔍 Checking critical imports...")
    
    critical_imports = [
        "goldenverba.unified_verba_manager",
        "goldenverba.server.api",
        "goldenverba.components.managers",
    ]
    
    failed_imports = []
    
    for import_name in critical_imports:
        try:
            __import__(import_name)
            print(f"  ✅ {import_name}")
        except ImportError as e:
            failed_imports.append(f"{import_name}: {str(e)}")
            print(f"  ❌ {import_name}: {str(e)}")
    
    if not failed_imports:
        print("  ✅ All critical imports working")
        return True
    else:
        print(f"  ❌ {len(failed_imports)} import failures")
        return False


def check_configuration():
    """Check configuration files"""
    print("🔍 Checking configuration files...")
    
    # Check .env.example
    env_example_path = Path(".env.example")
    if env_example_path.exists():
        with open(env_example_path, 'r') as f:
            content = f.read()
        
        has_postgres = "DATABASE_URL" in content or "POSTGRES_HOST" in content
        has_weaviate = "WEAVIATE_URL_VERBA" in content
        has_supabase = "SUPABASE_URL" in content

        if has_postgres and not has_weaviate and not has_supabase:
            print("  ✅ Environment configuration properly updated to pure PostgreSQL")
        elif has_weaviate:
            print("  ⚠️  Weaviate environment variables still present")
        elif has_supabase:
            print("  ⚠️  Supabase environment variables still present")
        else:
            print("  ⚠️  Missing PostgreSQL environment variables")
    else:
        print("  ⚠️  .env.example not found")
    
    # Check docker-compose.yml
    docker_compose_path = Path("docker-compose.yml")
    if docker_compose_path.exists():
        with open(docker_compose_path, 'r') as f:
            content = f.read()
        
        has_weaviate_service = "weaviate:" in content.lower()
        has_postgres_config = "DATABASE_URL" in content
        has_supabase_config = "SUPABASE" in content

        if not has_weaviate_service and not has_supabase_config and has_postgres_config:
            print("  ✅ Docker Compose properly updated (pure PostgreSQL)")
            return True
        elif has_weaviate_service:
            print("  ❌ Weaviate service still present in Docker Compose")
            return False
        elif has_supabase_config:
            print("  ⚠️  Supabase references still present in Docker Compose")
            return True  # Not a failure, just a warning
        else:
            print("  ⚠️  Missing PostgreSQL configuration")
            return True
    else:
        print("  ⚠️  docker-compose.yml not found")
        return True


def check_dependencies():
    """Check pyproject.toml dependencies"""
    print("🔍 Checking dependencies...")
    
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Check for required PostgreSQL dependencies
        required_deps = ["asyncpg", "pgvector", "psycopg2-binary", "sqlalchemy"]
        missing_deps = []
        
        for dep in required_deps:
            if dep not in content:
                missing_deps.append(dep)
        
        if not missing_deps:
            print("  ✅ All required PostgreSQL dependencies present")
            return True
        else:
            print(f"  ❌ Missing dependencies: {', '.join(missing_deps)}")
            return False
    else:
        print("  ❌ pyproject.toml not found")
        return False


def main():
    """Run simple verification"""
    print("=" * 60)
    print("SIMPLE MIGRATION VERIFICATION")
    print("=" * 60)
    
    checks = [
        ("Weaviate References", check_weaviate_references),
        ("Critical Imports", check_imports),
        ("Configuration", check_configuration),
        ("Dependencies", check_dependencies)
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"  ❌ Check failed: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 ALL CHECKS PASSED! Migration verification successful!")
        return 0
    else:
        print(f"❌ {total - passed} checks failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
