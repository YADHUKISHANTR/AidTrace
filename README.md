# AidTrace — Relief Investigation System

AidTrace is a graph-powered relief investigation system that helps identify discrepancies in disaster-relief distribution, trace resources across connected records, investigate missing evidence, and understand potential supply-chain irregularities.

Built with **Python, Flask, FalkorDB, Cypher, and Google Gemini**, AidTrace connects relief requests, deliveries, receipts, routes, communities, warehouses, and supplies into a graph that investigators can explore.

## Features

- **Graph-based investigation:** Trace connected relief records and identify potential discrepancies.
- **Evidence tracing:** Explore relationships between requests, deliveries, receipts, and routes.
- **Cross-centre investigation:** Examine potential inconsistencies across relief distribution centres.
- **Resource matching:** Help identify relief resources and distribution needs.
- **Interactive graph explorer:** Inspect graph nodes and their relationships.
- **Route updates:** Update route information with a recorded reason.
- **Node updates:** Edit supported graph properties with a reason for the change.
- **AI-assisted investigation:** Use Google Gemini to explain findings based on investigation evidence.
- **Multiple scenarios:** Explore the Wayanad and Assam flood-relief scenarios.

## Technology Stack

- **Backend:** Python, Flask
- **Graph database:** FalkorDB
- **Graph queries:** Cypher
- **AI:** Google Gemini API
- **Frontend:** HTML, CSS, JavaScript

## Architecture

1. Relief data is stored as connected nodes and relationships in FalkorDB.
2. The Flask backend executes Cypher queries to retrieve and investigate graph evidence.
3. The dashboard displays investigation findings, resource information, and graph relationships.
4. Google Gemini assists in explaining investigation results using the available evidence.

Deterministic graph queries handle the underlying data retrieval and investigation logic, while AI provides additional explanations.

## Graph Data Model

AidTrace represents relief-distribution information as a graph.

**Core entities**
- Communities
- Relief requests
- Deliveries
- Receipts
- Routes
- Incident reports
- Warehouses
- Supplies

These entities are connected through relationships representing the flow of relief resources, fulfilment of requests, delivery confirmation, and related incidents.

The graph structure allows AidTrace to investigate connected records instead of examining each record in isolation.

## Prerequisites

Install the following before running AidTrace:

- Python 3.10 or later
- Git
- Docker Desktop or Docker Engine
- A Google Gemini API key for AI-assisted investigation

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YADHUKISHANTR/AidTrace.git
cd AidTrace
```

### 2. Start FalkorDB

Run FalkorDB using Docker:

```bash
docker run -d \
  --name aidtrace-db \
  -p 6379:6379 \
  -p 3000:3000 \
  -v aidtrace_data:/var/lib/falkordb/data \
  falkordb/falkordb:latest
```

If the container already exists, start it with:

```bash
docker start aidtrace-db
```

The application connects to FalkorDB at `localhost:6379` and uses the graph named `aidtrace`.

FalkorDB's browser interface is available at:

```text
http://localhost:3000
```

### 3. Create a Python virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux or macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure the environment

Create a file named `.env` in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Replace the example value with your own Google Gemini API key.

Keep `.env` private and do not commit API keys to GitHub.

### 6. Initialize the graph data

Run the project's data initialization script:

```bash
python seed_graph.py
```

This initializes the graph data used by the investigation system. Use the Wayanad and Assam scenarios provided by the project to explore different relief-investigation cases.

### 7. Run the application

```bash
python app.py
```

Open the local dashboard in your browser:

```text
http://127.0.0.1:5000/
```

Keep the FalkorDB container running while using the application.

## Using AidTrace

1. Open the dashboard.
2. Select the Wayanad or Assam scenario.
3. Run an investigation to examine the connected relief records.
4. Review discrepancies, evidence, resource information, and investigation findings.
5. Explore the graph to inspect relationships between records.
6. Use supported route and node updates to record justified changes.
7. Run the AI-assisted investigation to obtain an additional explanation of the available evidence.

The scenarios use sample data for demonstration. Investigation findings indicate potential discrepancies that require verification; they do not, by themselves, establish fraud or wrongdoing.

## Project Structure

```text
AidTrace/
├── static/                  # Frontend assets
├── templates/               # Flask HTML templates
├── tests/                   # Tests
├── app.py                   # Flask application
├── seed_graph.py             # Graph data initialization
├── investigate.py            # Investigation logic
├── investigation.py          # Investigation functionality
├── investigation_report.py   # Investigation reporting
├── ai_investigator.py        # Gemini-assisted investigation
├── trace_evidence.py         # Evidence tracing
├── graph_explorer.py         # Graph exploration
├── check_cross_centre.py     # Cross-centre checks
├── add_evidence.py           # Evidence utilities
├── rename_location.py        # Location utilities
└── requirements.txt          # Python dependencies
```

Graph Queries

AidTrace uses Cypher queries to investigate connected relief-distribution records, trace evidence, identify potential discrepancies, and support resource matching through FalkorDB.

For details about the graph data model, Cypher queries, and investigation logic, see [Cypher Queries and Graph Algorithms](docs/CYPHER_QUERIES.md).

## AI Disclosure

AI tools, including Google Gemini and ChatGPT, were used to assist with development, debugging, and documentation. AI-assisted contributions were reviewed by the project author.

## Track

**FalkorDB Graph Hacks — Track 01: Agents That Act on Connected Data**

AidTrace applies graph-based investigation to disaster-relief distribution, using connected evidence to identify potential discrepancies and support explainable investigation workflows.
