# AI Support & TAM Assistant

A production-minded AI system designed to support Technical Support and Technical Account Management (TAM) workflows.

The system provides:

1. Intelligent support ticket triage
2. Knowledge-base retrieval and grounding
3. Deterministic customer account-health scoring
4. TAM executive summaries
5. Data-quality warnings
6. Automated evaluation and regression testing
7. Production design considerations

---

# 1. Project Overview

The AI Support & TAM Assistant combines deterministic business logic, Retrieval-Augmented Generation (RAG), and Large Language Model (LLM) capabilities.

The project contains three primary workflows.

## Task 1 — Ticket Triage

A support ticket is analyzed to determine:

- Product
- Product area
- Issue category
- Urgency
- Reasoning
- Known issue
- Relevant knowledge-base document
- Recommended responder team
- First-response message

## Task 2 — Account Health

Customer account information and support-ticket information are processed to determine:

- Health score
- Health status
- 90-day ticket count
- Open ticket count
- Priority counts
- Recent ticket count
- Seat utilization
- Usage trend
- Days to renewal
- NPS
- Escalation notes
- Recurring themes
- Recommended actions
- Data-quality warnings

## Task 3 — TAM Executive Summary

The TAM agent converts the deterministic account-health information into an executive-facing summary containing:

- Executive summary
- Open risks
- Talking points
- Top risks
- Recommended actions
- Renewal risk
- Customer sentiment
- Data-quality warnings

---

# 2. Architecture

