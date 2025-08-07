#!/usr/bin/env python3
"""
Complete RAG Pipeline Validation Script
Tests end-to-end RAG functionality with PostgreSQL backend
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


class RAGPipelineValidator:
    """Comprehensive RAG pipeline validator"""

    def __init__(self):
        self.manager = VerbaManager()
        self.logger = LoggerManager()
        self.test_results = {
            "document_upload": False,
            "document_processing": False,
            "vector_storage": False,
            "semantic_search": False,
            "context_retrieval": False,
            "response_generation": False,
            "end_to_end_rag": False,
            "errors": []
        }
        self.test_document_id = None

    async def run_complete_validation(self) -> Dict[str, Any]:
        """Run complete RAG pipeline validation"""
        msg.info("Starting complete RAG pipeline validation...")
        start_time = datetime.utcnow()

        try:
            # Step 1: Document Upload and Processing
            await self.test_document_upload_processing()

            # Step 2: Vector Storage Validation
            await self.test_vector_storage()

            # Step 3: Semantic Search
            await self.test_semantic_search()

            # Step 4: Context Retrieval
            await self.test_context_retrieval()

            # Step 5: Response Generation
            await self.test_response_generation()

            # Step 6: End-to-End RAG Pipeline
            await self.test_end_to_end_rag()

        except Exception as e:
            self.test_results["errors"].append(f"Validation suite failed: {str(e)}")
            msg.fail(f"Validation suite failed: {str(e)}")

        finally:
            # Cleanup test documents
            await self.cleanup_test_data()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        self.print_validation_results(duration)
        return self.test_results

    async def test_document_upload_processing(self):
        """Test document upload and processing pipeline"""
        msg.info("Testing document upload and processing...")
        
        try:
            # Create comprehensive test document
            test_content = """
            # PostgreSQL Vector Database Guide

            PostgreSQL with pgvector is a powerful combination for vector similarity search.
            This document explains how to use PostgreSQL for storing and querying vector embeddings.

            ## Key Features
            - Native vector operations with pgvector extension
            - ACID compliance for reliable data storage
            - Scalable architecture for large datasets
            - Integration with existing PostgreSQL tools

            ## Vector Operations
            PostgreSQL supports various vector similarity metrics:
            1. Cosine similarity for semantic search
            2. Euclidean distance for spatial queries
            3. Inner product for recommendation systems

            ## Best Practices
            Always index your vector columns for optimal performance.
            Use appropriate vector dimensions based on your embedding model.
            Consider partitioning for very large vector datasets.
            """
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
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
                    chunker_config={"chunk_size": 200, "chunk_overlap": 50},
                    embedder="OpenAIEmbedder",
                    embedder_config={"model": "text-embedding-ada-002"}
                )

                # Get credentials and connect
                credentials = Credentials(
                    deployment="Supabase",
                    url=os.getenv("SUPABASE_URL", ""),
                    key=os.getenv("SUPABASE_KEY", "")
                )
                
                if not credentials.url or not credentials.key:
                    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

                client = await self.manager.connect(credentials)
                if not client:
                    raise Exception("Failed to connect to PostgreSQL")

                # Process document
                result = await self.manager.import_document(client, file_config, self.logger)
                
                if result and len(result) > 0:
                    document = result[0]
                    self.test_document_id = document.uuid
                    
                    msg.good("✓ Document upload and processing successful")
                    msg.info(f"  - Document ID: {document.uuid}")
                    msg.info(f"  - Title: {document.title}")
                    msg.info(f"  - Chunks created: {len(document.chunks)}")
                    msg.info(f"  - Total characters: {len(document.content)}")
                    
                    self.test_results["document_upload"] = True
                    self.test_results["document_processing"] = True
                else:
                    raise Exception("Document processing returned no results")

                await self.manager.disconnect(client)

            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)

        except Exception as e:
            self.test_results["errors"].append(f"Document upload/processing failed: {str(e)}")
            msg.fail(f"✗ Document upload/processing failed: {str(e)}")

    async def test_vector_storage(self):
        """Test vector storage in PostgreSQL"""
        msg.info("Testing vector storage...")
        
        try:
            if not self.test_document_id:
                raise Exception("No test document available for vector storage test")

            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect to PostgreSQL")

            # Get document statistics to verify vector storage
            stats = await self.manager.get_document_stats(client)
            
            if stats and stats.get("total_chunks", 0) > 0:
                msg.good("✓ Vector storage successful")
                msg.info(f"  - Total documents: {stats.get('total_documents', 0)}")
                msg.info(f"  - Total chunks: {stats.get('total_chunks', 0)}")
                msg.info(f"  - Vector dimensions: {stats.get('vector_dimensions', 'unknown')}")
                
                self.test_results["vector_storage"] = True
            else:
                raise Exception("No vectors found in storage")

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"Vector storage test failed: {str(e)}")
            msg.fail(f"✗ Vector storage test failed: {str(e)}")

    async def test_semantic_search(self):
        """Test semantic search functionality"""
        msg.info("Testing semantic search...")
        
        try:
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect to PostgreSQL")

            # Test various search queries
            test_queries = [
                "PostgreSQL vector operations",
                "similarity search metrics",
                "database best practices",
                "pgvector extension features"
            ]

            retriever_config = {
                "retriever": "WindowRetriever",
                "limit": 5,
                "similarity_threshold": 0.1
            }

            successful_searches = 0
            total_chunks_found = 0

            for query in test_queries:
                try:
                    chunks = await self.manager.retrieve_chunks(
                        client, query, retriever_config, self.logger
                    )
                    
                    if chunks and len(chunks) > 0:
                        successful_searches += 1
                        total_chunks_found += len(chunks)
                        msg.info(f"  - Query '{query}': {len(chunks)} chunks (best score: {chunks[0].score:.4f})")
                    else:
                        msg.warn(f"  - Query '{query}': No results")
                
                except Exception as e:
                    msg.warn(f"  - Query '{query}' failed: {str(e)}")

            if successful_searches > 0:
                msg.good("✓ Semantic search successful")
                msg.info(f"  - Successful queries: {successful_searches}/{len(test_queries)}")
                msg.info(f"  - Total chunks retrieved: {total_chunks_found}")
                
                self.test_results["semantic_search"] = True
            else:
                raise Exception("No successful semantic searches")

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"Semantic search test failed: {str(e)}")
            msg.fail(f"✗ Semantic search test failed: {str(e)}")

    async def test_context_retrieval(self):
        """Test context retrieval for RAG"""
        msg.info("Testing context retrieval...")
        
        try:
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect to PostgreSQL")

            # Test context retrieval with specific query
            query = "How do I optimize PostgreSQL for vector search?"
            
            retriever_config = {
                "retriever": "WindowRetriever",
                "limit": 3,
                "similarity_threshold": 0.0
            }

            chunks = await self.manager.retrieve_chunks(
                client, query, retriever_config, self.logger
            )

            if chunks and len(chunks) > 0:
                # Validate chunk content and metadata
                valid_chunks = 0
                total_context_length = 0
                
                for i, chunk in enumerate(chunks):
                    if hasattr(chunk, 'content') and chunk.content:
                        valid_chunks += 1
                        total_context_length += len(chunk.content)
                        msg.info(f"  - Chunk {i+1}: {len(chunk.content)} chars, score: {chunk.score:.4f}")
                
                if valid_chunks > 0:
                    msg.good("✓ Context retrieval successful")
                    msg.info(f"  - Valid chunks: {valid_chunks}")
                    msg.info(f"  - Total context length: {total_context_length} characters")
                    
                    self.test_results["context_retrieval"] = True
                else:
                    raise Exception("No valid chunks with content found")
            else:
                raise Exception("No chunks retrieved for context")

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"Context retrieval test failed: {str(e)}")
            msg.fail(f"✗ Context retrieval test failed: {str(e)}")

    async def test_response_generation(self):
        """Test response generation with retrieved context"""
        msg.info("Testing response generation...")
        
        try:
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect to PostgreSQL")

            # Get context for generation
            query = "What are the key features of PostgreSQL for vector search?"
            
            retriever_config = {
                "retriever": "WindowRetriever",
                "limit": 3,
                "similarity_threshold": 0.0
            }

            chunks = await self.manager.retrieve_chunks(
                client, query, retriever_config, self.logger
            )

            if not chunks:
                raise Exception("No context chunks available for generation")

            # Generate response
            generator_config = {
                "generator": "OpenAIGenerator",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 200
            }

            response = await self.manager.generate_response(
                client, query, chunks, generator_config, self.logger
            )

            if response and len(response.strip()) > 0:
                msg.good("✓ Response generation successful")
                msg.info(f"  - Query: {query}")
                msg.info(f"  - Context chunks: {len(chunks)}")
                msg.info(f"  - Response length: {len(response)} characters")
                msg.info(f"  - Response preview: {response[:100]}...")
                
                # Validate response quality
                if len(response.strip()) > 50:  # Reasonable response length
                    self.test_results["response_generation"] = True
                else:
                    raise Exception("Generated response too short")
            else:
                raise Exception("Empty response generated")

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"Response generation test failed: {str(e)}")
            msg.fail(f"✗ Response generation test failed: {str(e)}")

    async def test_end_to_end_rag(self):
        """Test complete end-to-end RAG pipeline"""
        msg.info("Testing end-to-end RAG pipeline...")
        
        try:
            credentials = Credentials(
                deployment="Supabase",
                url=os.getenv("SUPABASE_URL", ""),
                key=os.getenv("SUPABASE_KEY", "")
            )
            
            client = await self.manager.connect(credentials)
            if not client:
                raise Exception("Failed to connect to PostgreSQL")

            # Complete RAG pipeline test
            test_queries = [
                "Explain PostgreSQL vector similarity search",
                "What are the benefits of using pgvector?",
                "How to optimize vector database performance?"
            ]

            successful_rag_queries = 0

            for query in test_queries:
                try:
                    # Step 1: Retrieve relevant context
                    retriever_config = {
                        "retriever": "WindowRetriever",
                        "limit": 3,
                        "similarity_threshold": 0.0
                    }

                    chunks = await self.manager.retrieve_chunks(
                        client, query, retriever_config, self.logger
                    )

                    if not chunks:
                        msg.warn(f"  - No context found for: {query}")
                        continue

                    # Step 2: Generate response
                    generator_config = {
                        "generator": "OpenAIGenerator",
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.7,
                        "max_tokens": 150
                    }

                    response = await self.manager.generate_response(
                        client, query, chunks, generator_config, self.logger
                    )

                    if response and len(response.strip()) > 30:
                        successful_rag_queries += 1
                        msg.info(f"  - ✓ RAG query successful: {query[:50]}...")
                        msg.info(f"    Context: {len(chunks)} chunks, Response: {len(response)} chars")
                    else:
                        msg.warn(f"  - Poor response for: {query}")

                except Exception as e:
                    msg.warn(f"  - RAG query failed: {query} - {str(e)}")

            if successful_rag_queries > 0:
                msg.good("✓ End-to-end RAG pipeline successful")
                msg.info(f"  - Successful RAG queries: {successful_rag_queries}/{len(test_queries)}")
                
                self.test_results["end_to_end_rag"] = True
            else:
                raise Exception("No successful end-to-end RAG queries")

            await self.manager.disconnect(client)

        except Exception as e:
            self.test_results["errors"].append(f"End-to-end RAG test failed: {str(e)}")
            msg.fail(f"✗ End-to-end RAG test failed: {str(e)}")

    async def cleanup_test_data(self):
        """Clean up test documents"""
        if self.test_document_id:
            try:
                msg.info("Cleaning up test data...")
                
                credentials = Credentials(
                    deployment="Supabase",
                    url=os.getenv("SUPABASE_URL", ""),
                    key=os.getenv("SUPABASE_KEY", "")
                )
                
                client = await self.manager.connect(credentials)
                if client:
                    await self.manager.delete_documents(client, [self.test_document_id])
                    msg.good("✓ Test data cleaned up")
                    await self.manager.disconnect(client)
                    
            except Exception as e:
                msg.warn(f"⚠ Failed to clean up test data: {str(e)}")

    def print_validation_results(self, duration: float):
        """Print comprehensive validation results"""
        msg.info("=" * 60)
        msg.info("RAG PIPELINE VALIDATION RESULTS")
        msg.info("=" * 60)
        
        total_tests = len([k for k in self.test_results.keys() if k != "errors"])
        passed_tests = len([k for k, v in self.test_results.items() if k != "errors" and v])
        
        msg.info(f"Total Tests: {total_tests}")
        msg.info(f"Passed: {passed_tests}")
        msg.info(f"Failed: {total_tests - passed_tests}")
        msg.info(f"Duration: {duration:.2f} seconds")
        msg.info("")
        
        # Individual test results
        test_names = {
            "document_upload": "Document Upload",
            "document_processing": "Document Processing",
            "vector_storage": "Vector Storage",
            "semantic_search": "Semantic Search",
            "context_retrieval": "Context Retrieval",
            "response_generation": "Response Generation",
            "end_to_end_rag": "End-to-End RAG Pipeline"
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
            msg.good("🎉 ALL TESTS PASSED! RAG pipeline is working correctly with PostgreSQL.")
        else:
            msg.fail(f"❌ {total_tests - passed_tests} tests failed. Please check the pipeline.")


async def main():
    """Main validation runner"""
    validator = RAGPipelineValidator()
    results = await validator.run_complete_validation()
    
    # Exit with appropriate code
    total_tests = len([k for k in results.keys() if k != "errors"])
    passed_tests = len([k for k, v in results.items() if k != "errors" and v])
    
    if passed_tests == total_tests:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == "__main__":
    asyncio.run(main())
