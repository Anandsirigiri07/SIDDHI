# SIDDHI (Situational Intelligence Dashboard for Dynamic Hotspot Investigation)

SIDDHI is a next-generation AI-powered Multilingual Crime Intelligence and Investigative Analysis platform. Designed for modern fusion centers and law enforcement command-and-control operations, it transforms raw police records into structured, actionable intelligence.

---

## 1. Problem Statement
Modern law enforcement agencies are inundated with vast amounts of unstructured or semi-structured data (FIRs, accused profiles, witness statements). Traditional database management and crime query systems fail to:
- **Track Association Networks:** Manually identifying co-accused networks, gang modularity, and accomplice structures is slow and error-prone.
- **Correlate Geo-Temporal Data:** Traditional query tools fail to dynamically link geographic crime distributions with temporal spikes and trend migrations.
- **Support Localized Operators:** Most analytical platforms lack localized multilingual support (e.g., Kannada speech-to-text and back-translation) for field police personnel.
- **Enforce Secure Database Queries:** Providing raw SQL query access to analysts risks database injection, data tampering, or performance bottlenecks.

---

## 2. Solution Overview
SIDDHI addresses these challenges by combining a secure FastAPI backend, a responsive React 18 frontend, and the analytical power of the Gemini 2.5 Flash API to deliver a unified, triple-lens investigative pipeline:

- **Lens 1: Conversational Chat:** Dynamic natural language queries (English or Kannada) are translated, classified by intent, converted to secure read-only SQL, executed, and compiled into evidence-backed summaries with strict FIR citations.
- **Lens 2: Interactive D3.js Network Graph:** Renders real-time, 2-hop co-accused association networks, highlighting PageRank centrality, Louvain community modularity, and identifying critical "Bridge Suspects."
- **Lens 3: Leaflet Geographic Heatmap:** Clusters crime locations using DBSCAN density-based spatial analysis, computes localized risk scores, and broadcasts real-time hotspot spike alerts.

---

## 3. Triple-Lens Architecture & Data Flow

