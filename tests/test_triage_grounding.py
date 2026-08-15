from app.agents.factory import build_retriever
from app.agents.triage_agent import TriageAgent


def test_connection_timeout_is_grounded_to_error_reference():
    retriever = build_retriever()

    agent = TriageAgent(
        retriever=retriever,
        top_k=8,
    )

    result = agent.triage(
        subject="DataBridge Pro connection timeout",
        body=(
            "Our DataBridge Pro pipeline has been failing "
            "with ERR_CONNECTION_TIMEOUT after 30 seconds. "
            "We are unable to complete the data transfer."
        ),
    )

    assert result.known_issue is True

    assert (
        result.kb_document
        == "troubleshooting\\performance-and-integrations.md"
    )