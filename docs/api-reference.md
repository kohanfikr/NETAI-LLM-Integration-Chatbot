# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

The API does not currently require authentication for development. In production,
the Kubernetes Ingress handles authentication via NRP's identity provider.

---

## Chat Endpoints

### POST /api/v1/chat/

Send a message to the NETAI chatbot.

**Request Body:**
```json
{
  "message": "What is the current throughput between San Diego and Chicago?",
  "conversation_id": "optional-uuid",
  "model": "qwen3-vl",
  "source": "sdsc-prp.ucsd.edu",
  "destination": "nrp-chi.uchicago.edu",
  "stream": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | Yes | User's message (1-4096 chars) |
| `conversation_id` | string | No | Session ID (auto-created if omitted) |
| `model` | string | No | Model override: `qwen3-vl`, `glm-4.7`, `gpt-oss` |
| `source` | string | No | Network source endpoint for context |
| `destination` | string | No | Network destination endpoint for context |
| `stream` | bool | No | Enable SSE streaming (default: false) |

**Response (200):**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": {
    "role": "assistant",
    "content": "## Throughput Analysis\n\nBased on current telemetry...",
    "timestamp": "2026-02-28T04:00:00Z"
  },
  "model": "qwen3-vl",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 300,
    "total_tokens": 450
  }
}
```

### POST /api/v1/chat/stream

Stream a chatbot response via Server-Sent Events.

Uses the same request body as `/api/v1/chat/`. Returns `text/event-stream`:

```
data: ## Throughput

data:  Analysis

data: [DONE]
```

### GET /api/v1/chat/conversations

List all active conversation sessions.

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "message_count": 5,
    "created_at": "2026-02-28T04:00:00Z"
  }
]
```

### GET /api/v1/chat/conversations/{conversation_id}

Get full conversation history.

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "message_count": 4,
  "created_at": "2026-02-28T04:00:00Z",
  "messages": [
    {"role": "user", "content": "Hello", "timestamp": "..."},
    {"role": "assistant", "content": "Hi! How can I help?", "timestamp": "..."}
  ]
}
```

### DELETE /api/v1/chat/conversations/{conversation_id}

Delete a conversation session.

**Response (200):**
```json
{"status": "deleted", "conversation_id": "..."}
```

---

## Network Endpoints

### GET /api/v1/network/summary

Get network health overview across all monitored paths.

**Response (200):**
```json
{
  "timestamp": "2026-02-28T04:00:00Z",
  "total_paths": 5,
  "healthy": 3,
  "degraded": 1,
  "warning": 1,
  "critical": 0,
  "paths": [
    {
      "source": "sdsc-prp.ucsd.edu",
      "destination": "fiona-10g.ucsd.edu",
      "throughput_gbps": 8.5,
      "latency_ms": 12.3,
      "packet_loss_pct": 0.0,
      "health_status": "healthy"
    }
  ]
}
```

### POST /api/v1/network/diagnostics

Run comprehensive diagnostics for a specific network path.

**Request Body:**
```json
{
  "source": "sdsc-prp.ucsd.edu",
  "destination": "nrp-chi.uchicago.edu"
}
```

**Response (200):**
```json
{
  "path": { "source": "...", "health_status": "warning", ... },
  "traceroute": { "hop_count": 7, "hops": [...], ... },
  "anomalies": [{ "type": "latency_spike", "severity": "medium", ... }],
  "measurement_count": { "throughput": 96, "latency": 1440 }
}
```

### POST /api/v1/network/traceroute

Execute a traceroute between two endpoints.

**Request Body:**
```json
{
  "source": "sdsc-prp.ucsd.edu",
  "destination": "nrp-chi.uchicago.edu"
}
```

### GET /api/v1/network/nodes

List available NRP network nodes.

### GET /api/v1/network/paths/{source}/{destination}

Get health metrics for a specific path.

---

## Health Endpoints

### GET /healthz
Kubernetes liveness probe. Returns `{"status": "ok"}`.

### GET /readyz
Kubernetes readiness probe. Returns `{"status": "ready", "version": "..."}`.

### GET /api/v1/info
Service information including available models and endpoints.

---

## Error Responses

All errors follow a standard format:

```json
{
  "detail": "Error description"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request (invalid model, missing fields) |
| 404 | Resource not found (conversation) |
| 422 | Validation error (empty message, too long) |
| 500 | Internal server error |
| 502 | LLM service error |
| 503 | Service not initialized |
