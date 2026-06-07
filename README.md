# SIDDHI (Situational Intelligence Dashboard for Dynamic Hotspot Investigation)

SIDDHI is a next-generation AI-powered Multilingual Crime Intelligence and Investigative Analysis platform. Designed for modern fusion centers and law enforcement command-and-control operations, it transforms raw police records into structured, actionable intelligence.

---

## 1. Problem Statement
Modern law enforcement agencies are inundated with vast amounts of unstructured or semi-structured data (FIRs, accused profiles, witness statements). Traditional systems fail to:
- Dynamically track co-accused association networks.
- Connect geographic crime distributions with temporal spikes.
- Provide multilingual interfaces for localized police personnel (e.g., Kannada translation).
- Ensure secure, read-only analytical query execution without risk of database injection or tampering.

---

## 2. Solution Overview
SIDDHI solves these challenges by combining a secure FastAPI backend, a responsive React 18 frontend, and the power of the Gemini 2.5 Flash API to deliver a unified, triple-lens investigative pipeline:
- **Lens 1: Conversational Chat:** Dynamic natural language queries are parsed, secure read-only SQL is generated, and evidence-backed summaries are generated with strict FIR citations.
- **Lens 2: Interactive D3.js Network Graph:** Renders real-time co-accused association graphs using PageRank sizing and Louvain community modularity to identify gang leaders and accomplice structures.
- **Lens 3: Leaflet Geographic Heatmap:** Clusters crime hotspots using DBSCAN density analysis and flags localized crime spikes (e.g., 4 chain snatchings in 7 days).

---

## 3. Triple-Lens Architecture

```
                       +-------------------------+
                       |      User Browser       |
                       +------------+------------+
                                    |
                                    v
                       +------------+------------+
                       |    React 18 Frontend    |
                       +------------+------------+
                                    | (HTTPS + JWT)
                                    v
                       +------------+------------+
                       |     FastAPI Backend     |
                       +------------+------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------+-----------+                       +-----------+-----------+
|    Gemini API Key     |                       |    Fallback Engine    |
| (Real Gemini Execution|                       | (Rule-Based Simulation|
|  & retry capability)  |                       |  Uptime Assurance)    |
+-----------+-----------+                       +-----------+-----------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
                       +------------+------------+
                       |      SQL Guard.py       |
                       | (Write-Blocker Check &  |
                       |  LIMIT 100 Enforcer)    |
                       +------------+------------+
                                    |
                                    v
                       +------------+------------+
                       |     SQLite Database     |
                       +------------+------------+
                                    |
                                    v
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
+---------+---------+                               +---------+---------+
|   D3 Network Graph|                               |  Leaflet Heatmap  |
| (PageRank & Louvain)                              | (DBSCAN Clusters) |
+---------+---------+                               +---------+---------+
          |                                                   |
          +-------------------------+-------------------------+
                                    |
                                    v
                       +------------+------------+
                       |   Triple-Lens Response  |
                       | (Chat, Graph, Map Data) |
                       +-------------------------+
```

---

## 4. Key Features
- **Multilingual AI Interface:** Ingests Kannada text/speech, translates it to English, executes the query pipeline, and back-translates summaries back to Kannada.
- **Voice Controls:** Integrated microphone inputs for hands-free queries (speech-to-text) and TTS audio readouts.
- **Explainable SQL Generation:** Real-time translation of natural language queries to SQL with explanations, fully audited in a secure DB log.
- **PDF Intelligence Briefings:** One-click A4 exports containing summary reports, D3 graph snapshots, and Leaflet heatmap overlays.
- **Robust Failure Resilience:** Automatic 429 rate limit retries with exponential backoff, failing over seamlessly to the simulated fallback engine on API key limits.

---

## 5. Technology Stack
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, jsPDF.
- **Visualizations:** D3.js (Force Directed Simulation), Leaflet (Map tiles & density heatmaps).
- **Backend:** FastAPI, SQLAlchemy, SQLite, Uvicorn, Python 3.10+.
- **AI Intelligence:** Gemini 2.5 Flash (`google-generativeai` SDK).
- **Data Engineering:** NetworkX (graph processing), Scikit-Learn (DBSCAN), Langdetect.

---

## 6. Backend Setup

1. **Navigate to the Backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the Environment variables:**
   Create a `.env` file in the root directory (or use `.env.example`):
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   JWT_SECRET_KEY=your_jwt_secret_here
   ```

4. **Initialize and Seed the database:**
   ```bash
   python seed.py
   ```

5. **Start the FastAPI server:**
   ```bash
   python -m uvicorn main:app --port 8000 --host 127.0.0.1
   ```

---

## 7. Frontend Setup

1. **Navigate to the Frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install packages:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 8. Demo Credentials
Log in using the following credentials to access the analytical workspace:

| Username | Password | Role | Access Level |
| :--- | :--- | :--- | :--- |
| **analyst** | `password123` | Analyst | Co-accused graphs & hotspot analysis |
| **investigator** | `password123` | Investigator | Access to specific case profiles |
| **supervisor** | `password123` | Supervisor | Access to audit trails & logs |
| **policymaker** | `password123` | Policymaker | Aggregate trends & maps |

---

## 9. Future Scope
- **Live OCR Integration:** Scan hand-written police FIRs directly from mobile camera feeds.
- **Multimodal Video Processing:** Process CCTV traffic video files to detect suspect vehicle plate patterns.
- **Predictive Crime Hotspots:** Implement temporal forecasting models to predict hotspot migrations.

---

## 10. Team Information
Developed by Team SIDDHI.
- Hackathon Project - 2026.
