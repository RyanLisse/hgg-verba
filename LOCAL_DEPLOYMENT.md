# Local Weaviate Docker Deployment Guide

This guide explains how to run Verba with a local Weaviate instance using Docker, instead of relying on Weaviate Cloud.

## Overview

Running Weaviate locally provides:
- **Complete data control** - All data stays on your infrastructure
- **No cloud dependencies** - Works offline
- **Cost savings** - No cloud hosting fees
- **Better performance** - Direct local network connection
- **Development flexibility** - Easy to reset and experiment

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB of RAM available
- 10GB of free disk space
- Ports 8000, 8080, and 50051 available

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/weaviate/verba.git
cd verba
```

### 2. Set Up Environment Variables

Copy the local environment template:
```bash
cp .env.local .env
```

Edit `.env` and add your API keys:
```bash
# Required for embeddings and generation
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
COHERE_API_KEY=your-cohere-key-here

# Optional for document processing
UNSTRUCTURED_API_KEY=your-unstructured-key-here
FIRECRAWL_API_KEY=your-firecrawl-key-here
```

### 3. Start the Services

```bash
# Start both Weaviate and Verba
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v
```

### 4. Access the Application

- **Verba UI**: http://localhost:8000
- **Weaviate API**: http://localhost:8080
- **Weaviate gRPC**: localhost:50051

## Configuration Details

### Docker Compose Services

The `docker-compose.yml` includes two main services:

#### Weaviate Service
- **Image**: `cr.weaviate.io/semitechnologies/weaviate:1.26.1`
- **Ports**: 
  - 8080 (REST API)
  - 50051 (gRPC for faster operations)
- **Persistence**: Data stored in `weaviate_data` volume
- **Modules**: Pre-configured with OpenAI, Anthropic, Cohere, and Gemini support
- **Performance**: Optimized with 6GB memory limit and 4 CPU cores

#### Verba Service
- **Build**: From local Dockerfile
- **Port**: 8000
- **Connection**: Automatically connects to Weaviate at `http://weaviate:8080`
- **Volumes**: `./data` mounted for document storage

### Environment Variables

Key environment variables for local deployment:

```bash
# Weaviate Connection (handled automatically by Docker)
WEAVIATE_URL_VERBA=http://localhost:8080
WEAVIATE_API_KEY_VERBA=  # Leave empty for local deployment

# Server Configuration
VERBA_HOST=0.0.0.0
VERBA_PORT=8000
```

## Using the Local Deployment

### Initial Setup

1. **First Launch**: When you first access http://localhost:8000, Verba will automatically:
   - Connect to the local Weaviate instance
   - Create necessary collections (VERBA_DOCUMENTS, VERBA_CONFIG, VERBA_SUGGESTION)
   - Initialize the schema

2. **Select Components**: Choose your preferred:
   - **Embedder**: OpenAI, Cohere, or local models
   - **Generator**: OpenAI (o3, GPT-4.1), Anthropic (Claude 4), or Gemini (2.5)
   - **Retriever**: WindowRetriever or other options

3. **Import Documents**: Use the document import feature to add your content

### Connection Settings

When using the UI, select:
- **Deployment Type**: "Weaviate" (not "Docker" - this is handled automatically)
- **URL**: Leave as `http://localhost:8080`
- **API Key**: Leave empty

The system will automatically detect this as a local deployment and connect appropriately.

## Data Management

### Backup Data
```bash
# Backup Weaviate data
docker run --rm -v verba_weaviate_data:/data -v $(pwd):/backup alpine tar czf /backup/weaviate-backup.tar.gz -C /data .

# Backup document files
tar czf documents-backup.tar.gz ./data
```

### Restore Data
```bash
# Restore Weaviate data
docker run --rm -v verba_weaviate_data:/data -v $(pwd):/backup alpine tar xzf /backup/weaviate-backup.tar.gz -C /data

# Restore document files
tar xzf documents-backup.tar.gz
```

### Reset Everything
```bash
# Stop services and remove all data
docker compose down -v
rm -rf ./data/*

# Start fresh
docker compose up -d
```

## Performance Optimization

### Memory Settings

The Weaviate container is configured with:
- `GOMEMLIMIT: '6GiB'` - Maximum memory for Go runtime
- `GOMAXPROCS: '4'` - Number of CPU cores to use

Adjust these in `docker-compose.yml` based on your system:

```yaml
environment:
  GOMEMLIMIT: '8GiB'  # Increase for larger datasets
  GOMAXPROCS: '8'     # Increase for more CPU cores
```

### Vector Index Settings

For large datasets (>1M documents), consider adjusting:
- Increase memory allocation
- Use SSD storage for the Docker volume
- Enable HNSW index optimization

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using port 8080
   lsof -i :8080
   
   # Change port in docker-compose.yml if needed
   ports:
     - 8081:8080  # Use 8081 instead
   ```

2. **Connection Refused**
   - Ensure Weaviate is healthy: `docker compose ps`
   - Check logs: `docker compose logs weaviate`
   - Wait for startup (can take 15-30 seconds)

3. **Out of Memory**
   - Increase Docker memory allocation
   - Reduce `GOMEMLIMIT` in docker-compose.yml
   - Use smaller embedding models

4. **Slow Performance**
   - Ensure Docker has enough resources
   - Use gRPC port (50051) for bulk operations
   - Consider using batch imports

### Health Checks

```bash
# Check Weaviate health
curl http://localhost:8080/v1/.well-known/ready

# Check Verba health
curl http://localhost:8000/health

# View container status
docker compose ps

# View resource usage
docker stats
```

## Advanced Configuration

### Using External Weaviate

To connect to a Weaviate instance running elsewhere on your network:

1. Update `.env`:
   ```bash
   WEAVIATE_URL_VERBA=http://your-weaviate-host:8080
   ```

2. Remove the Weaviate service from docker-compose.yml

3. Start only Verba:
   ```bash
   docker compose up verba
   ```

### Custom Schema

The schema is automatically created, but you can customize it by modifying the collection definitions in `goldenverba/components/managers.py`.

### Production Deployment

For production use:
1. Use a reverse proxy (nginx/traefik) with SSL
2. Enable authentication on Weaviate
3. Set up regular backups
4. Monitor with Prometheus/Grafana
5. Use dedicated storage volumes

## Benefits of Local Deployment

1. **Data Privacy**: All data remains on your infrastructure
2. **Cost Effective**: No cloud API costs for vector database
3. **Low Latency**: Direct local network connection
4. **Full Control**: Complete control over updates and configuration
5. **Offline Capable**: Works without internet (except for LLM APIs)
6. **Development Friendly**: Easy to reset and experiment

## Support

For issues or questions:
- Check the [Verba Documentation](https://github.com/weaviate/verba)
- Review [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- Open an issue on GitHub
- Join the Weaviate Slack community

## License

This setup uses the open-source version of Weaviate, which is available under the BSD-3-Clause license.