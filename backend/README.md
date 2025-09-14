# Northwind Sales Chatbot — Full (Frontend + Backend)

- **Frontend**: React + Vite + TypeScript + Tailwind + Recharts + Framer Motion + lucide-react + html-to-image
- **Backend**: FastAPI + SQLite + Groq LLM (llama-3.1-8b-instant) + Forecast (Prophet if available, else fallback)

## Run Backend
```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt
# macOS/Linux
source .venv/bin/activate && pip install -r requirements.txt

cp .env.example .env
# put your GROQ_API_KEY (or set USE_LLM=false)

uvicorn app:app --reload --port 8000
```

## Run Frontend
```bash
cd frontend
cp .env.example .env  # default VITE_API_BASE=http://localhost:8000
npm install
npm run dev
```

### Notes
- DB seeding: tries full Northwind from jpwhite3 via Python executescript; if that fails, auto-creates a **mini demo dataset** so the app always runs.
- No Docker required.