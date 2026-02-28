# Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- Git

### Setup
```bash
git clone https://github.com/Mohammed-Anirudh/NETAI-LLM-Integration-Chatbot.git
cd NETAI-LLM-Integration-Chatbot

python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
make run
```

The application starts at `http://localhost:8000` with:
- Chat UI: `http://localhost:8000/static/index.html`
- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`

---

## Docker

### Build
```bash
docker build -t netai-chatbot:latest .
```

### Run with Docker Compose
```bash
docker compose up --build
```

### Environment Variables
Configure via `.env` file or `docker-compose.yml` environment section.

---

## Kubernetes Deployment

### Prerequisites
- `kubectl` configured for your cluster
- NRP namespace access (for production)

### Using Raw Manifests

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy configuration
kubectl apply -f k8s/configmap.yaml

# Set secrets (edit with your API key first!)
kubectl edit -f k8s/secret.yaml  # Set LLM_API_KEY
kubectl apply -f k8s/secret.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Verify
kubectl -n netai get pods
kubectl -n netai get svc
```

### Using Helm Chart

```bash
# Install
helm install netai-chatbot helm/netai-chatbot/ \
  --namespace netai \
  --create-namespace \
  --set secrets.llmApiKey=your-api-key \
  --set config.enableMockData=false

# Check status
helm status netai-chatbot -n netai

# Upgrade
helm upgrade netai-chatbot helm/netai-chatbot/ \
  --namespace netai \
  --set image.tag=v0.2.0

# Uninstall
helm uninstall netai-chatbot -n netai
```

### Custom Values

Create `values-production.yaml`:
```yaml
replicaCount: 3

config:
  enableMockData: "false"
  llmApiBaseUrl: "https://llm.nrp-nautilus.io/v1"
  llmDefaultModel: "qwen3-vl"
  appLogLevel: "warning"

secrets:
  llmApiKey: "your-production-api-key"

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: "2"
    memory: 2Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
```

Install with custom values:
```bash
helm install netai-chatbot helm/netai-chatbot/ \
  -f values-production.yaml \
  --namespace netai
```

---

## GPU Inference Pod

For self-hosting LLM models on NRP GPU resources:

```bash
kubectl apply -f k8s/gpu-inference.yaml
```

This creates:
- GPU-enabled deployment with NVIDIA GPU request
- PersistentVolumeClaim for model cache (50Gi)
- Service for internal inference endpoint

Update the chatbot to use the local inference service:
```yaml
config:
  llmApiBaseUrl: "http://netai-llm-inference.netai.svc.cluster.local:8080/v1"
```

---

## Monitoring

### Health Probes
- **Liveness**: `GET /healthz` — Is the process alive?
- **Readiness**: `GET /readyz` — Is the service ready for traffic?

### Kubernetes Dashboard
```bash
kubectl -n netai get pods -w
kubectl -n netai logs -f deployment/netai-chatbot
kubectl -n netai top pods
```

### Port Forwarding (for debugging)
```bash
kubectl -n netai port-forward svc/netai-chatbot 8000:80
```
