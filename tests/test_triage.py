from app.agents.factory import build_retriever
from app.agents.triage_agent import TriageAgent


def build_agent():
    retriever = build_retriever()

    return TriageAgent(
        retriever=retriever,
        top_k=8,
    )


def test_connection_timeout_triage():
    agent = build_agent()

    result = agent.triage(
        subject="DataBridge Pro connection timeout",
        body=(
            "Our DataBridge Pro pipeline has been failing "
            "with ERR_CONNECTION_TIMEOUT after 30 seconds. "
            "We are unable to complete the data transfer."
        ),
    )

    assert result.product == "DataBridge Pro"

    assert result.urgency in {
        "P1",
        "P2",
        "P3",
        "P4",
    }

    assert result.known_issue is True

    assert (
        result.kb_document
        == "troubleshooting\\performance-and-integrations.md"
    )

    assert result.first_response.strip()


def test_empty_subject_is_rejected():
    agent = build_agent()

    try:
        agent.triage(
            subject="",
            body="The pipeline is failing.",
        )

        assert False, "Expected ValueError"

    except ValueError as exc:
        assert "subject" in str(exc).lower()


def test_empty_body_is_rejected():
    agent = build_agent()

    try:
        agent.triage(
            subject="DataBridge Pro issue",
            body="",
        )

        assert False, "Expected ValueError"

    except ValueError as exc:
        assert "body" in str(exc).lower()