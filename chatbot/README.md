# FinanceAI - Financial Analysis Chatbot

A modern, production-grade financial chatbot with a RAG (Retrieval Augmented Generation) architecture using SQLite + ChromaDB + Gemini LLM.

## Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React + Vite)         │
│  ├─ Tailwind CSS (styling)              │
│  ├─ Recharts (beautiful charts)         │
│  └─ Axios (API client)                  │
└────────────────┬────────────────────────┘
                 │ HTTP / WebSocket
                 ↓
┌─────────────────────────────────────────┐
│      Backend (Flask + Python)           │
│  ├─ RAG Engine (Gemini LLM)             │
│  ├─ ChromaDB (semantic search)          │
│  ├─ SQLite (precise queries)            │
│  └─ REST API (FastAPI-like)             │
└─────────────────────────────────────────┘
```

## Quick Start

### 1. Setup Backend

```bash
cd backend

# Create virtual environment (if not already done)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Development server (with hot reload)
npm run dev

# Build for production
npm run build
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
cd backend
source ../venv/bin/activate
python api.py
# Server runs on http://localhost:5000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Dev server runs on http://localhost:3000
```

Visit `http://localhost:3000` in your browser.

## Environment Setup

### Backend (.env)

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_TYPE=sqlite
# Optional: customize paths
# DB_PATH=../data/financial_analyzer.db
# CHROMA_PATH=./chroma_db
```

Get a Gemini API key:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Add to `.env`

## Project Structure

```
chatbot/
├── backend/
│   ├── api.py              # Flask REST API server
│   ├── config.py           # Configuration & constants
│   ├── db_client.py        # SQLite database client
│   ├── rag_engine.py       # RAG pipeline + Gemini integration
│   ├── vector_sync.py      # ChromaDB synchronization
│   ├── requirements.txt    # Python dependencies
│   ├── .env.example        # Environment template
│   └── .gitignore
│
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── App.jsx
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ChatArea.jsx
│   │   │   ├── Message.jsx
│   │   │   ├── ChartDisplay.jsx
│   │   │   └── InputArea.jsx
│   │   ├── hooks/          # Custom React hooks
│   │   │   └── useChat.js
│   │   ├── services/       # API client
│   │   │   └── api.js
│   │   ├── styles/         # Tailwind CSS
│   │   │   └── globals.css
│   │   ├── main.jsx        # React entry point
│   │   └── App.jsx         # Root component
│   ├── public/             # Static assets
│   ├── index.html          # HTML template
│   ├── vite.config.js      # Vite configuration
│   ├── tailwind.config.js  # Tailwind configuration
│   ├── package.json        # Node dependencies
│   └── .gitignore
│
└── README.md (this file)
```

## Features

### Backend (RAG Architecture)

- **Semantic Search**: ChromaDB with Sentence-Transformers embeddings
- **Precise Queries**: SQLite for exact financial metrics
- **LLM Integration**: Google Gemini for natural language responses
- **Context Assembly**: Hybrid retrieval system
- **Chart Generation**: 6 chart types (line, bar, radar, etc.)
- **Conversation History**: Per-session message tracking

### Frontend (Modern UI)

- **Real-time Chat**: Message streaming with loading indicators
- **Interactive Charts**: Recharts visualizations (line, bar, radar)
- **Dark/Light Mode**: Theme toggle with persistence
- **Responsive Design**: Works on desktop, tablet, mobile
- **Markdown Support**: Formatted responses with code blocks
- **Source Citations**: Display data sources for transparency

## API Endpoints

### Chat

```
POST /api/chat
Body: { message: string, session_id?: string }
Response: {
  response: string,
  chart?: { type, data, title },
  sources: Array,
  category: string,
  timestamp: ISO8601
}
```

### Companies

```
GET /api/companies
Response: { companies: Array, count: number }

GET /api/metrics/<ticker>
Response: { ticker, revenue, net_income, ... }

GET /api/comparison
Response: { comparison_data: Array, count: number }
```

### Utilities

```
GET /health
POST /api/chat/reset
POST /api/search
```

## Development

### Adding a New Chart Type

1. Update `backend/config.py` - Add chart config
2. Update `backend/api.py` - Add chart generation logic
3. Update `frontend/src/components/ChartDisplay.jsx` - Add Recharts rendering

### Adding a New Database Query

1. Add method to `backend/db_client.py`
2. Use in `backend/rag_engine.py` or `backend/api.py`
3. Call from frontend via `frontend/src/services/api.js`

### Styling

Frontend uses **Tailwind CSS** with custom dark theme variables:
- Colors in `frontend/tailwind.config.js`
- Global styles in `frontend/src/styles/globals.css`

## Performance

- **Backend**: Single-threaded Flask (production: use Gunicorn)
- **Frontend**: Vite production build (~150KB gzipped)
- **Database**: SQLite with indexes on common queries
- **Vector DB**: ChromaDB with cosine similarity search
- **LLM**: Gemini 2.0 Flash (~500ms response time)

## Production Deployment

### Backend

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

### Frontend

```bash
# Build
npm run build

# Serve dist/ folder with nginx/apache
# Or use Flask to serve built files
```

### Docker (Optional)

Create `Dockerfile` for containerized deployment.

## Troubleshooting

**Frontend can't connect to backend:**
- Make sure backend is running on port 5000
- Check CORS in `backend/api.py`
- Check proxy in `frontend/vite.config.js`

**Gemini API key error:**
- Verify `GEMINI_API_KEY` in `.env`
- Check quota at [Google AI Studio](https://aistudio.google.com/app/apikey)

**ChromaDB errors:**
- Delete `backend/chroma_db/` folder
- Re-run backend to re-sync

**Chart not rendering:**
- Check browser console for errors
- Verify chart data format in API response

## Technologies

**Backend:**
- Flask 3.0 (REST API)
- Python 3.10+
- SQLite (relational DB)
- ChromaDB (vector DB)
- Gemini LLM (via google-generativeai)
- Sentence-Transformers (embeddings)

**Frontend:**
- React 18 (UI library)
- Vite 5 (build tool)
- Tailwind CSS 3 (styling)
- Recharts 2 (charts)
- Axios (HTTP client)
- React Markdown (rich text)

## Contributing

Professional standards:
- ✅ Separate backend/frontend clearly
- ✅ Type hints in Python
- ✅ ESLint in JavaScript
- ✅ Meaningful commit messages
- ✅ Environment variables for secrets
- ✅ Comprehensive error handling

## License

Forage BCG GenAI Simulation

---

**Last Updated:** April 2026  
**Status:** Production-ready
