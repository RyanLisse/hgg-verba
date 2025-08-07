# Verba: The Golden RAGtriever

Verba is an open-source Retrieval-Augmented Generation (RAG) application designed to provide an end-to-end, streamlined interface for querying and interacting with documents and data. It combines state-of-the-art RAG techniques with vector databases to enable users to ask questions about their documents, cross-reference data points, and gain insights from knowledge bases.

## Key Features

- **Multi-provider LLM support**: OpenAI, Anthropic Claude, Google Gemini, Cohere, and local models via Ollama
- **Flexible embedding models**: OpenAI, Cohere, VoyageAI, SentenceTransformers, and Ollama
- **Multiple data ingestion methods**: PDF, DOCX, CSV/XLSX, GitHub/GitLab repos, web scraping via Firecrawl, and UnstructuredIO
- **Advanced chunking strategies**: Token-based, sentence-based, semantic, recursive, HTML, Markdown, code, and JSON
- **Hybrid search**: Combines semantic and keyword search for better retrieval
- **Customizable frontend**: Built with Next.js and React, fully customizable UI
- **Vector visualization**: 3D visualization of document embeddings
- **Docker deployment**: Complete containerized deployment with PostgreSQL backend

## Architecture

Verba follows a modular architecture with clear separation between:
- **Backend**: Python FastAPI server handling RAG pipeline, document processing, and API endpoints
- **Frontend**: Next.js React application providing the user interface
- **Database**: PostgreSQL with pgvector for vector storage and operations
- **Components**: Pluggable system for embedders, generators, chunkers, and retrievers

The application is designed for both local development and production deployment, with support for Docker, cloud providers, and various database backends.