# Railway Deployment Strategy for Verba RAG Application

## Current Setup Status

- ✅ **Weaviate Database**: Running on Railway at `https://weaviate-production-9dce.up.railway.app`
- ✅ **Verba Application**: Ready with Instructor integration
- ✅ **Configuration**: Updated to connect to Railway Weaviate instance  

## Optimal Railway Deployment Strategy

### 1. Service Grouping Strategy

#### ✅ RECOMMENDED: Single Railway Project

Create a Railway "Project" to group both services together for optimal benefits:

- **Cost Efficiency**: No egress fees for service-to-service communication
- **Private Networking**: High-speed internal communication (up to 100 Gbps)
- **Simplified Management**: All related services in one dashboard
- **Variable Sharing**: Cross-service environment variable referencing
- **Template Creation**: Can package as deployable template

**Project Structure:**

```text
Verba-RAG-Project/
├── weaviate-db (existing service)
└── verba-app (new service to deploy)
```

### 2. Deployment Strategy

#### Option A: GitHub Integration (RECOMMENDED)

1. **Setup GitHub Integration:**

   ```bash
   # Ensure your code is in a GitHub repository
   git remote -v  # Verify GitHub origin
   
   # Push latest changes
   git add .
   git commit -m "feat: Railway deployment configuration"
   git push origin main
   ```

2. **Deploy from Railway Dashboard:**
   - Go to your existing Weaviate project
   - Click "Create" → "Deploy from GitHub repo"
   - Select your `hgg-verba` repository
   - Choose `main` branch
   - Railway will auto-detect Python/FastAPI and use Nixpacks

3. **Auto-deployment on Push:**
   - Every git push to `main` triggers automatic deployment
   - Railway uses Nixpacks to build Python FastAPI applications
   - No manual Dockerfile needed (unless custom requirements)

#### Option B: Railway CLI Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to existing project (with Weaviate)
railway link [your-project-id]

# Deploy current directory
railway up
```

### 3. Service Communication & Networking

#### ✅ Use Private Networking

Configure Verba to communicate with Weaviate via private network:

1. **Environment Variable Configuration:**

   ```bash
   # In Verba service variables, use Railway's private domain
   WEAVIATE_URL_VERBA=${{weaviate-db.RAILWAY_PRIVATE_DOMAIN}}
   # Or reference the existing service directly
   WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app
   ```

2. **Benefits of Private Networking:**
   - No egress costs between services
   - IPv6 encrypted Wireguard tunnels
   - Internal DNS resolution via `railway.internal` domain
   - Faster communication (up to 100 Gbps internal)

#### Security Considerations

- Keep Weaviate internal-only (no public domain needed)
- Only expose Verba application publicly
- Use Railway's managed TLS certificates
- Environment variables are encrypted at rest

### 4. Environment Variables Management

#### ✅ RECOMMENDED: Hybrid Approach

**A. Shared Variables (Project Level):**

```bash
# Create shared variables for common configuration
ENVIRONMENT=production
LOG_LEVEL=info
WEAVIATE_URL_VERBA=${{weaviate-db.RAILWAY_PRIVATE_DOMAIN}}
```

**B. Service-Level Variables (Verba App):**

```bash
# Seal sensitive API keys for security
OPENAI_API_KEY=[sealed]
ANTHROPIC_API_KEY=[sealed]
COHERE_API_KEY=[sealed]
GOOGLE_API_KEY=[sealed]

# Reference shared variables
WEAVIATE_URL_VERBA=${{shared.WEAVIATE_URL_VERBA}}
```

**Variable Management Commands:**

```bash
# Set variables via CLI
railway variables set OPENAI_API_KEY=your-key --seal

# Reference other service variables
railway variables set DATABASE_URL='${{weaviate-db.RAILWAY_PRIVATE_DOMAIN}}'
```

### 5. Production Configuration

**A. Service Configuration:**

Create `railway.toml` in your project root:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn goldenverba.server.api:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/api/health"
healthcheckTimeout = 60
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[env]
PYTHONPATH = "/app"
```

**B. Scaling Configuration:**

```toml
# Add to railway.toml for production scaling
[deploy]
replicas = 2  # Horizontal scaling
memoryLimit = "2Gi"  # 2GB RAM
cpuLimit = "1000m"   # 1 vCPU
```

### 6. Deployment Steps

**Step-by-Step Deployment:**

1. **Prepare Repository:**

   ```bash
   cd /Users/neo/Developer/hgg-verba
   
   # Create railway.toml with configuration above
   # Ensure pyproject.toml dependencies are up to date
   # Verify .env files are correct
   ```

2. **Create Railway Service:**
   - Go to Railway dashboard
   - Navigate to your Weaviate project
   - Click "Create" → "Deploy from GitHub repo"
   - Select `hgg-verba` repository
   - Service will auto-deploy

3. **Configure Environment Variables:**

   ```bash
   # Via Railway dashboard or CLI
   WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app
   OPENAI_API_KEY=[your-sealed-key]
   ANTHROPIC_API_KEY=[your-sealed-key]
   # ... other API keys
   ```

4. **Enable Networking:**
   - Go to service Settings → Networking
   - Click "Generate Domain" for public access
   - Configure custom domain if needed

### 7. Scaling & Monitoring

**A. Scaling Options:**

- **Vertical**: Up to 32 vCPU, 32GB RAM per service
- **Horizontal**: Up to 50 replicas with load balancing
- **Global**: Deploy to 4 regions (US East/West, Europe West, SE Asia)

**B. Monitoring Setup:**

```bash
# Configure observability
ENABLE_LOGGING=true
LOG_FORMAT=json
METRICS_ENABLED=true

# Webhook notifications
RAILWAY_WEBHOOK_URL=https://your-slack-webhook
```

**C. Usage Limits:**

- Set spending limits in project settings
- Configure alerts for resource usage
- Monitor costs via Railway dashboard

### 8. CI/CD Pipeline

**Automated Deployment Workflow:**

```yaml
# .github/workflows/railway-deploy.yml
name: Deploy to Railway

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Railway CLI
        run: npm install -g @railway/cli
        
      - name: Deploy to Railway
        run: railway up --service verba-app
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

### 9. Production Checklist

**Pre-Deployment:**

- [ ] All API keys configured and sealed
- [ ] Environment variables reference correct services
- [ ] Weaviate connection tested
- [ ] Health check endpoint working (`/api/health`)
- [ ] pyproject.toml dependencies up to date

**Post-Deployment:**

- [ ] Public domain generated and accessible
- [ ] Private networking between services working
- [ ] Logs showing successful startup
- [ ] Test document ingestion and querying
- [ ] Monitor resource usage
- [ ] Set up alerts and notifications

### 10. Cost Optimization

**Best Practices:**

- Use private networking to avoid egress costs
- Right-size compute resources (start small, scale up)
- Use shared variables to reduce duplication
- Monitor usage with Railway's built-in analytics
- Consider region placement for user proximity

**Estimated Monthly Costs:**

- Weaviate service: ~$5-20/month (depending on usage)
- Verba service: ~$5-20/month (1-2 replicas)
- Total: ~$10-40/month for basic production setup

---

## Quick Start Commands

```bash
# 1. Link to Railway project
railway link

# 2. Set essential variables
railway variables set OPENAI_API_KEY=your-key --seal
railway variables set WEAVIATE_URL_VERBA=https://weaviate-production-9dce.up.railway.app

# 3. Deploy
railway up

# 4. Generate public domain
railway domain

# 5. View logs
railway logs
```

This strategy provides a robust, scalable, and cost-effective deployment for your
Verba RAG application on Railway.
