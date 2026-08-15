# AI Support & TAM Assistant

A production-minded AI assistant for **Technical Support** and
**Technical Account Management (TAM)** workflows.

The system uses the supplied synthetic support dataset and product
knowledge base to provide:

-   Intelligent support-ticket triage
-   Knowledge-base retrieval and grounding
-   Deterministic customer account-health analysis
-   TAM executive summaries
-   Churn/escalation signal detection
-   Data-quality warnings
-   Automated evaluation and regression testing
-   Streamlit thin UI
-   Streaming triage responses
-   GitHub Actions CI
-   Versioned prompt documentation

> **Assignment:** US Delivery Internship --- Technical Interview Task
> Round\
> **Focus:** Production-grade AI for Technical Support & TAM Teams

------------------------------------------------------------------------

## 1. Solution Overview

The solution contains two primary business workflows.

### Task 1 --- Intelligent Ticket Triage

A raw support ticket is processed to produce:

-   Product
-   Product area
-   Issue category
-   Urgency tier (P1--P4)
-   Concise reasoning
-   Known-issue status
-   Grounded knowledge-base document
-   Recommended responder team
-   Draft first-response message

The pipeline combines **TF-IDF retrieval + supplied Markdown
knowledge-base evidence + Groq LLM structured generation + Pydantic
validation and grounding checks**.

### Task 2 --- TAM Account Health Summarizer

Given an account ID, the system combines:

-   Supplied account summary
-   Relevant support-ticket history
-   Last-90-day ticket metrics
-   Priority counts
-   Open-ticket information
-   Seat utilization
-   Usage trend
-   Renewal timing
-   NPS
-   Escalation notes
-   Recurring ticket themes

It produces a deterministic account-health result and an
executive-facing TAM summary containing:

1.  Executive summary
2.  Open risks and flagged issues
3.  Recommended TAM talking points/actions

The **health score and health status are calculated deterministically**
by the Account Health Service. The LLM is used for synthesis/explanation
and cannot override the authoritative score or status.

------------------------------------------------------------------------

## 2. Architecture

### Ticket Triage

``` text
Support Ticket
     |
     v
Query Construction
     |
     v
TF-IDF Retriever
     |
     v
Top-K Knowledge-Base Evidence
     |
     +--------------------+
     |                    |
     v                    v
Knowledge Base       Ticket Context
     |                    |
     +---------+----------+
               |
               v
           Groq LLM
               |
               v
      Structured JSON Output
               |
               v
     Pydantic Validation
               |
               v
      Grounding / Validation
               |
               v
        Triage Response
```

### Account Health + TAM

``` text
Customer Account + Ticket History
               |
               v
     Account Health Service
               |
               v
   Deterministic Health Score
               |
               v
 Health Status + Metrics + Risks
               |
               v
           TAM Agent
               |
               v
    Executive TAM Summary
```

### Design principle

Business-critical account-health calculations remain deterministic. The
LLM is not trusted to independently calculate or override those values.

------------------------------------------------------------------------

## 3. Technology Stack

-   Python 3.11
-   FastAPI
-   Pydantic
-   Groq API
-   LLM structured generation
-   TF-IDF retrieval / RAG
-   Pytest
-   Streamlit
-   JSON synthetic datasets
-   Markdown knowledge base
-   GitHub Actions

------------------------------------------------------------------------

## 4. Data and Grounding

The implementation uses **only the supplied synthetic assignment data
and knowledge base**.

The starter repository provides:

-   500 synthetic support tickets
-   50 synthetic customer account summaries
-   Markdown knowledge-base documents

The knowledge base contains product, troubleshooting, billing, and
onboarding information.

No live customer data, web scraping, or external business dataset is
used.

For triage, retrieved KB evidence is supplied to the LLM. The prompt
explicitly requires grounded results and prevents unsupported KB claims.

------------------------------------------------------------------------

## 5. Repository Structure

