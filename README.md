# AidTrace — Graph-Powered Relief Investigation

AidTrace is a graph-powered relief investigation prototype built with **FalkorDB**, **Python/Flask**, and **Google Gemini**. It helps investigators explore connected relief-operation data, identify potential discrepancies, examine resource availability, and understand findings through AI-assisted explanations.

The project demonstrates how graph relationships can support investigations involving relief requests, deliveries, receipts, routes, incidents, warehouses, and supplies.

> **Project status:** Hackathon prototype. Findings are investigative leads that require verification; discrepancies alone do not prove fraud, theft, or misconduct.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Graph Data Model](#graph-data-model)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Configure Environment Variables](#configure-environment-variables)
- [Initialize the Graph Database](#initialize-the-graph-database)
- [Run AidTrace](#run-aidtrace)
- [Using the Application](#using-the-application)
- [Cypher Queries and Graph Algorithms](#cypher-queries-and-graph-algorithms)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Demo Video](#demo-video)
- [Hackathon Track](#hackathon-track)
- [AI-Assisted Development Disclosure](#ai-assisted-development-disclosure)
- [Limitations](#limitations)

## Features

- **Graph-based investigation:** Examine connected relief requests, deliveries, receipts, routes, and related records.
- **Delivery discrepancy analysis:** Compare reported delivery quantities with receipt-confirmed quantities where supporting records are available.
- **Cross-centre findings:** Explore potential relationships and discrepancies across relief centres.
- **Resource matching:** Identify supply records that may be relevant to outstanding relief needs.
- **Route updates:** Record operational route-status changes through the application.
- **AI-assisted investigation:** Use Google Gemini to help explain investigation findings.
- **Graph evidence explorer:** Inspect graph nodes, properties, and relationships.
- **Node editing:** Update supported node properties with a reason for the change.
- **Multiple scenarios:** Explore the Wayanad and Assam River Flooding demonstration datasets.

The exact findings depend on the records loaded into FalkorDB and the queries used by the application.

## Technology Stack

| Technology            | Purpose                                               |
| --------------------- | ----------------------------------------------------- |
| Python                | Backend implementation and investigation logic        |
| Flask                 | Web application and API endpoints                     |
| FalkorDB              | Graph database for connected relief-operation records |
| Cypher                | Graph querying and relationship traversal             |
| Google Gemini         | AI-assisted investigation explanations                |
| HTML, CSS, JavaScript | Web interface and client-side interactions            |
| python-dotenv         | Loading local environment configuration               |

Python dependencies are listed in [`requirements.txt`](requirements.txt).

## Architecture

```text
User
 |
 v
AidTrace Web Interface
(HTML, CSS, JavaScript)
 |
 v
Flask Application
(app.py)
 |
 +------------------------+
 |                        |
 v                        v
FalkorDB              Gemini API
Graph Database        AI Explanations
 |
 v
Connected Relief Data
Requests, Deliveries, Receipts,
Routes, Incidents, Warehouses,
and Supplies
 |
 v
Investigation Results
and Graph Evidence
```

FalkorDB is responsible for storing and querying connected graph data. Flask coordinates requests and processes results. Gemini is used for AI-assisted analysis; the graph data and investigation logic provide the operational evidence.

## Graph Data Model

AidTrace models relief operations as a graph. Nodes represent entities or records, and directed relationships represent connections between them.

### Node labels

The current query modules reference the following labels:

| Node label       | Purpose                                                     |
| ---------------- | ----------------------------------------------------------- |
| `Community`      | A community or destination associated with a relief request |
| `ReliefRequest`  | A request for a relief item and quantity                    |
| `Delivery`       | A delivery record                                           |
| `Receipt`        | A receipt or confirmation record                            |
| `Route`          | A route associated with a delivery                          |
| `IncidentReport` | A report associated with a potentially affected route       |
| `Warehouse`      | A warehouse holding supplies                                |
| `Supply`         | A supply item and its recorded quantity                     |

### Relationships

| Relationship      | Meaning                                  |
| ----------------- | ---------------------------------------- |
| `HAS_REQUEST`     | Connects a community to a relief request |
| `FULFILLED_BY`    | Connects a request to a delivery         |
| `HAS_RECEIPT`     | Connects a delivery to a receipt         |
| `TRANSPORTED_VIA` | Connects a delivery to a route           |
| `AFFECTS`         | Connects an incident report to a route   |
| `STORES`          | Connects a warehouse to a supply record  |

### Important properties

Depending on the node type, records can include properties such as:

- `id` — record identifier
- `name` — human-readable name
- `item` — relief item
- `quantity` — requested or recorded quantity
- `reported_quantity` — quantity reported as delivered
- `confirmed_quantity` — quantity confirmed by a receipt
- `status` — recorded status
- `description` — incident or record description
- `scenario_id` — scenario identifier used to separate demonstration data

Property availability varies by node type. Refer to the actual seed data and query implementation for the definitive schema.

## Prerequisites

Install the following before running the application:

1. **Python 3.10 or later**, subject to the compatibility of the pinned or installed dependencies.
2. **Git**, to clone the repository.
3. **FalkorDB**, running locally or at a reachable database endpoint.
4. **A Google Gemini API key**, for the AI investigation feature.

FalkorDB must be available before you run database-dependent investigation or graph operations.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/YADHUKISHANTR/AidTrace.git
cd AidTrace
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If dependency installation fails, confirm that the Python version is compatible with the packages listed in `requirements.txt`.

### 4. Start FalkorDB

Start a FalkorDB instance using your chosen installation method. For a local setup, ensure the service is reachable at the host and port configured in the application.

The current graph connection code uses the graph name `aidtrace` and a local connection at `localhost:6379`.

If you use Docker, confirm the current FalkorDB image and startup instructions from the official documentation before running the container.

- FalkorDB documentation: https://docs.falkordb.com/
- FalkorDB repository: https://github.com/FalkorDB/FalkorDB

If your database uses different host, port, or authentication settings, update the application configuration accordingly.

## Configure Environment Variables

Create a `.env` file in the project root for local secrets and configuration.

Example:

```dotenv
GEMINI_API_KEY=your_gemini_api_key_here
```

Replace the placeholder with your own Gemini API key.

**Security requirements:**

- Never commit a real API key to GitHub.
- Keep `.env` in `.gitignore`.
- Do not paste API keys into screenshots, public issues, or the demo video.
- Do not put secrets in source code or the README.

If the application requires additional configuration, follow the environment-variable names used in the current source code.

## Initialize the Graph Database

AidTrace includes a graph seed script named `seed_graph.py`.

After FalkorDB is running and your Python environment is active, inspect the script to confirm its supported options and run the appropriate initialization command.

```bash
python seed_graph.py
```

**Important:** Confirm whether the script seeds both scenarios, whether it clears existing graph data, and whether it supports running repeatedly before executing it against any database containing data you need to preserve.

The demonstration scenarios are:

- **Wayanad** — relief-operation demonstration scenario in Kerala.
- **Assam River Flooding** — a separate relief-operation demonstration scenario.

If the seed script has separate commands for each scenario, document those exact commands here after verifying them in the source code.

## Run AidTrace

With the virtual environment active, dependencies installed, environment configured, and FalkorDB running, start Flask:

```bash
python app.py
```

Open the local URL printed in the terminal. If the development server uses the standard Flask default, this is usually:

http://127.0.0.1:5000/

If the application reports a connection error, check that FalkorDB is running, the configured host and port are correct, and the expected graph has been initialized.

The Flask development server is intended for local demonstration and development, not production deployment.

## Using the Application

1. Open AidTrace in your browser.
2. Select the Wayanad or Assam scenario.
3. Run the investigation.
4. Review the findings, resource-matching results, and recommended actions.
5. Update a route's status if the scenario and interface provide an appropriate update control.
6. Run the AI investigation to inspect the explanation generated for the selected case.
7. Open the graph visualization to examine nodes and their relationships.
8. Inspect or update supported node properties when appropriate, providing a truthful reason for any change.

After changing graph data, rerun the relevant investigation to check whether the displayed results reflect the updated records.

## Cypher Queries and Graph Algorithms

The primary query documentation is maintained separately:

**[Cypher Queries and Graph Algorithms](docs/CYPHER_QUERIES.md)**

That document describes the graph traversal patterns, quantity comparisons, evidence retrieval, scenario filtering, and graph explorer queries.

The principal implementation files include:

- `investigate.py`
- `trace_evidence.py`
- `graph_explorer.py`
- `investigation.py`
- `app.py`

The queries in the source code are the source of truth. Keep the documentation synchronized with the implementation.

## Project Structure

```text
AidTrace/
├── app.py
├── ai_investigator.py
├── add_evidence.py
├── check_cross_centre.py
├── graph_explorer.py
├── investigate.py
├── investigation.py
├── investigation_report.py
├── rename_location.py
├── seed_graph.py
├── trace_evidence.py
├── requirements.txt
├── README.md
├── docs/
│   └── CYPHER_QUERIES.md
├── static/
├── templates/
└── tests/
```

This is a high-level view. The repository may contain additional configuration and supporting files.

## Testing

The repository includes a `tests/` directory.

Inspect the available tests and run the appropriate test command for the current test framework. If the project uses pytest, run:

```bash
python -m pytest
```

Before submitting, test both scenarios and verify:

- Investigation results load successfully.
- Wayanad data does not leak into Assam results, or vice versa.
- Quantity calculations agree with the underlying records.
- Missing delivery or receipt evidence is handled appropriately.
- Resource matching does not double-count stock.
- Route updates persist as expected.
- Node edits are validated and audited.
- AI explanations agree with the structured investigation evidence.

Do not describe a test as passing unless you have actually run it.

## Demo Video

**Demo video:** [Add your published demo video URL here]

The walkthrough should demonstrate the working website, the investigation workflow, a route update, AI-assisted analysis, and inspection of the underlying graph evidence.

Replace the placeholder above with the final public video link before submission.

## Hackathon Track

**Event:** FalkorDB Graph Hacks — WeMakeDevs

**Track:** Track 01 — Agents That Act on Connected Data

AidTrace explores how graph queries can support investigation by traversing connected relief-operation records, retrieving relevant evidence, and helping users understand potential discrepancies and resource gaps.

Official event page: https://www.wemakedevs.org/hackathons/falkordb

## AI-Assisted Development Disclosure

AI coding assistants were used during development for assistance with code review, debugging, documentation, and implementation guidance. The project author is responsible for reviewing, testing, and understanding the submitted code.

Before submission, update this section to identify the actual tools used and accurately describe the assistance they provided. Do not claim that all code was written independently if AI-generated code was incorporated into the project.

## Limitations

AidTrace is a hackathon prototype and its findings depend on the quality, completeness, and consistency of the underlying records.

- A discrepancy indicates a difference between records; it does not establish wrongdoing.
- Missing relationships can prevent some records from appearing in a query result.
- Resource matching requires careful validation of available stock, allocations, and delivery feasibility.
- AI explanations may be incomplete or incorrect and should be checked against graph evidence.
- Scenario isolation, aggregation, and persistence must be tested before the results are used for operational decisions.

## License

Add the license and attribution information applicable to this repository and its data before public release.