```text
                         ┌──────────────────────┐
                         │    Support Ticket    │
                         │  Subject + Body      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │     Triage Agent     │
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
          ┌───────────────────┐           ┌───────────────────┐
          │   TF-IDF RAG      │           │     Groq LLM      │
          │    Retriever      │           │                   │
          └─────────┬─────────┘           └─────────┬─────────┘
                    │                               │
                    ▼                               │
          ┌───────────────────┐                     │
          │  Knowledge Base   │─────────────────────┘
          │  Markdown Docs    │
          └───────────────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Structured Triage    │
                         │ Result + Grounding   │
                         └──────────────────────┘


                         ┌──────────────────────┐
                         │   Customer Account   │
                         │ + Ticket History     │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Account Health       │
                         │ Service              │
                         │                      │
                         │ Deterministic Rules  │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │      TAM Agent       │
                         │       + LLM          │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ TAM Executive        │
                         │ Summary              │
                         └──────────────────────┘



3. High-Level Flow
Ticket Triage Flow
Support Ticket
      │
      ▼
Query Construction
      │
      ▼
TF-IDF Retriever
      │
      ▼
Top-K Knowledge Base Chunks
      │
      ├───────────────┐
      │               │
      ▼               ▼
Knowledge Base      Ticket Context
      │               │
      └───────┬───────┘
              ▼
          Groq LLM
              │
              ▼
     Structured Triage Result
              │
              ▼
     Grounding / Validation
              │
              ▼
      Final Triage Response

The RAG pipeline retrieves relevant knowledge-base content before the LLM generates the final structured response.

Structured error identifiers such as:

ERR_CONNECTION_TIMEOUT
PIPELINE_STALLED
CHECKSUM_MISMATCH

are used to improve knowledge-base grounding.

4. Account Health Flow
Customer Account
      │
      ├──────────────────┐
      │                  │
      ▼                  ▼
Account Data          Ticket Data
      │                  │
      └─────────┬────────┘
                ▼
      Account Health Service
                │
                ▼
      Deterministic Health Score
                │
                ▼
       Health Status + Metrics
                │
                ▼
       Data Quality Validation
                │
                ▼
            TAM Agent
                │
                ▼
       Executive Summary

The health score and health status are calculated deterministically by the account-health service.

The LLM does not recalculate or override the deterministic health score or health status.

5. Technology Stack
Python 3.11
Pydantic
Groq API
LLM-based structured generation
TF-IDF retrieval
Pytest
JSON datasets
Markdown knowledge base
Streamlit thin UI
FastAPI REST API



6. Dataset

The project uses the supplied synthetic assignment data.

data/
├── tickets.json
└── accounts.json

Knowledge-base documents are stored under:

knowledge-base/
├── products/
├── troubleshooting/
├── billing/
└── onboarding/

The project uses only the supplied mock data and knowledge base.

No live customer data is required.

7. Setup
7.1 Create Virtual Environment
python -m venv .venv
7.2 Activate Virtual Environment
Windows PowerShell
.venv\Scripts\Activate.ps1
Linux / macOS
source .venv/bin/activate
7.3 Install Dependencies
pip install -r requirements.txt
7.4 Configure Environment Variables
7.5 Run the FastAPI Backend

uvicorn app.api.main:app --reload

The API is available at:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

7.6 Run the Streamlit UI

streamlit run ui/streamlit_app.py

The Streamlit UI provides three workflows:

- Ticket Triage
- Account Health
- TAM Summary

The UI communicates with the FastAPI backend and does not duplicate the core business logic.



Create a .env file based on .env.example.

Example:

GROQ_API_KEY=your_groq_api_key

The real API key must never be committed to the repository.

8. Task 1 — Intelligent Ticket Triage

The triage agent analyzes a support ticket using RAG and an LLM.

Run
python -m app.agents.triage_demo

Example ticket:

Subject:
DataBridge Pro connection timeout


Body:
Our DataBridge Pro pipeline has been failing with
ERR_CONNECTION_TIMEOUT after 30 seconds.
We are unable to complete the data transfer.

Example output:

{
  "product": "DataBridge Pro",
  "product_area": "Data Ingestion",
  "category": "Bug",
  "urgency": "P2",
  "reasoning": "The customer is experiencing a connection timeout error after 30 seconds...",
  "known_issue": true,
  "kb_document": "troubleshooting\\performance-and-integrations.md",
  "recommended_responder_team": "Technical Support",
  "first_response": "Thank you for reaching out..."
}

The result is validated using the Pydantic model and grounded against retrieved knowledge-base content.

9. Task 2 — TAM Account Health

The account-health service combines account information and ticket history to calculate a deterministic health result.

Run
python -m app.services.account_health_demo

Example:

ACC-3336 | Omni Consumer Products | Critical | Score: 2.00

The account-health result includes:

Health score
Health status
Ticket counts
Priority counts
Seat utilization
Usage trend
Renewal timing
NPS
Escalation notes
Recurring themes
Recommended actions
Data-quality warnings
10. Task 3 — TAM Executive Summary

The TAM agent uses the deterministic account-health result and account context to produce an executive-facing summary.

Run
python -m app.agents.tam_demo

The output includes:

Executive summary
Open risks
Talking points
Top risks
Recommended actions
Renewal risk
Customer sentiment
Data-quality warnings

The LLM is used for synthesis and explanation.

The deterministic account-health score and status remain authoritative.

11. Evaluation

The project contains an evaluation harness covering both ticket triage and account health.

Run:

python -m evaluation.run_evaluation

Current evaluation result:

======================================================================
TRIAGE EVALUATION
======================================================================
PASS: TRIAGE-001
PASS: TRIAGE-002
PASS: TRIAGE-003
PASS: TRIAGE-004
PASS: TRIAGE-005

Triage result: 5/5 passed
Triage quality score: 1.00

======================================================================
TRIAGE ADVERSARIAL EVALUATION
======================================================================
PASS: TRIAGE-ADV-001

======================================================================
ACCOUNT HEALTH EVALUATION
======================================================================
PASS: ACC-3336
PASS: ACC-2944
PASS: ACC-6254
PASS: ACC-7397
PASS: ACC-7463

Account Health result: 5/5 passed
Account Health quality score: 1.00

======================================================================
ACCOUNT HEALTH ADVERSARIAL EVALUATION
======================================================================
PASS: ACC-ADV-001

======================================================================
OVERALL EVALUATION
======================================================================
Passed: 12/12
Pass rate: 100.0%
Overall quality score: 1.00
STATUS: PASS

12. Automated Tests

Run the complete test suite:

pytest -q

Current result:

18 passed

The test suite covers:

Triage validation
LLM connectivity
RAG retrieval
Knowledge-base grounding
Product grounding
Account-health calculations
Data-quality handling
TAM functionality
13. Evaluation Criteria

The evaluation harness checks deterministic and structured aspects of the system.

Triage

The evaluation validates:

Product
Category
Expected triage behavior
Structured output validity
Knowledge-base grounding
Account Health

The evaluation validates:

Account ID
Health score bounds
Health status
Ticket counts
Priority counts
Recent ticket counts
Seat utilization
Data-quality warnings

Current validation:

Triage:          5/5
Account Health:  5/5
Overall:        10/10
Score:          100%
14. Data Quality Handling

The system detects inconsistencies between structured account fields and escalation notes.

For example:

Account escalation notes mention P1 tickets
but p1_tickets_last_30d is 0.

The warning is preserved through the account-health result and surfaced again by the TAM agent.

Data-quality warnings are deterministic and cannot be silently removed by the LLM.

15. Project Structure
.
├── app/
│   ├── agents/
│   │   ├── factory.py
│   │   ├── tam_agent.py
│   │   ├── tam_demo.py
│   │   ├── triage_agent.py
│   │   └── triage_demo.py
│   │
│   ├── models/
│   │   ├── account_health.py
│   │   ├── tam_summary.py
│   │   └── triage.py
│   │
│   ├── prompts/
│   │   └── triage_v1.py
│   │
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── context.py
│   │   └── retriever.py
│   │
│   └── services/
│       ├── account_health.py
│       ├── account_health_demo.py
│       ├── data_loader.py
│       └── llm_client.py
│
├── data/
│   ├── accounts.json
│   └── tickets.json
│
├── knowledge-base/
│   ├── products/
│   ├── troubleshooting/
│   ├── billing/
│   └── onboarding/
│
├── evaluation/
│   ├── cases.json
│   └── run_evaluation.py
│
├── tests/
│
├── DESIGN_NOTE.md
├── README.md
├── requirements.txt
└── .env.example
├── ui/
│   └── streamlit_app.py
16. Security

The project follows these security principles:

API keys are loaded through environment variables.
Secrets must never be committed to Git.
.env should be excluded from version control.
Only supplied synthetic data is used.
No live production customer data is required.
Sensitive production data should be redacted before being sent to an external LLM API.
Deterministic business-critical fields are protected from LLM modification.
17. Production Considerations

The production design considerations are documented separately in:

DESIGN_NOTE.md

The design note covers:

Failure modes
Latency vs quality trade-offs
Data sensitivity and PII
Scaling considerations
18. Current Validation Status
Automated Tests:       18/18 PASS
Evaluation Cases:      10/10 PASS
Evaluation Score:      100%

The implementation has been validated through both the automated regression test suite and the assignment evaluation harness.

19. Running the Complete Validation

For a complete local validation, run:

pytest -q

Then:

python -m evaluation.run_evaluation

Then optionally run each demonstration:

python -m app.agents.triage_demo
python -m app.services.account_health_demo
python -m app.agents.tam_demo
20. Submission Checklist

Before submission, verify that the repository contains:

 Source code
 Supplied datasets
 Knowledge base
 Test suite
 Evaluation harness
 README
 DESIGN_NOTE.md
 .env.example
 Evaluation report
 Git repository
 Loom walkthrough
21. Demo Flow

For a project walkthrough, demonstrate the following sequence.

1. Project Architecture

Explain the two major workflows:

Ticket
  ↓
TF-IDF RAG
  ↓
Knowledge Base
  ↓
Groq LLM
  ↓
Grounding / Validation
  ↓
Triage Result

And:

Account + Tickets
  ↓
Deterministic Account Health Service
  ↓
Health Score + Status
  ↓
TAM Agent
  ↓
Executive Summary
2. Task 1

Run:

python -m app.agents.triage_demo

Show the structured triage result and knowledge-base grounding.

3. Task 2

Run:

python -m app.services.account_health_demo

Show the account-health score, status, renewal information, and data-quality handling.

4. Task 3

Run:

python -m app.agents.tam_demo

Show the executive summary, risks, talking points, and recommended actions.

5. Automated Validation

Run:

pytest -q

Then:

python -m evaluation.run_evaluation

Expected validation:

18 passed


10/10 evaluation cases passed
100% evaluation score
Final Project Status

The current implementation successfully demonstrates:

RAG-based ticket triage
Knowledge-base grounding
Structured LLM output
Deterministic account-health scoring
Data-quality detection
TAM executive summarization
Regression testing
Automated evaluation
PROJECT VALIDATION


Pytest:              18/18 PASS
Evaluation:          12/12 PASS
Adversarial Evaluation: 2/2 PASS
Evaluation Score:    100%

6. Thin UI

Run:

streamlit run ui/streamlit_app.py

Demonstrate:

- Ticket Triage
- Account Health
- TAM Summary

The Streamlit application calls the FastAPI backend and presents the structured results through a simple user interface.