``` text
.
├── app/
│   ├── agents/
│   │   ├── factory.py
│   │   ├── tam_agent.py
│   │   ├── tam_demo.py
│   │   ├── triage_agent.py
│   │   └── triage_demo.py
│   ├── api/
│   │   └── main.py
│   ├── models/
│   │   ├── account_health.py
│   │   ├── tam_summary.py
│   │   └── triage.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── README.md
│   │   └── triage_v1.py
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── context.py
│   │   └── retriever.py
│   └── services/
│       ├── account_health.py
│       ├── account_health_demo.py
│       ├── data_loader.py
│       └── llm_client.py
├── data/
│   ├── accounts.json
│   └── tickets.json
├── knowledge-base/
├── evaluation/
│   ├── cases.json
│   ├── eval_report.json
│   └── run_evaluation.py
├── tests/
├── ui/
│   └── streamlit_app.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
├── DESIGN_NOTE.md
├── README.md
├── requirements.txt
├── .env.example
└── run.py
```

------------------------------------------------------------------------

## 6. Setup

### Requirements

-   Python 3.11
-   Groq API key for LLM-backed workflows

### Create a virtual environment

#### Windows PowerShell

``` powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux / macOS

``` bash
python -m venv .venv
source .venv/bin/activate
```

### Install dependencies

``` bash
pip install -r requirements.txt
```

### Configure environment variables

Create a local `.env` file based on `.env.example`:

``` env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

**Never commit `.env` or a real API key.**

### Run the application

``` bash
python run.py
```

The FastAPI service is available at:

``` text
http://127.0.0.1:8000
```

Swagger documentation:

``` text
http://127.0.0.1:8000/docs
```

Health check:

``` text
GET /health
```

------------------------------------------------------------------------

## 7. Task 1 --- Intelligent Ticket Triage

### API

``` text
POST /triage
```

Example request:

``` json
{
  "subject": "DataBridge Pro connection timeout",
  "body": "Our DataBridge Pro pipeline has been failing with ERR_CONNECTION_TIMEOUT after 30 seconds. We are unable to complete the data transfer."
}
```

The response is structured JSON.

Example:

``` json
{
  "product": "DataBridge Pro",
  "product_area": "Data Ingestion",
  "category": "Bug",
  "urgency": "P2",
  "reasoning": "The customer is experiencing a connection timeout while attempting a data transfer.",
  "known_issue": true,
  "kb_document": "troubleshooting\\performance-and-integrations.md",
  "recommended_responder_team": "Technical Support",
  "first_response": "Thank you for reaching out..."
}
```

### Demo

``` bash
python -m app.agents.triage_demo
```

### Streaming

A streaming endpoint is also available:

``` text
POST /triage/stream
```

The streaming implementation reuses the same retrieval and prompt
strategy while returning the LLM response incrementally.

------------------------------------------------------------------------

## 8. Task 2 --- TAM Account Health

### API

``` text
POST /accounts/{account_id}/health
```

Example:

``` text
ACC-3336
```

The account-health workflow calculates deterministic metrics including:

-   Health score
-   Health status
-   90-day ticket count
-   Open ticket count
-   Recent ticket count
-   P1/P2 counts
-   Seat utilization
-   Usage trend
-   Days to renewal
-   NPS
-   Escalation signals
-   Recurring themes
-   Recommended actions
-   Data-quality warnings

### Demo

``` bash
python -m app.services.account_health_demo
```

------------------------------------------------------------------------

## 9. TAM Executive Summary

### API

``` text
POST /accounts/{account_id}/tam-summary
```

Example:

``` text
ACC-3336
```

The TAM workflow converts the deterministic account-health result into
an executive-facing brief containing:

-   Executive summary
-   Open risks
-   Talking points
-   Top risks
-   Recommended actions
-   Renewal risk
-   Customer sentiment
-   Data-quality warnings

### Demo

``` bash
python -m app.agents.tam_demo
```

The LLM performs synthesis and explanation. It does not recalculate or
override the deterministic health score/status.

------------------------------------------------------------------------

## 10. Evaluation Harness

The evaluation harness covers both major workflows.

### Run evaluation

``` bash
python -m evaluation.run_evaluation
```

The harness includes:

