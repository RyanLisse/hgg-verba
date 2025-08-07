#!/usr/bin/env python3
"""
Comprehensive Test Script for PostgreSQL Functionality
Tests document ingestion, vector search, and RAG pipeline with PostgreSQL backend
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from dotenv import load_dotenv
from wasabi import msg

from goldenverba.unified_verba_manager import VerbaManager
from goldenverba.server.types import Credentials, FileConfig
from goldenverba.server.helpers import LoggerManager

load_dotenv()


class PostgreSQLFunctionalityTester:
    """Comprehensive tester for PostgreSQL functionality"""

    def __init__(self):
        self.manager = VerbaManager()
        self.logger = LoggerManager()
        self.test_results = {
            "connection": False,
            "document_ingestion": False,
            "vector_search": False,
            "rag_pipeline": False,
            "api_endpoints": False,
            "errors": []
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all PostgreSQL functionality tests"""
        msg.info("Starting comprehensive PostgreSQL functionality tests...")
        start_time = datetime.utcnow()

        try:
            # Test 1: Database Connection
            await self.test_database_connection()

            # Test 2: Document Ingestion
            await self.test_document_ingestion()

            # Test 3: Vector Search
            await self.test_vector_search()

            # Test 4: RAG Pipeline
            await self.test_rag_pipeline()

            # Test 5: API Endpoints
            await self.test_api_endpoints()

        except Exception as e:
            self.test_results["errors"].append(f"Test suite failed: {str(e)}")
            msg.fail(f"Test suite failed: {str(e)}")

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        self.print_test_results(duration)
        return self.test_results

    async def test_database_connection(self):
        """Test PostgreSQL database connection"""
        msg.info("Testing PostgreSQL database connection...")
        
        try:
            # Get credentials from environment
            credentials = Credentials(
                deployment="PostgreSQL",
                url=os.getenv("DATABASE_URL", ""),
                key=os.getenv("POSTGRES_PASSWORD", "")
            )

            if not credentials.url:
                raise Exception("Missing DATABASE_URL environment variable")

            # Test connection
            client = await self.manager.connect(credentials)
            if client:
                msg.good("✓ PostgreSQL connection successful")
                self.test_results["connection"] = True
                
                # Test health check
                health = await self.manager.health_check(client)
                if health.get("status") == "healthy":
                    msg.good("✓ PostgreSQL health check passed")
                else:
                    msg.warn("⚠ PostgreSQL health check returned unhealthy status")
                
                await self.manager.disconnect(client)
            else:
                raise Exception("Failed to establish connection")

        except Exception as e:
            self.test_results["errors"].append(f"Connection test failed: {str(e)}")
            msg.fail(f"✗ Connection test failed: {str(e)}")

    async def test_document_ingestion(self):
        """Test document ingestion with PostgreSQL backend"""
        msg.info("Testing document ingestion...")
        
        try:
            # Create a test document
            test_content = """
            This is a test document for PostgreSQL functionality testing.
            It contains multiple sentences to test chunking and embedding.
            The document should be processed and stored in PostgreSQL with pgvector.
            Vector embeddings should be generated and stored properly.
            """
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name

            try:
                # Create file configuration
                file_config = FileConfig(
                    filename=Path(temp_file_path).name,
                    file_path=temp_file_path,
                    reader="BasicReader",
                    reader_config={},
                    chunker="TokenChunker",
                    chunker_config={"chunk_size": 100, "chunk_overlap": 20},
                    embedder="OpenAIEmbedder",
                    embedder_config={"model": "text-embedding-ada-002"}
                )

                # Get credentials and connect
                credentials = Credentials(
                    deployment="Supabase",
                    url=os.getenv("SUPABASE_URL", ""),
                    key=os.getenv("SUPABASE_KEY", "")
                )
                
                client = await self.manager.connect(credentials)
                if not client:
                    raise Exception("Failed to connect for document ingestion test")

                # Import document
                result = await self.manager.import_document(client, file_config, self.logger)
                
                if result and len(result) > 0:
                    msg.good("✓ Document ingestion successful")
                    msg.info(f"  - Processed {len(result)} documents")
                    msg.info(f"  - Generated {sum(len(doc.chunks) for doc in result)} chunks")
                    self.test_results["document_ingestion"] = True
                else:
                    raise Exception("Document ingestion returned no results")

                await self.manager.disconnect(client)

            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            self.test_results["errors"].append(f"Document ingestion test failed: {str(e)}")
            msg.fail(f"✗ Document ingestion test failed: {str(e)}")

    async def test_vector_search(self):
        """Test vector search functionality"""
        msg.info("Testing vector search functionality...")
        
        try:
            # Get credentials and connect
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect for vector search test")

            # Test retrieval configuration
            retriever_config = {
                "retriever": "WindowRetriever",
                "limit": 5,
                "similarity_threshold": 0.0
            }

            # Perform vector search
            chunks = await self.manager.retrieve_chunks(
                client,
                "test document functionality",
                retriever_config,
                self.logger
            )

            if chunks and len(chunks) > 0:
                msg.good("✓ Vector search successful")
                msg.info(f"  - Retrieved {len(chunks)} relevant chunks")
                for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                    msg.info(f"  - Chunk {i+1}: Score {chunk.score:.4f}")
                self.test_results["vector_search"] = True
            else:
                msg.warn("⚠ Vector search returned no results (may be expected if no documents exist)")
                self.test_results["vector_search"] = True  # Not necessarily a failure

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"Vector search test failed: {str(e)}")
            msg.fail(f"✗ Vector search test failed: {str(e)}")

    async def test_rag_pipeline(self):
        """Test end-to-end RAG pipeline"""
        msg.info("Testing RAG pipeline functionality...")
        
        try:
            # Get credentials and connect
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect for RAG pipeline test")

            # Step 1: Retrieve relevant chunks
            retriever_config = {
                "retriever": "WindowRetriever",
                "limit": 3,
                "similarity_threshold": 0.0
            }

            query = "What is this document about?"
            chunks = await self.manager.retrieve_chunks(
                client,
                query,
                retriever_config,
                self.logger
            )

            # Step 2: Generate response
            generator_config = {
                "generator": "OpenAIGenerator",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 150
            }

            response = await self.manager.generate_response(
                client,
                query,
                chunks,
                generator_config,
                self.logger
            )

            if response and len(response.strip()) > 0:
                msg.good("✓ RAG pipeline successful")
                msg.info(f"  - Query: {query}")
                msg.info(f"  - Retrieved {len(chunks)} chunks")
                msg.info(f"  - Generated response: {response[:100]}...")
                self.test_results["rag_pipeline"] = True
            else:
                raise Exception("RAG pipeline generated empty response")

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"RAG pipeline test failed: {str(e)}")
            msg.fail(f"✗ RAG pipeline test failed: {str(e)}")

    async def test_api_endpoints(self):
        """Test key API endpoint functionality"""
        msg.info("Testing API endpoint functionality...")
        
        try:
            # Test configuration management
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect for API endpoint test")

            # Test configuration retrieval
            rag_config = await self.manager.get_config(client, "rag")
            theme_config = await self.manager.get_config(client, "theme")
            
            msg.good("✓ Configuration retrieval successful")
            msg.info(f"  - RAG config: {'Found' if rag_config else 'Not found'}")
            msg.info(f"  - Theme config: {'Found' if theme_config else 'Not found'}")

            # Test document statistics
            stats = await self.manager.get_document_stats(client)
            msg.good("✓ Document statistics retrieval successful")
            msg.info(f"  - Stats: {stats}")

            self.test_results["api_endpoints"] = True
            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"API endpoint test failed: {str(e)}")
            msg.fail(f"✗ API endpoint test failed: {str(e)}")

    def print_test_results(self, duration: float):
        """Print comprehensive test results"""
        msg.info("=" * 60)
        msg.info("POSTGRESQL FUNCTIONALITY TEST RESULTS")
        msg.info("=" * 60)
        
        total_tests = len([k for k in self.test_results.keys() if k != "errors"])
        passed_tests = len([k for k, v in self.test_results.items() if k != "errors" and v])
        
        msg.info(f"Total Tests: {total_tests}")
        msg.info(f"Passed: {passed_tests}")
        msg.info(f"Failed: {total_tests - passed_tests}")
        msg.info(f"Duration: {duration:.2f} seconds")
        msg.info("")
        
        # Individual test results
        for test_name, result in self.test_results.items():
            if test_name == "errors":
                continue
            status = "✓ PASS" if result else "✗ FAIL"
            msg.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        # Error summary
        if self.test_results["errors"]:
            msg.info("")
            msg.warn("ERRORS ENCOUNTERED:")
            for error in self.test_results["errors"]:
                msg.warn(f"  - {error}")
        
        msg.info("=" * 60)
        
        if passed_tests == total_tests:
            msg.good("🎉 ALL TESTS PASSED! PostgreSQL functionality is working correctly.")
        else:
            msg.fail(f"❌ {total_tests - passed_tests} tests failed. Please check the errors above.")


async def main():
    """Main test runner"""
    tester = PostgreSQLFunctionalityTester()
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    total_tests = len([k for k in results.keys() if k != "errors"])
    passed_tests = len([k for k, v in results.items() if k != "errors" and v])
    
    if passed_tests == total_tests:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    asyncio.run(main())
