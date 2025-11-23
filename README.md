# 🌍 AI Travel Planner

AI-powered travel planner that generates **complete city itineraries in seconds**.

Given a **city, number of days, budget, preferences and simple filters**, the system returns a structured, cost-aware plan (morning / afternoon / evening for each day) with reasons and estimated costs — plus one-click export to **JSON, CSV, and PDF**. 

Built during my time at **Tips Hindawi** as a hands-on project in RAG and LLM tooling.

---

## ✨ Features

- 🧠 **RAG-based planning**
  - FAISS vector store over local attraction datasets with MiniLM embeddings.   
  - MMR retriever to select diverse, relevant places for a city.
  - Mistral-7B Instruct, 4-bit quantized (bitsandbytes) for efficient generation.   

- 🧾 **Structured, validated itineraries**
  - LangChain chain: **Retriever → Prompt → LLM → Pydantic parser**.   
  - Pydantic models (`Slot`, `DayPlan`, `Itinerary`) validate the JSON from the LLM; malformed outputs are rejected before they reach the UI.   

- 🎛️ **Smart filters**
  - Flags for **vegetarian**, **family friendly**, **avoid long walks**.   
  - Post-processing layer tweaks descriptions (e.g. replacing “long walk” with “short visit” if needed).   

- 💰 **Budget awareness**
  - Each slot has `est_cost_usd`; totals are recomputed per day and checked against user budget in the frontend.   

- 💻 **User-friendly UI (Streamlit)**
  - Simple form for destination, days, total budget, free-text preferences, and toggles.   
  - Itinerary displayed as a table with total cost per day.
  - Export options:
    - Save raw trip as **JSON**
    - Download **CSV**
    - Generate a landscape **PDF** with wrapped text using FPDF.   

---

## 🏗 Architecture

High-level architecture (as in the slides):   

1. **Frontend – Streamlit (`app.py`)**
   - Collects inputs: city, days, budget, preferences + filters.
   - Calls backend `/plan` via HTTP with a Bearer API key.
   - Renders the returned itinerary into a `pandas` DataFrame and handles export to CSV / PDF.
2. **API – FastAPI (`backend/main.py`)**
   - Auth guard using `Authorization: Bearer <API_KEY>`.
   - Uses LangChain RAG pipeline to build the itinerary.
   - Applies lightweight post-processing rules (filters, tags).
   - Returns a validated `Itinerary` JSON object.
3. **Planner Core – LangChain + FAISS (`backend/planner.py`)**
   - FAISS index over local city datasets (JSON).   
   - Retriever (MMR) chooses candidate attractions.
   - Prompt template constrains the LLM: *“Return only one JSON object. Use only retrieved places.”*   
   - Mistral-7B Instruct (4-bit) generates the itinerary.
   - Pydantic parser enforces the schema.

---
▶️ Running the project
1. Backend (FastAPI + RAG)
In a Python virtualenv
pip install -r requirements_backend.txt

cd backend
uvicorn main:app --host 0.0.0.0 --port 8000


Environment:

export PLANNER_API_KEY="secret123"       # or your own key


The API exposes:

POST /plan
Authorization: Bearer <API_KEY>
Content-Type: application/json

{
  "city": "Cairo",
  "days": 3,
  "budget": 400,
  "preferences": "history, food, markets",
  "filters": {
    "avoid_long_walks": false,
    "family_friendly": true,
    "vegetarian": false
  }
}


Response (simplified):

{
  "days": [
    {
      "day_number": 1,
      "city": "Cairo",
      "morning":   {"place": "Egyptian Museum", "reason": "...", "est_cost_usd": 15},
      "afternoon": {"place": "Khan el-Khalili", "reason": "...", "est_cost_usd": 10},
      "evening":   {"place": "Nile dinner cruise", "reason": "...", "est_cost_usd": 40}
    }
  ]
}

2. Frontend (Streamlit)
pip install -r requirements_frontend.txt

 if backend is local
export PLANNER_URL="http://localhost:8000"
export PLANNER_API_KEY="secret123"

streamlit run app.py


The UI lets you:

Enter destination, days, budget, preferences.

Toggle filters (vegetarian, family friendly, avoid long walks).

Click “Generate Itinerary” to call the API and show the table.

Save JSON / Download CSV / Export PDF.

📦 Requirements

Frontend (requirements_frontend.txt):

streamlit
pandas
requests
fpdf


Backend (requirements_backend.txt): 

fastapi
uvicorn
langchain
faiss-cpu
sentence-transformers
bitsandbytes
pydantic
python-dotenv


Adjust based on your actual backend code.

⚠️ Limitations & Roadmap

As documented in the slides:

Current limitations

Uses local datasets for attractions (no live reviews/hours).

Costs are rough estimates, not dynamic prices.

No route optimisation or transit time yet.

Single city per plan (no multi-city trips).

Future ideas

“Regenerate Day” with a ban-list of already used places.

Multi-city trips with travel time & distance balancing.

Live data from Google Places / Yelp / OpenTripMap.

Maps view with drag-to-swap activities.

User accounts + shareable links.

👤 Author

Seifeldin Elnozahy
AI & Software Engineer
Built as part of an AI engineering internship/project at Tips Hindawi.