-   5 normal triage cases
-   1 adversarial triage case
-   5 normal account-health cases
-   1 adversarial account-health case
-   Per-case pass/fail scoring
-   Per-case quality score from 0--1
-   Aggregate pass rate
-   Aggregate quality score
-   JSON report

### Final evaluation result

``` text
Triage:                    5/5 passed
Triage adversarial:       1/1 passed
Account Health:            5/5 passed
Account Health adversarial:1/1 passed

Total:                    12/12
Pass rate:                100.0%
Overall quality score:   1.00
STATUS:                   PASS
```

The generated report is stored at:

``` text
evaluation/eval_report.json
```

------------------------------------------------------------------------

## 11. Automated Tests

Run the complete regression suite:

``` bash
pytest -q
```

Current result:

``` text
18 passed
```

The tests cover areas including:

-   Triage validation
-   LLM connectivity
-   RAG retrieval
-   Knowledge-base grounding
-   Product grounding
-   Account-health calculations
-   Data-quality handling
-   TAM functionality

------------------------------------------------------------------------

## 12. Thin UI

A Streamlit UI is provided for non-technical users.

Run:

``` bash
streamlit run ui/streamlit_app.py
```

The UI provides:

-   Ticket Triage
-   Account Health
-   TAM Summary

The UI communicates with the FastAPI backend and does not duplicate the
core business logic.

This implements the **Thin UI bonus**.

------------------------------------------------------------------------

## 13. Streaming

Streaming is implemented for ticket triage through:

``` text
POST /triage/stream
```

The implementation uses the LLM streaming interface while preserving the
same retrieval, prompt, grounding, and validation architecture.

This implements the **Streaming bonus**.

------------------------------------------------------------------------

## 14. Prompt Versioning

The triage prompt is maintained separately from the agent
implementation:

``` text
app/prompts/triage_v1.py
```

Current prompt version:

``` text
1.0.0
```

Prompt documentation and version history:

``` text
app/prompts/README.md
```

The prompt includes explicit rules for:

-   Structured JSON output
-   Category selection
-   Urgency classification
-   KB grounding
-   Known-issue detection
-   Responder-team recommendation
-   Customer-facing response generation
-   Preventing fabricated information

Prompt changes are intended to be versioned and evaluated before
promotion.

This implements the **Prompt Versioning bonus**.

------------------------------------------------------------------------

## 15. Continuous Integration

GitHub Actions runs automatically on pushes and pull requests.

Workflow:

``` text
.github/workflows/ci.yml
```

CI performs:

1.  Repository checkout
2.  Python 3.11 setup
3.  Dependency installation
4.  Pytest regression suite
5.  Evaluation harness

The Groq API key is supplied through GitHub Actions Secrets and is never
stored in source code.

This implements the **Automated CI bonus**.

------------------------------------------------------------------------

## 16. Data Quality Handling

The account-health service detects inconsistencies between structured
account fields and escalation notes.

For example, escalation notes may indicate P1 activity while the
structured P1 count is zero.

Such inconsistencies are surfaced as deterministic data-quality
warnings.

The warnings are preserved through the account-health result and
surfaced in the TAM summary rather than silently allowing the LLM to
hide them.

------------------------------------------------------------------------

## 17. Security

Security principles:

-   API keys are loaded through environment variables.
-   `.env` is excluded from version control.
-   `.env.example` contains placeholders only.
-   No real API credentials are committed.
-   Only the supplied synthetic assignment data is used.
-   No live customer data is required.
-   Production deployments should redact or minimize sensitive data
    before external LLM calls.
-   Deterministic business-critical fields are protected from LLM
    modification.

------------------------------------------------------------------------

## 18. Design Note

The required production design discussion is documented in:

``` text
DESIGN_NOTE.md
```

It covers:

### Failure modes

Top production failure scenarios and detection/mitigation strategies.

### Latency vs quality

The trade-off between retrieval quality, LLM generation quality, and
response latency, including what would change under a hard latency
constraint.

### Data sensitivity

Handling of potentially sensitive ticket/account information and
controls for external LLM APIs.

### Scaling

Expected bottlenecks and architecture considerations for approximately
10× the current ticket volume.

------------------------------------------------------------------------

