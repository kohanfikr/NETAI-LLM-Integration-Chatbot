# Architecture

## System Overview

NETAI is a Kubernetes-native chatbot that provides AI-powered network diagnostics
assistance for the National Research Platform (NRP). The system integrates with
NRP's managed LLM service and perfSONAR network measurements to deliver
context-aware, intelligent responses to network operators.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Web UI     │  │  REST API    │  │  SSE Streaming   │  │
│  │  (Chat)      │  │  Clients     │  │  Clients         │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼────────────────────┼────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Middleware: CORS, Rate Limiting, Request Logging        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ /chat/*  │  │ /network/*   │  │ /healthz, /readyz    │  │
│  │ Chat API │  │ Telemetry API│  │ K8s Health Probes    │  │
│  └────┬─────┘  └──────┬───────┘  └──────────────────────┘  │
└───────┼───────────────┼──────────────────────────────────────┘
        │               │
        ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                      │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Context Manager                           │  │
│  │  - Conversation session lifecycle                     │  │
│  │  - Sliding window history management                  │  │
│  │  - Query classification                               │  │
│  │  - Network telemetry context injection                │  │
│  └───┬───────────────────────────────────────────────┬───┘  │
│      │                                               │       │
│  ┌───▼───────────────┐          ┌────────────────────▼────┐ │
│  │   LLM Module      │          │  Diagnostics Engine     │ │
│  │                    │          │                         │ │
│  │  ┌──────────────┐ │          │  ┌──────────────────┐   │ │
│  │  │ LLM Client   │ │          │  │ perfSONAR Client │   │ │
│  │  │ (OpenAI API) │ │          │  │ (Throughput,     │   │ │
│  │  └──────────────┘ │          │  │  Latency, Loss)  │   │ │
│  │                    │          │  └──────────────────┘   │ │
│  │  ┌──────────────┐ │          │  ┌──────────────────┐   │ │
│  │  │ Prompt Engine│ │          │  │ Traceroute       │   │ │
│  │  │ (Templates,  │ │          │  │ Analyzer         │   │ │
│  │  │  Classifier) │ │          │  └──────────────────┘   │ │
│  │  └──────────────┘ │          │  ┌──────────────────┐   │ │
│  │                    │          │  │ Anomaly Detector │   │ │
│  │  ┌──────────────┐ │          │  │ (Threshold +     │   │ │
│  │  │ Providers    │ │          │  │  Statistical)    │   │ │
│  │  │ (Qwen3-VL,  │ │          │  └──────────────────┘   │ │
│  │  │  GLM-4.7,   │ │          │  ┌──────────────────┐   │ │
│  │  │  GPT-OSS)   │ │          │  │ Telemetry        │   │ │
│  │  └──────────────┘ │          │  │ Processor        │   │ │
│  └───────────────────┘          │  └──────────────────┘   │ │
│                                 └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
        │                                    │
        ▼                                    ▼
┌───────────────────┐          ┌─────────────────────────────┐
│   NRP LLM Service │          │  perfSONAR Measurement      │
│   (Nautilus K8s)  │          │  Archive (MA) / Network     │
│                   │          │  Telemetry Sources           │
│  - Qwen3-VL      │          │                              │
│  - GLM-4.7       │          │  - Throughput (iperf3)       │
│  - GPT-OSS       │          │  - Latency (owping)          │
└───────────────────┘          │  - Traceroute (paris-tr.)    │
                               └─────────────────────────────┘
```

## Data Flow

### Chat Request Flow
1. User sends message via Web UI or REST API
2. **Context Manager** classifies the query (anomaly, remediation, telemetry, general)
3. Selects optimal **Prompt Template** based on classification
4. Fetches current **Network Telemetry** for context injection
5. Builds complete message list with system prompt + history + telemetry + user message
6. **LLM Client** sends request to NRP's managed LLM service
7. Response is recorded in conversation history and returned to user

### Telemetry Context Injection
The system automatically enriches LLM prompts with real-time network data:
- Current throughput, latency, packet loss for relevant paths
- Active anomalies detected by the anomaly detector
- Traceroute results showing path-level issues
- Network health summary across all monitored paths

## Kubernetes Deployment

```
┌─ Namespace: netai ──────────────────────────────────────────┐
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Deployment: netai-chatbot (replicas: 2-10)          │    │
│  │ ┌─────────────┐  ┌─────────────┐                   │    │
│  │ │  Pod        │  │  Pod        │   ← HPA auto-     │    │
│  │ │  chatbot    │  │  chatbot    │      scales        │    │
│  │ └─────────────┘  └─────────────┘                   │    │
│  └─────────────────────────────────────────────────────┘    │
│                          ▲                                   │
│  ┌───────────────────────┴─────────────────────────────┐    │
│  │ Service: netai-chatbot (ClusterIP :80)              │    │
│  └───────────────────────┬─────────────────────────────┘    │
│                          ▲                                   │
│  ┌───────────────────────┴─────────────────────────────┐    │
│  │ Ingress: netai-chatbot.nrp-nautilus.io (TLS)        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Optional: GPU Inference Pod (nvidia.com/gpu: 1)     │    │
│  │ For self-hosted LLM inference on NRP GPUs           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ConfigMap │ Secret │ ServiceAccount │ HPA                   │
└──────────────────────────────────────────────────────────────┘
```

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Web framework | FastAPI | Async support, auto-docs, Pydantic integration |
| LLM API format | OpenAI-compatible | NRP's service uses this format |
| Config management | pydantic-settings | Type-safe, env var loading, validation |
| HTTP client | httpx | Async support, streaming, modern API |
| Logging | structlog | Structured logging for K8s observability |
| Testing | pytest-asyncio | Native async test support |
| Linting | ruff | Fast, comprehensive Python linting |
| Container | Multi-stage Docker | Small image size, non-root user |
| K8s packaging | Helm | Industry standard, configurable deployments |
