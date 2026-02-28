<div align="center">

# 🔬 NETAI — AI-Powered Kubernetes Chatbot for Network Diagnostics

**Google Summer of Code 2026 • National Research Platform (NRP)**

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5.svg)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-Apache%202.0-red.svg)](LICENSE)

*An intelligent chatbot that integrates with NRP's managed LLM service to provide*
*natural language network diagnostics, anomaly explanation, and remediation strategies.*

[Features](#-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [API Reference](#-api-reference) • [Deployment](#-deployment) • [Testing](#-testing)

</div>

---

## 📋 Overview

NETAI is a **Kubernetes-native chatbot** that leverages the National Research Platform's managed LLM service (supporting **Qwen3-VL**, **GLM-4.7**, and **GPT-OSS**) to help network operators:

- **Understand** complex network behaviors through natural language
- **Diagnose** anomalies with AI-powered root cause analysis
- **Remediate** issues with actionable, step-by-step strategies
- **Monitor** network health with context-aware telemetry integration

The chatbot integrates with **perfSONAR** measurement data and traceroute path analysis to provide real-time, data-driven network diagnostics assistance.

## ✨ Features

### 🤖 LLM Integration
- **Multi-model support** — Qwen3-VL (reasoning), GLM-4.7 (fast), GPT-OSS (balanced)
- **OpenAI-compatible API** — Seamless integration with NRP's managed LLM endpoints
- **Streaming responses** — Real-time token-by-token streaming via Server-Sent Events
- **Context-aware** — Automatically injects network telemetry into LLM context

### 🧠 Prompt Engineering
- **Domain-specific system prompts** — Optimized for network diagnostics, anomaly explanation, and remediation
- **Query classification** — Automatically selects the best prompt strategy per query
- **Template engine** — Reusable, parameterized prompt templates
- **Context injection** — Real-time network telemetry injected into system prompts

### 📊 Network Diagnostics
- **perfSONAR integration** — Throughput, latency, packet loss, and jitter measurements
- **Traceroute analysis** — Hop-by-hop path analysis with problematic hop detection
- **Anomaly detection** — Threshold-based and statistical (z-score) anomaly detection
- **Health monitoring** — Real-time network path health classification

### 🌐 RESTful API
- **Chat endpoints** — Send messages, stream responses, manage conversations
- **Network endpoints** — Query network health, run diagnostics, execute traceroutes
- **Health probes** — Kubernetes-compatible liveness and readiness endpoints
- **OpenAPI docs** — Auto-generated Swagger UI at `/docs`

### ☸️ Kubernetes Native
- **Helm chart** — One-command deployment with configurable values
- **GPU inference pods** — Ready for self-hosted LLM inference on NRP GPUs
- **Auto-scaling** — HPA based on CPU/memory utilization
- **Security** — Non-root containers, read-only filesystems, network policies

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web UI (Chat Interface)              │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/SSE
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Application                    │
│  ┌──────────┐  ┌────────────┐  ┌────────────────────┐  │
│  │ Chat API │  │ Network API│  │   Health Probes     │  │
│  └────┬─────┘  └─────┬──────┘  └────────────────────┘  │
│       │              │                                   │
│  ┌────▼──────────────▼───────────────────────────────┐  │
│  │              Context Manager                       │  │
│  │  • Conversation memory    • Query classification   │  │
│  │  • History windowing      • Telemetry injection    │  │
│  └──┬──────────────────────────────────────────────┬─┘  │
│     │                                              │     │
│  ┌──▼────────────┐           ┌─────────────────────▼──┐ │
│  │  LLM Client   │           │ Diagnostics Engine     │ │
│  │  ┌──────────┐ │           │ ┌─────────┐ ┌───────┐ │ │
│  │  │ Qwen3-VL │ │           │ │perfSONAR│ │Tracer │ │ │
│  │  │ GLM-4.7  │ │           │ │ Client  │ │ oute  │ │ │
│  │  │ GPT-OSS  │ │           │ └─────────┘ └───────┘ │ │
│  │  └──────────┘ │           │ ┌─────────────────────┐│ │
│  │  Prompt Engine│           │ │ Anomaly Detector    ││ │
│  └───────┬───────┘           │ └─────────────────────┘│ │
│          │                   └────────────┬───────────┘ │
└──────────┼────────────────────────────────┼─────────────┘
           │                                │
    ┌──────▼──────┐                ┌────────▼────────┐
    │  NRP LLM    │                │   perfSONAR     │
    │  Service    │                │   Measurement   │
    │  (Nautilus) │                │   Archive       │
    └─────────────┘                └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/Mohammed-Anirudh/NETAI-LLM-Integration-Chatbot.git
cd NETAI-LLM-Integration-Chatbot

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env

# Run the application (uses mock data by default)
make run
```

The chatbot will be available at **http://localhost:8000** with:
- 💬 Chat UI at `/static/index.html`
- 📚 API docs at `/docs`
- 📊 Network dashboard via API endpoints

### Docker

```bash
# Build and run with Docker Compose
docker compose up --build

# Or build manually
docker build -t netai-chatbot:latest .
docker run -p 8000:8000 netai-chatbot:latest
```

### With NRP LLM Service

To use real NRP LLM models, set your API key:

```bash
export LLM_API_KEY=your-nrp-api-key
export LLM_API_BASE_URL=https://llm.nrp-nautilus.io/v1
export ENABLE_MOCK_DATA=false
make run
```

## 📡 API Reference

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/chat/` | Send a message and get AI response |
| `POST` | `/api/v1/chat/stream` | Stream response via SSE |
| `GET` | `/api/v1/chat/conversations` | List active conversations |
| `GET` | `/api/v1/chat/conversations/{id}` | Get conversation history |
| `DELETE` | `/api/v1/chat/conversations/{id}` | Delete a conversation |

### Network Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/network/summary` | Network health overview |
| `POST` | `/api/v1/network/diagnostics` | Path-specific diagnostics |
| `POST` | `/api/v1/network/traceroute` | Run traceroute |
| `GET` | `/api/v1/network/nodes` | List NRP nodes |
| `GET` | `/api/v1/network/paths/{src}/{dst}` | Path health metrics |

### Example: Send a Chat Message

```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current throughput between San Diego and Chicago?",
    "model": "qwen3-vl",
    "source": "sdsc-prp.ucsd.edu",
    "destination": "nrp-chi.uchicago.edu"
  }'
```

### Example: Network Diagnostics

```bash
curl -X POST http://localhost:8000/api/v1/network/diagnostics \
  -H "Content-Type: application/json" \
  -d '{
    "source": "sdsc-prp.ucsd.edu",
    "destination": "nrp-chi.uchicago.edu"
  }'
```

## ☸️ Deployment

### Kubernetes (Raw Manifests)

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
kubectl apply -f k8s/hpa.yaml

# Optional: GPU inference pod for self-hosted models
kubectl apply -f k8s/gpu-inference.yaml
```

### Helm Chart

```bash
# Install
helm install netai-chatbot helm/netai-chatbot/ \
  --namespace netai --create-namespace \
  --set secrets.llmApiKey=your-api-key

# Upgrade
helm upgrade netai-chatbot helm/netai-chatbot/ \
  --namespace netai \
  --set image.tag=v0.2.0

# Uninstall
helm uninstall netai-chatbot --namespace netai
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_API_BASE_URL` | `https://llm.nrp-nautilus.io/v1` | NRP LLM service endpoint |
| `LLM_API_KEY` | — | API key for NRP LLM service |
| `LLM_DEFAULT_MODEL` | `qwen3-vl` | Default model (qwen3-vl, glm-4.7, gpt-oss) |
| `ENABLE_MOCK_DATA` | `true` | Use simulated data for development |
| `PERFSONAR_URL` | — | perfSONAR measurement archive URL |
| `APP_PORT` | `8000` | Application port |
| `APP_LOG_LEVEL` | `info` | Log level |

## 🧪 Testing

```bash
# Run full test suite with coverage
make test

# Quick tests without coverage
make test-quick

# Lint
make lint

# Format code
make format
```

### Test Coverage

The test suite covers:
- ✅ **API endpoints** — Chat, network telemetry, health checks
- ✅ **LLM client** — Mock responses, model selection, usage stats
- ✅ **Prompt engine** — Query classification, template rendering, context building
- ✅ **Diagnostics** — perfSONAR data, traceroute analysis, anomaly detection
- ✅ **Context manager** — Conversation lifecycle, history windowing, telemetry injection

## 📁 Project Structure

```
├── src/netai_chatbot/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration (pydantic-settings)
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py         # Chat endpoints
│   │   │   ├── health.py       # K8s health probes
│   │   │   └── telemetry.py    # Network telemetry endpoints
│   │   ├── models/             # Pydantic request/response models
│   │   └── middleware.py       # CORS configuration
│   ├── llm/
│   │   ├── client.py           # LLM API client (OpenAI-compatible)
│   │   ├── providers.py        # NRP model configurations
│   │   └── prompt_engine.py    # Prompt engineering strategies
│   ├── diagnostics/
│   │   ├── perfsonar.py        # perfSONAR data integration
│   │   ├── traceroute.py       # Traceroute analysis
│   │   ├── anomaly.py          # Anomaly detection
│   │   └── telemetry.py        # Telemetry processing
│   ├── context/
│   │   └── manager.py          # Conversation context manager
│   └── utils/                  # Logging utilities
├── static/                     # Web UI (HTML/CSS/JS)
├── tests/                      # Comprehensive test suite
├── k8s/                        # Kubernetes manifests
├── helm/netai-chatbot/         # Helm chart
├── Dockerfile                  # Multi-stage container build
├── docker-compose.yml          # Local development setup
└── docs/                       # Documentation
```

## 🛠 Technologies

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.11+, FastAPI, Pydantic, uvicorn |
| **LLM** | OpenAI-compatible API, Qwen3-VL, GLM-4.7, GPT-OSS |
| **Diagnostics** | perfSONAR, traceroute analysis, statistical anomaly detection |
| **Infrastructure** | Kubernetes, Helm, Docker, GPU pods (NVIDIA) |
| **Testing** | pytest, pytest-asyncio, pytest-cov, httpx |
| **Quality** | ruff (lint/format), mypy (type checking), structlog |

## 🎯 GSoC 2026 Proposal

This prototype demonstrates the core capabilities outlined in the **NETAI / LLM Integration & Kubernetes Chatbot** GSoC 2026 project:

- ✅ Kubernetes-native chatbot with REST API
- ✅ Integration with NRP's managed LLM service (OpenAI-compatible)
- ✅ Multi-model support (Qwen3-VL, GLM-4.7, GPT-OSS)
- ✅ Domain-specific prompt engineering for network diagnostics
- ✅ Context-aware responses with network telemetry injection
- ✅ perfSONAR measurement data integration
- ✅ Traceroute path analysis
- ✅ Anomaly detection and explanation
- ✅ Streaming responses (SSE)
- ✅ Conversation session management
- ✅ Kubernetes deployment manifests + Helm chart
- ✅ GPU inference pod configuration
- ✅ Docker containerization
- ✅ Comprehensive test suite
- ✅ Web-based chat interface

**Mentors:** Dmitry Mishin, Derek Weitzel

## 📄 License

Apache License 2.0 — See [LICENSE](LICENSE) for details.

---

<div align="center">
<strong>Built for GSoC 2026 • National Research Platform</strong>
</div>