## 19. Production Considerations

For a production deployment, the architecture could be extended with:

-   Embedding-based retrieval/vector database
-   Retrieval-quality monitoring
-   Authentication and authorization
-   Rate limiting
-   Request tracing
-   Structured logging
-   PII detection/redaction
-   LLM timeout/retry policies
-   Model fallback
-   Response caching where appropriate
-   Prompt/version registry
-   Automated evaluation gates in CI/CD
-   Retrieval and generation observability

The current implementation intentionally stays within the assignment's
supplied data and time constraints.

------------------------------------------------------------------------

## 20. Final Validation

### Regression tests

``` bash
pytest -q
```

Expected:

``` text
18 passed
```

### Evaluation

``` bash
python -m evaluation.run_evaluation
```

Expected:

``` text
Passed: 12/12
Pass rate: 100.0%
Overall quality score: 1.00
STATUS: PASS
```

### Formatting check

``` bash
git diff --check
```

Expected: no output.

### Clean-install verification

The project has been verified from a fresh Python virtual environment
using:

``` bash
pip install -r requirements.txt
python run.py
```

The FastAPI service starts successfully and responds with HTTP 200 for:

``` text
GET /health
GET /
```

------------------------------------------------------------------------

## 21. Submission Checklist

Before submission, verify:

-   [x] Source code
-   [x] Supplied synthetic datasets
-   [x] Supplied knowledge base
-   [x] Test suite
-   [x] Evaluation harness
-   [x] `evaluation/eval_report.json`
-   [x] `DESIGN_NOTE.md`
-   [x] `.env.example`
-   [x] Top-level README
-   [x] Streamlit thin UI
-   [x] Streaming triage
-   [x] GitHub Actions CI
-   [x] Prompt versioning and changelog
-   [x] Clean Git working tree
-   [ ] 3--6 minute Loom walkthrough

The Loom should demonstrate:

1.  Architecture/code
2.  Live Task 1 triage
3.  Live Task 2 account health/TAM summary
4.  Evaluation results
5.  Bonus features where time permits

------------------------------------------------------------------------

## 22. Recommended Demo Flow

### 1. Architecture

Explain:

``` text
Ticket
  ↓
TF-IDF RAG
  ↓
Knowledge Base
  ↓
Groq LLM
  ↓
Structured Output
  ↓
Grounding / Validation
  ↓
Triage Result
```

and:

``` text
Account + Tickets
  ↓
Deterministic Account Health
  ↓
Health Score + Status
  ↓
TAM Agent
  ↓
Executive Summary
```

### 2. Task 1

Run:

``` bash
python -m app.agents.triage_demo
```

Show the structured result and KB grounding.

### 3. Task 2

Run:

``` bash
python -m app.services.account_health_demo
```

Show health metrics, risk signals, renewal information, and data-quality
handling.

Then:

``` bash
python -m app.agents.tam_demo
```

Show the executive summary.

### 4. Automated validation

Run:

``` bash
pytest -q
python -m evaluation.run_evaluation
```

Show:

``` text
18 passed
12/12 evaluation cases passed
100% evaluation score
```

### 5. Bonus features

Briefly demonstrate:

-   Streamlit UI
-   Streaming triage endpoint
-   GitHub Actions CI
-   Prompt versioning

------------------------------------------------------------------------

## 23. Final Status

The implementation demonstrates:

-   RAG-based ticket triage
-   Knowledge-base grounding
-   Structured LLM output
-   Deterministic account-health scoring
-   Risk and escalation detection
-   Data-quality handling
-   TAM executive summarization
-   Regression testing
-   Automated evaluation
-   Adversarial evaluation
-   Thin UI
-   Streaming
-   CI automation
-   Prompt versioning

### Validation

``` text
Pytest:                  18/18 PASS
Evaluation:              12/12 PASS
Adversarial Evaluation:   2/2 PASS
Evaluation Score:       100%
Overall Quality Score:    1.00
```

The repository is intended to provide a clear, reproducible
demonstration of an AI-assisted support/TAM workflow while keeping
deterministic business logic authoritative and using only the supplied
synthetic assignment data.
