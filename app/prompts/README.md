\# Prompt Engineering



\## Triage Prompt



The ticket-triage agent uses a versioned prompt stored in:



`app/prompts/triage\_v1.py`



\### Current Version



\*\*Version:\*\* `1.0.0`



\### Purpose



The triage prompt converts a customer support ticket and retrieved knowledge-base evidence into a structured triage result.



The prompt is designed to:



\- Classify the affected product and product area.

\- Assign a supported ticket category.

\- Determine ticket urgency.

\- Ground known-issue detection in retrieved KB evidence.

\- Return the relevant KB document when the issue is grounded.

\- Recommend the appropriate responder team.

\- Generate a concise customer-facing first response.



\### Grounding Strategy



The model is instructed to use only:



1\. Ticket information supplied by the customer.

2\. Retrieved knowledge-base evidence.



The prompt explicitly prevents unsupported product, customer, and KB claims.



\### Output Contract



The model returns structured JSON using the required lowercase `snake\_case` fields:



\- `product`

\- `product\_area`

\- `category`

\- `urgency`

\- `reasoning`

\- `known\_issue`

\- `kb\_document`

\- `recommended\_responder\_team`

\- `first\_response`



\### Version History



\#### 1.0.0 — Initial Production Version



\- Added structured JSON output requirements.

\- Added explicit category definitions.

\- Added urgency classification rules.

\- Added KB grounding requirements.

\- Added known-issue detection based on retrieved evidence.

\- Added responder-team recommendation.

\- Added customer-facing first-response guidance.

\- Added safeguards against fabricated KB and customer information.

\- Added protection against exposing hidden chain-of-thought.



\### Design Principle



Prompt changes should be versioned and evaluated against the existing evaluation suite before being promoted. This keeps prompt behavior reproducible and reduces the risk of regressions.

