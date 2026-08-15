from app.agents.factory import build_retriever
from app.agents.triage_agent import TriageAgent


def main():

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

    print("\nTASK 1 — TICKET TRIAGE\n")

    print(
        result.model_dump_json(
            indent=2
        )
    )


if __name__ == "__main__":
    main()