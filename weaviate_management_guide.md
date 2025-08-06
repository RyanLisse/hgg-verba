# Weaviate Connection Management Guide

## 🎉 Connection Status: Both Working!

Your Weaviate setup is now fully operational with both local and Railway instances:

### ✅ Local Docker Weaviate
- **URL**: `http://localhost:8080`
- **Version**: 1.26.1
- **Modules**: 6 enabled
- **Status**: Running and accessible
- **gRPC Port**: 50051 (for faster operations)

### ✅ Railway Weaviate
- **URL**: `https://weaviate-production-9dce.up.railway.app`
- **Version**: 1.31.9 (newer version)
- **Modules**: 10 enabled
- **Status**: Running and accessible
- **Authentication**: Anonymous access enabled

## 🔧 Quick Commands

### Local Docker Management
```bash
# Start local Weaviate only
docker compose --env-file .env.local up weaviate -d

# Start both Verba and Weaviate locally
docker compose --env-file .env.local up -d

# Stop services
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v

# View logs
docker compose logs -f weaviate

# Check status
docker ps | grep weaviate
```

### Health Checks
```bash
# Test local Weaviate
curl http://localhost:8080/v1/.well-known/ready

# Test Railway Weaviate
curl https://weaviate-production-9dce.up.railway.app/v1/.well-known/ready

# Get meta information (local)
curl http://localhost:8080/v1/meta | python3 -m json.tool

# Get meta information (Railway)
curl https://weaviate-production-9dce.up.railway.app/v1/meta | python3 -m json.tool

# Run connection test script
python3 test_weaviate_connections.py
```

## 🔄 Switching Between Instances

### For Local Development (.env.local)
```bash
WEAVIATE_URL_VERBA=http://localhost:8080
WEAVIATE_API_KEY_VERBA=
```

### For Railway Production (.env)
```bash
WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app
WEAVIATE_API_KEY_VERBA=
```

### Docker Compose Configuration
The `docker-compose.yml` is already configured to switch between local and Railway:

```yaml
environment:
  # For local Docker deployment (default):
  - WEAVIATE_URL_VERBA=http://weaviate:8080
  # For Railway Weaviate deployment (uncomment and comment above):
  # - WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app
```

## 🚀 Running Verba

### Option 1: Local Development (Python)
```bash
# Use local Weaviate
export WEAVIATE_URL_VERBA=http://localhost:8080
verba start --port 8000 --host localhost

# Or use Railway Weaviate
export WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app
verba start --port 8000 --host localhost
```

### Option 2: Docker with Local Weaviate
```bash
docker compose --env-file .env.local up -d
```

### Option 3: Docker with Railway Weaviate
```bash
# Edit docker-compose.yml to use Railway URL, then:
docker compose up verba -d
```

## 📊 Performance Comparison

| Feature | Local Docker | Railway |
|---------|-------------|---------|
| Version | 1.26.1 | 1.31.9 |
| Modules | 6 | 10 |
| Latency | ~1ms | ~50-200ms |
| Persistence | Local volume | Cloud storage |
| Availability | Local only | Internet accessible |
| Cost | Free (local resources) | Railway pricing |

## 🔍 Troubleshooting

### Local Docker Issues
```bash
# Check if Docker is running
docker --version

# Check container status
docker ps -a | grep weaviate

# Restart container
docker compose restart weaviate

# View detailed logs
docker compose logs weaviate --tail 50
```

### Railway Issues
```bash
# Test connectivity
curl -v https://weaviate-production-9dce.up.railway.app/v1/.well-known/ready

# Check if URL is correct
echo $WEAVIATE_URL_VERBA
```

### Connection Test
```bash
# Run comprehensive test
python3 test_weaviate_connections.py
```

## 🎯 Recommendations

1. **Development**: Use local Docker for faster iteration and testing
2. **Production**: Use Railway for deployed applications
3. **Data Migration**: Use Weaviate backup/restore tools to sync data between instances
4. **Monitoring**: Set up health checks for both instances
5. **Version Management**: Keep local version updated to match Railway when possible

## 📝 Next Steps

1. **Test with Verba**: Start Verba and verify it connects to your chosen Weaviate instance
2. **Import Data**: Use Verba's import functionality to add your documents
3. **Configure LLM APIs**: Add your API keys for OpenAI, Anthropic, etc.
4. **Set up Monitoring**: Implement health checks and alerts
5. **Backup Strategy**: Plan regular backups of your Weaviate data