```
                       +-------------------------+
                       |      User Browser       |
                       +------------+------------+
                                    |
                                    v
                       +------------+------------+
                       |    React 18 Frontend    |
                       +------------+------------+
                                    | (HTTPS + JWT + WebSockets)
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

### Detailed Execution Pipeline
1. **Ingestion & Translation Layer (`translator.py`):** The system detects the input language. If the query contains Kannada characters (verified using Unicode block checks `U+0C80` to `U+0CFF` and `langdetect`), it translates the prompt to English.
2. **Intent Classification (`gemini_client.py`):** Gemini classifies the query intent (`RECORD_LOOKUP`, `NETWORK_ANALYSIS`, `PATTERN_ANALYSIS`, `PROFILING`, `FORECASTING`, `GENERAL`), extracts entities (locations, crime types, accused, time ranges), and tracks conversational history in a session memory buffer.
3. **NL-to-SQL Conversion (`gemini_client.py`):** Translates the English query into a read-only SQLite SELECT query utilizing cached database schema representations.
4. **SQL Security Guard (`sql_guard.py`):** Hardens database access by running the query through a security filter:
   - **Command Whitelisting:** Blocks write operations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `ATTACH`, `PRAGMA`).
   - **Table Whitelisting:** Restricts queries exclusively to permitted tables.
   - **Limit Enforcement:** Automatically rewrites queries to append `LIMIT 100` if no limit is defined.
5. **Execution & Evidence Assembly (`evidence_assembler.py`):** Executes queries on the SQLite database.
   - Scans output text for citation patterns (e.g., `[FIR-2026-00102]`).
   - Verifies the validity of citations against executed SQL rows, automatically stripping hallucinated citations or appending valid citation badges to ensure strict audit integrity.
6. **Network Graph & Pattern Extraction:** Sends the SQL results to the D3 and Leaflet adapters for visual layout compilation.
7. **Back-Translation:** If the initial input language was Kannada, the compiled English summary is translated back to Kannada before rendering in the browser.

---

## 4. Key Features

### 4.1. Conversational Crime Analytics
- **Explainable SQL:** Displays the generated SQL query along with an natural-language explanation of the database logic.
- **Multilingual Support:** Seamlessly translate Kannada input and speech to English, processing it through the pipeline, and back-translating compiled summaries.
- **Voice Capabilities:** Microphone inputs for hands-free speech-to-text queries, combined with Text-to-Speech (TTS) readouts of reports.

### 4.2. Advanced Visual Analytics
- **2-Hop Network Graph:** Automatically parses query results to build co-accused association networks. Performs PageRank centrality to size nodes (identifying key network actors) and Louvain community detection to segment accomplice groups.
- **Bridge Suspect Identification:** Highlights "bridge" individuals—accused who connect crimes across multiple distinct Louvain communities and have a non-zero betweenness centrality.
- **Geographic DBSCAN Heatmap:** Performs density-based spatial clustering (EPS = ~0.5km) to map crime hotspots. Calculates hotspot risk levels based on incident counts, recent temporal frequency, crime severity weights, and repeat offender presence.
- **Real-Time Spike Alerts:** Triggers alerts over WebSockets if the crime volume in a cluster over the last 7 days significantly exceeds historical weekly averages.
- **Temporal Timeline Playback:** Dynamically filter and play back crime incidents chronologically, showing how network graphs evolve and how hotspots migrate over time.

### 4.3. Document Ingestion Pipeline
- **Multimodal Document Parsing:** Upload scanned FIR images or PDF case files. The backend utilizes Gemini Multimodal prompts to parse structured fields (FIR number, date, crime type, location, officers, accused, victims) from raw files.
- **Human-in-the-Loop Verification:** Renders parsed data on a correction draft panel, allowing operators to verify, edit, and validate fields prior to database insertion.
- **Validation Engine:** Enforces strict structural checks (valid ISO dates, whitelisted crime categories, non-empty fields) and automatically recalculates accused risk scores (`firs_count * 12.5`) upon confirmation.

### 4.4. Production Resilience & Security
- **API Key Rotation & Quota Resilience:** Supports multiple Gemini API key variables (`GEMINI_API_KEY`, `GEMINI_API_KEY_BACKUP`, etc.). If a key hits rate limits (429 ResourceExhausted), the backend automatically rotates to the next key.
- **Caching Layer:** SQLite caching table (`gemini_cache`) stores prompt hashes, system instructions, and response data to prevent duplicate LLM calls and reduce API costs.
- **Uptime Assurance Fallback:** If all keys are rate-limited or unavailable, the system transparently falls back to an internal rule-based simulated generator, maintaining platform availability.
- **Supervisory Audit Logs:** Restricts access to audit trail views to `Supervisor` roles, recording detailed execution metrics (username, timestamp, raw query, generated SQL, execution time, returned row count) for compliance.
- **One-Click PDF Export:** Downloads standardized A4 intelligence dossiers including summary texts, network graph snapshots, and Leaflet maps.

---

## 5. Technology Stack
- **Frontend:** React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, jsPDF, html2canvas.
- **Visualizations:** D3.js (Force-directed network simulation), Leaflet (Interactive mapping & marker clustering).
- **Backend:** FastAPI, SQLAlchemy, SQLite, Uvicorn, Python 3.10+.
- **AI Intelligence:** Gemini 2.5 Flash (`google-generativeai` SDK).
- **Data Engineering:** NetworkX (PageRank, Betweenness Centrality, Louvain Communities), Scikit-Learn (DBSCAN Clustering), NumPy, Langdetect.

---

## 6. Database Schema
The SQLite database (`siddhi.db`) contains the following structured tables:

| Table Name | Primary Key | Key Columns / Foreign Keys | Description |
| :--- | :--- | :--- | :--- |
| **`users`** | `user_id` | `username` (unique), `password_hash`, `role`, `name` | Handles credentials and RBAC roles. |
| **`locations`** | `location_id` | `name`, `lat`, `lng`, `district`, `station_area` | Geographic coordinate lookups. |
| **`officers`** | `officer_id` | `name`, `rank`, `station` | Investigating officer records. |
| **`firs`** | `fir_id` | `fir_number` (unique), `date`, `crime_type`, `location_id` (FK), `officer_id` (FK) | Core FIR incident details. |
| **`accused`** | `accused_id` | `name`, `age`, `gender`, `occupation`, `risk_score` | Crime suspect details and computed risk. |
| **`fir_accused`** | `(fir_id, accused_id)` | `fir_id` (FK), `accused_id` (FK), `role` | Maps accused roles in specific FIRs. |
| **`victims`** | `victim_id` | `fir_id` (FK), `name`, `age`, `gender` | Crime victim details. |
| **`audit_logs`** | `log_id` | `user_id` (FK), `query`, `generated_sql`, `execution_time` | Compliance audit trials. |
| **`gemini_cache`**| `cache_key` | `prompt`, `system_instruction`, `response_text` | Caching database for token optimization. |

### Indexes Enforced
- `idx_firs_crime_type` on `firs(crime_type)`
- `idx_firs_date` on `firs(date)`
- `idx_locations_lat_lng` on `locations(lat, lng)`
- `idx_fir_accused_accused_id` on `fir_accused(accused_id)`
- `idx_fir_accused_fir_id` on `fir_accused(fir_id)`
- `idx_victims_fir_id` on `victims(fir_id)`

---

## 7. Role-Based Access Control (RBAC)
User permissions are strictly enforced at the API route layer:

| Username / Role | Access Level & Capabilities |
| :--- | :--- |
| **`analyst`** (Analyst) | Co-accused association network graph navigation, DBSCAN hotspot analysis, conversational query, case profile views. |
| **`investigator`** (Investigator) | Access to specific case profiles, dossier generation modal, scanned FIR document ingestion & multimodal review. |
| **`supervisor`** (Supervisor) | Comprehensive query analytics, case notes ingestion, and full access to query audit trails & logs. |
| **`policymaker`** (Policymaker) | Query-level access to aggregate trends, forecasts, and geo-spatial hotspots. (Restricted from detailed individual case profiling). |

---

## 8. Backend Setup & Run Guide

1. **Navigate to the Backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the `backend/` directory:
   ```env
   GEMINI_API_KEY=your_primary_key_here
   GEMINI_API_KEY_BACKUP=your_backup_key_here
   GEMINI_MODEL=gemini-2.5-flash

   # Token secret for user session verification
   # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
   JWT_SECRET_KEY=some_long_and_secure_random_string_key
   
   # Enable demo users for local debugging
   SEED_DEMO_USERS=true
   DEMO_USER_PASSWORD=password123
   ```
   *Note: The backend will fail to start if `JWT_SECRET_KEY` is missing or is under 12 characters.*

4. **Initialize and Seed the Database:**
   ```bash
   python seed.py
   ```
   *This initializes `siddhi.db`, loads the schema, and inserts mock police logs (FIRs, accused, locations) centered around Bengaluru neighborhoods.*

5. **Run Verification Suite:**
   ```bash
   python verify_backend.py
   ```
   *Validates database structures, runs authentication tests, checks intent classification, and executes a mock query validation pipeline to verify frontend readiness.*

6. **Start the FastAPI Dev Server:**
   ```bash
   python -m uvicorn main:app --port 8000 --host 127.0.0.1
   ```

---

## 9. Frontend Setup & Run Guide

1. **Navigate to the Frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install node packages:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   Open [http://localhost:5173](http://localhost:5173) in your browser. Log in using `analyst` / `password123` (or any other role defined in the Seeding configuration).

---

## 10. Future Roadmap
- **Live OCR Integration:** Scan hand-written police FIR reports directly using mobile camera inputs.
- **Multimodal Video Processing:** Ingest traffic CCTV video clips to detect suspect vehicles matching license plate parameters.
- **Predictive Hotspot Forecasting:** Train heavier temporal models (LSTM/Facebook Prophet) to forecast crime migrations week-over-week.

---

## 11. Team Information
Developed by Team SIDDHI.
- Hackathon Project - 2026.
