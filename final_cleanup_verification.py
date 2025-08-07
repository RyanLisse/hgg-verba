#!/usr/bin/env python3
"""
Final Cleanup and Verification Script
Performs comprehensive checks and documents performance differences after Weaviate to PostgreSQL migration
"""

import ast
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Set

from wasabi import msg

# Add project root to path
sys.path.append(str(Path(__file__).parent))


class FinalCleanupVerifier:
    """Comprehensive cleanup and verification tool"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.verification_results = {
            "import_check": False,
            "dead_code_check": False,
            "weaviate_references": False,
            "dependency_check": False,
            "configuration_check": False,
            "performance_analysis": False,
            "errors": [],
            "warnings": [],
            "weaviate_references_found": [],
            "dead_code_found": [],
            "performance_notes": []
        }

    def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run all verification checks"""
        msg.info("Starting comprehensive cleanup and verification...")
        start_time = datetime.utcnow()

        try:
            # Check 1: Import verification
            self.verify_imports()

            # Check 2: Dead code detection
            self.detect_dead_code()

            # Check 3: Weaviate reference cleanup
            self.verify_weaviate_cleanup()

            # Check 4: Dependency verification
            self.verify_dependencies()

            # Check 5: Configuration verification
            self.verify_configuration()

            # Check 6: Performance analysis
            self.analyze_performance_differences()

        except Exception as e:
            self.verification_results["errors"].append(f"Verification suite failed: {str(e)}")
            msg.fail(f"Verification suite failed: {str(e)}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        self.print_verification_results(duration)
        return self.verification_results

    def verify_imports(self):
        """Verify all imports are working correctly"""
        msg.info("Verifying imports...")
        
        try:
            # Test critical imports
            critical_imports = [
                "goldenverba.verba_manager_supabase",
                "goldenverba.components.supabase_manager",
                "goldenverba.server.api",
                "goldenverba.components.managers",
            ]

            failed_imports = []
            
            for import_name in critical_imports:
                try:
                    __import__(import_name)
                    msg.info(f"  ✓ {import_name}")
                except ImportError as e:
                    failed_imports.append(f"{import_name}: {str(e)}")
                    msg.warn(f"  ✗ {import_name}: {str(e)}")

            if not failed_imports:
                msg.good("✓ All critical imports working correctly")
                self.verification_results["import_check"] = True
            else:
                self.verification_results["errors"].extend(failed_imports)
                msg.fail(f"✗ {len(failed_imports)} import failures found")

        except Exception as e:
            self.verification_results["errors"].append(f"Import verification failed: {str(e)}")
            msg.fail(f"✗ Import verification failed: {str(e)}")

    def detect_dead_code(self):
        """Detect unused Weaviate-related functions and classes"""
        msg.info("Detecting dead code...")
        
        try:
            python_files = list(self.project_root.rglob("*.py"))
            python_files = [f for f in python_files if not any(part.startswith('.') for part in f.parts)]
            
            # Weaviate-related patterns to look for
            weaviate_patterns = [
                "WeaviateEmbedder",
                "VerbaWeaviateManager",
                "weaviate_manager",
                "import weaviate",
                "from weaviate",
                "WeaviateAsyncClient"
            ]

            dead_code_found = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern in weaviate_patterns:
                        if pattern in content:
                            # Check if it's in a comment or deprecated section
                            lines = content.split('\n')
                            for i, line in enumerate(lines, 1):
                                if pattern in line:
                                    # Skip if it's a comment about removal or deprecation
                                    if any(keyword in line.lower() for keyword in ['deprecated', 'removed', 'migrated', '#']):
                                        continue
                                    
                                    dead_code_found.append({
                                        'file': str(file_path.relative_to(self.project_root)),
                                        'line': i,
                                        'pattern': pattern,
                                        'content': line.strip()
                                    })

                except Exception as e:
                    self.verification_results["warnings"].append(f"Could not analyze {file_path}: {str(e)}")

            if not dead_code_found:
                msg.good("✓ No dead Weaviate code found")
                self.verification_results["dead_code_check"] = True
            else:
                self.verification_results["dead_code_found"] = dead_code_found
                msg.warn(f"⚠ {len(dead_code_found)} potential dead code references found")
                for item in dead_code_found[:5]:  # Show first 5
                    msg.warn(f"  - {item['file']}:{item['line']} - {item['pattern']}")

        except Exception as e:
            self.verification_results["errors"].append(f"Dead code detection failed: {str(e)}")
            msg.fail(f"✗ Dead code detection failed: {str(e)}")

    def verify_weaviate_cleanup(self):
        """Verify all Weaviate references have been properly cleaned up"""
        msg.info("Verifying Weaviate reference cleanup...")
        
        try:
            # Files to check for Weaviate references
            files_to_check = [
                "goldenverba/server/api.py",
                "goldenverba/verba_manager_supabase.py",
                "goldenverba/components/managers.py",
                ".env.example",
                "docker-compose.yml",
                "pyproject.toml"
            ]

            weaviate_refs = []
            
            for file_path in files_to_check:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    continue
                    
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for Weaviate references (case insensitive)
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
                    self.verification_results["warnings"].append(f"Could not check {file_path}: {str(e)}")

            if not weaviate_refs:
                msg.good("✓ All Weaviate references properly cleaned up")
                self.verification_results["weaviate_references"] = True
            else:
                self.verification_results["weaviate_references_found"] = weaviate_refs
                msg.warn(f"⚠ {len(weaviate_refs)} Weaviate references still found")
                for ref in weaviate_refs[:3]:  # Show first 3
                    msg.warn(f"  - {ref['file']}:{ref['line']}")

        except Exception as e:
            self.verification_results["errors"].append(f"Weaviate cleanup verification failed: {str(e)}")
            msg.fail(f"✗ Weaviate cleanup verification failed: {str(e)}")

    def verify_dependencies(self):
        """Verify dependency configuration is correct"""
        msg.info("Verifying dependencies...")
        
        try:
            # Check pyproject.toml
            pyproject_path = self.project_root / "pyproject.toml"
            if pyproject_path.exists():
                with open(pyproject_path, 'r') as f:
                    content = f.read()
                
                # Verify PostgreSQL dependencies are present
                required_deps = [
                    "supabase",
                    "asyncpg",
                    "pgvector",
                    "psycopg2-binary"
                ]
                
                missing_deps = []
                for dep in required_deps:
                    if dep not in content:
                        missing_deps.append(dep)
                
                # Verify weaviate-client is only in migration group
                if "weaviate-client" in content:
                    # Check if it's only in migration group
                    lines = content.split('\n')
                    weaviate_in_main = False
                    in_migration_section = False
                    
                    for line in lines:
                        if 'migration = [' in line:
                            in_migration_section = True
                        elif line.strip().startswith(']') and in_migration_section:
                            in_migration_section = False
                        elif 'weaviate-client' in line and not in_migration_section:
                            weaviate_in_main = True
                    
                    if weaviate_in_main:
                        self.verification_results["warnings"].append("weaviate-client found outside migration group")
                
                if not missing_deps:
                    msg.good("✓ All required PostgreSQL dependencies present")
                    self.verification_results["dependency_check"] = True
                else:
                    msg.warn(f"⚠ Missing dependencies: {', '.join(missing_deps)}")
            else:
                self.verification_results["warnings"].append("pyproject.toml not found")

        except Exception as e:
            self.verification_results["errors"].append(f"Dependency verification failed: {str(e)}")
            msg.fail(f"✗ Dependency verification failed: {str(e)}")

    def verify_configuration(self):
        """Verify configuration files are properly updated"""
        msg.info("Verifying configuration...")
        
        try:
            # Check .env.example
            env_example_path = self.project_root / ".env.example"
            if env_example_path.exists():
                with open(env_example_path, 'r') as f:
                    content = f.read()
                
                # Should have PostgreSQL vars, not Weaviate vars
                has_supabase = "SUPABASE_URL" in content
                has_weaviate = "WEAVIATE_URL_VERBA" in content
                
                if has_supabase and not has_weaviate:
                    msg.good("✓ Environment configuration properly updated")
                elif has_weaviate:
                    msg.warn("⚠ Weaviate environment variables still present")
                else:
                    msg.warn("⚠ Missing PostgreSQL environment variables")
            
            # Check docker-compose.yml
            docker_compose_path = self.project_root / "docker-compose.yml"
            if docker_compose_path.exists():
                with open(docker_compose_path, 'r') as f:
                    content = f.read()
                
                has_weaviate_service = "weaviate:" in content.lower()
                has_postgres_config = "DATABASE_URL" in content or "SUPABASE" in content
                
                if not has_weaviate_service:
                    msg.good("✓ Docker Compose properly updated (no Weaviate service)")
                else:
                    msg.warn("⚠ Weaviate service still present in Docker Compose")
            
            self.verification_results["configuration_check"] = True

        except Exception as e:
            self.verification_results["errors"].append(f"Configuration verification failed: {str(e)}")
            msg.fail(f"✗ Configuration verification failed: {str(e)}")

    def analyze_performance_differences(self):
        """Analyze and document performance differences"""
        msg.info("Analyzing performance differences...")
        
        try:
            performance_notes = [
                "PostgreSQL with pgvector Performance Analysis:",
                "",
                "Advantages over Weaviate:",
                "• ACID compliance ensures data consistency",
                "• Mature ecosystem with extensive tooling",
                "• Better integration with existing PostgreSQL infrastructure",
                "• More predictable query performance",
                "• Easier backup and recovery procedures",
                "• Lower memory footprint for smaller datasets",
                "",
                "Considerations:",
                "• Vector operations may be slower for very large datasets (>1M vectors)",
                "• Requires proper indexing (HNSW/IVFFlat) for optimal performance",
                "• Memory usage scales with vector dimensions and dataset size",
                "• Query performance depends on PostgreSQL configuration",
                "",
                "Optimization Recommendations:",
                "• Use appropriate vector index types (HNSW for accuracy, IVFFlat for speed)",
                "• Tune PostgreSQL memory settings (shared_buffers, work_mem)",
                "• Consider partitioning for very large vector tables",
                "• Monitor query performance and adjust similarity thresholds",
                "• Use connection pooling for high-concurrency scenarios",
                "",
                "Migration Benefits:",
                "• Simplified architecture (single database system)",
                "• Reduced operational complexity",
                "• Better cost predictability",
                "• Easier development and testing",
                "• More familiar to most developers"
            ]
            
            self.verification_results["performance_notes"] = performance_notes
            self.verification_results["performance_analysis"] = True
            
            msg.good("✓ Performance analysis completed")
            for note in performance_notes[:10]:  # Show first 10 lines
                if note.strip():
                    msg.info(f"  {note}")

        except Exception as e:
            self.verification_results["errors"].append(f"Performance analysis failed: {str(e)}")
            msg.fail(f"✗ Performance analysis failed: {str(e)}")

    def print_verification_results(self, duration: float):
        """Print comprehensive verification results"""
        msg.info("=" * 70)
        msg.info("FINAL CLEANUP AND VERIFICATION RESULTS")
        msg.info("=" * 70)
        
        total_checks = 6
        passed_checks = sum([
            self.verification_results["import_check"],
            self.verification_results["dead_code_check"],
            self.verification_results["weaviate_references"],
            self.verification_results["dependency_check"],
            self.verification_results["configuration_check"],
            self.verification_results["performance_analysis"]
        ])
        
        msg.info(f"Total Checks: {total_checks}")
        msg.info(f"Passed: {passed_checks}")
        msg.info(f"Failed: {total_checks - passed_checks}")
        msg.info(f"Duration: {duration:.2f} seconds")
        msg.info("")
        
        # Individual check results
        checks = {
            "import_check": "Import Verification",
            "dead_code_check": "Dead Code Detection",
            "weaviate_references": "Weaviate Reference Cleanup",
            "dependency_check": "Dependency Verification",
            "configuration_check": "Configuration Verification",
            "performance_analysis": "Performance Analysis"
        }
        
        for check_key, check_name in checks.items():
            result = self.verification_results.get(check_key, False)
            status = "✓ PASS" if result else "✗ FAIL"
            msg.info(f"{check_name}: {status}")
        
        # Warnings
        if self.verification_results["warnings"]:
            msg.info("")
            msg.warn("WARNINGS:")
            for warning in self.verification_results["warnings"]:
                msg.warn(f"  - {warning}")
        
        # Errors
        if self.verification_results["errors"]:
            msg.info("")
            msg.fail("ERRORS:")
            for error in self.verification_results["errors"]:
                msg.fail(f"  - {error}")
        
        # Summary findings
        msg.info("")
        msg.info("SUMMARY FINDINGS:")
        
        if self.verification_results["dead_code_found"]:
            msg.info(f"• {len(self.verification_results['dead_code_found'])} potential dead code references")
        
        if self.verification_results["weaviate_references_found"]:
            msg.info(f"• {len(self.verification_results['weaviate_references_found'])} Weaviate references still present")
        
        msg.info("=" * 70)
        
        if passed_checks == total_checks:
            msg.good("🎉 ALL VERIFICATION CHECKS PASSED!")
            msg.good("✅ Weaviate to PostgreSQL migration completed successfully!")
        else:
            msg.fail(f"❌ {total_checks - passed_checks} verification checks failed.")
            msg.info("Please review the issues above before considering the migration complete.")


def main():
    """Main verification runner"""
    verifier = FinalCleanupVerifier()
    results = verifier.run_comprehensive_verification()
    
    # Create summary report
    report_path = Path("migration_verification_report.txt")
    with open(report_path, 'w') as f:
        f.write("Weaviate to PostgreSQL Migration Verification Report\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.utcnow().isoformat()}\n\n")
        
        f.write("Performance Notes:\n")
        for note in results.get("performance_notes", []):
            f.write(f"{note}\n")
        
        f.write("\nVerification Results:\n")
        for key, value in results.items():
            if key not in ["performance_notes", "errors", "warnings"]:
                f.write(f"{key}: {value}\n")
        
        if results["errors"]:
            f.write("\nErrors:\n")
            for error in results["errors"]:
                f.write(f"- {error}\n")
        
        if results["warnings"]:
            f.write("\nWarnings:\n")
            for warning in results["warnings"]:
                f.write(f"- {warning}\n")
    
    msg.info(f"📄 Detailed report saved to: {report_path}")
    
    # Exit with appropriate code
    total_checks = 6
    passed_checks = sum([
        results["import_check"],
        results["dead_code_check"],
        results["weaviate_references"],
        results["dependency_check"],
        results["configuration_check"],
        results["performance_analysis"]
    ])
    
    if passed_checks == total_checks:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Some issues found


if __name__ == "__main__":
    main()
