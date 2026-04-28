# Truthify AI — Fake News Detector Backend

> AI-powered misinformation detection API built with **FastAPI**, **Groq Cloud** (LLaMA 3.3 70B), and **Wikipedia** external verification.

---

## ✨ Features

- 🤖 **Groq Cloud inference** — ultra-fast LLaMA 3.3 70B via Groq API
- 📰 **Three analysis modes** — Text, URL (newspaper3k extraction), Image
- 🌐 **Wikipedia verification** — auto-fetches context for factual grounding
- 🏷️ **Rich verdicts** — `REAL`, `FAKE`, or `MISLEADING` with confidence score
- ⚡ **In-memory caching** — TTL-based LRU cache (10 min, 200 entries)
- 🪪 **Request-ID logging** — structured logs with per-request tracing
- 🔒 **Environment-based config** — no hardcoded secrets

---

## 📁 Project Structure

```
backend/
├── main.py                  # FastAPI app factory + middleware
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── routes/
│   └── analyze.py           # /analyze/text, /analyze/url, /analyze/image
├── services/
│   ├── ai_service.py        # Groq Cloud LLM inference
│   └── verification.py      # Wikipedia keyword lookup
└── utils/
    ├── logger.py            # Structured logging with request-ID
    └── cache.py             # In-memory LRU cache with TTL
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/sainidev1211/Fake-news-detector-Backend.git
cd Fake-news-detector-Backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get a free Groq API key at: https://console.groq.com/keys

`.env`:
```
GROQ_API_KEY=gsk_your_key_here
```

### 3. Run the Server

```bash
python main.py
```

API will be live at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server status + model info |
| `POST` | `/analyze/text` | Analyze raw news text |
| `POST` | `/analyze/url` | Analyze article from URL |
| `POST` | `/analyze/image` | Analyze uploaded image |

### Example Request

```bash
curl -X POST http://localhost:8000/analyze/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Scientists confirm moon landing was faked by NASA in 1969."}'
```

### Example Response

```json
{
  "status": "success",
  "data": {
    "claim_summary": "The 1969 Moon landing was staged by NASA.",
    "verdict": "FAKE",
    "confidence": 100,
    "red_flags": ["conspiracy language", "lack of credible sources", "exaggeration"],
    "explanation": "There is overwhelming evidence that the Moon landing was real...",
    "suggested_verification_sources": ["NASA", "Wikipedia", "Apollo 11 mission archives"],
    "wikipedia_context": "[Wikipedia – Moon landing]: ...",
    "request_id": "3c79390c",
    "cached": false,
    "latency_ms": 1964
  }
}
```

---

## ☁️ Deployment

### Render / Railway

1. Set `GROQ_API_KEY` as an environment variable in your dashboard
2. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔗 Frontend

The React frontend is at: https://github.com/sainidev1211/Fake-news-detector

---

## 📄 License

MIT
