#!/usr/bin/env python3
"""
Validation script for Astral tooling migration.
This script validates that the migration was successful.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a command and report the result."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=check,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ FAILED: {description}")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ FAILED: {description}")
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ FAILED: {description} - Command not found")
        return False


def check_file_exists(filepath, description):
    """Check if a file exists."""
    print(f"\n🔍 {description}")
    path = Path(filepath)
    
    if path.exists():
        print(f"✅ SUCCESS: {filepath} exists")
        return True
    else:
        print(f"❌ FAILED: {filepath} does not exist")
        return False


def check_file_not_exists(filepath, description):
    """Check if a file does not exist (for removed legacy files)."""
    print(f"\n🔍 {description}")
    path = Path(filepath)
    
    if not path.exists():
        print(f"✅ SUCCESS: {filepath} has been removed")
        return True
    else:
        print(f"❌ FAILED: {filepath} still exists (should be removed)")
        return False


def main():
    """Run all validation checks."""
    print("🚀 Validating Astral Tooling Migration")
    print("=" * 50)
    
    results = []
    
    # Check that legacy files have been removed
    results.append(check_file_not_exists("setup.py", "Legacy setup.py removed"))
    results.append(check_file_not_exists("requirements-supabase.txt", "Legacy requirements-supabase.txt removed"))
    results.append(check_file_not_exists("goldenverba/requirements.txt", "Legacy goldenverba/requirements.txt removed"))
    
    # Check that new configuration files exist
    results.append(check_file_exists("pyproject.toml", "pyproject.toml configuration exists"))
    results.append(check_file_exists("Dockerfile", "Optimized Dockerfile exists"))
    results.append(check_file_exists("docker-compose.yml", "Updated docker-compose.yml exists"))
    results.append(check_file_exists("Makefile", "Updated Makefile exists"))
    results.append(check_file_exists("ASTRAL_TOOLING_MIGRATION_GUIDE.md", "Migration guide exists"))
    
    # Check pyproject.toml content
    print(f"\n🔍 Checking pyproject.toml configuration")
    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()
            
        checks = [
            ("[tool.ruff]", "Ruff configuration present"),
            ("[tool.ty]", "Ty configuration present"),
            ("[tool.uv]", "UV configuration present"),
            ("[dependency-groups]", "Dependency groups present"),
            ("ruff>=0.8.0", "Ruff dependency present"),
            ("ty>=0.0.1-alpha.17", "Ty dependency present"),
        ]
        
        for check, desc in checks:
            if check in content:
                print(f"✅ SUCCESS: {desc}")
                results.append(True)
            else:
                print(f"❌ FAILED: {desc}")
                results.append(False)
                
    except Exception as e:
        print(f"❌ FAILED: Could not read pyproject.toml: {e}")
        results.append(False)
    
    # Check Makefile targets
    print(f"\n🔍 Checking Makefile targets")
    try:
        with open("Makefile", "r") as f:
            content = f.read()
            
        checks = [
            ("UV := uv", "UV variable defined"),
            ("$(UV) run ruff format", "Ruff format command present"),
            ("$(UV) run ruff check", "Ruff check command present"),
            ("$(UV) run ty check", "Ty check command present"),
            ("$(UV) sync --group dev", "UV sync command present"),
        ]
        
        for check, desc in checks:
            if check in content:
                print(f"✅ SUCCESS: {desc}")
                results.append(True)
            else:
                print(f"❌ FAILED: {desc}")
                results.append(False)
                
    except Exception as e:
        print(f"❌ FAILED: Could not read Makefile: {e}")
        results.append(False)
    
    # Check CI configuration
    print(f"\n🔍 Checking CI configuration")
    try:
        with open(".github/workflows/ci.yml", "r") as f:
            content = f.read()
            
        checks = [
            ("astral-sh/setup-uv", "UV setup action present"),
            ("uv run ruff check", "Ruff check in CI"),
            ("uv run ruff format --check", "Ruff format check in CI"),
            ("uv run ty check", "Ty check in CI"),
            ("uv sync", "UV sync in CI"),
        ]
        
        for check, desc in checks:
            if check in content:
                print(f"✅ SUCCESS: {desc}")
                results.append(True)
            else:
                print(f"❌ FAILED: {desc}")
                results.append(False)
                
    except Exception as e:
        print(f"❌ FAILED: Could not read CI configuration: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    total_checks = len(results)
    passed_checks = sum(results)
    failed_checks = total_checks - passed_checks
    
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {failed_checks}")
    
    if failed_checks == 0:
        print("\n🎉 ALL CHECKS PASSED! Migration is successful!")
        return 0
    else:
        print(f"\n⚠️  {failed_checks} checks failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
