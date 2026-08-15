import json

import requests
import streamlit as st


API_BASE_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="AI Support & TAM Assistant",
    page_icon="🤖",
    layout="wide",
)


st.title("🤖 AI Support & TAM Assistant")
st.caption(
    "Technical Support triage and Technical Account Management assistant"
)


def call_api(
    method: str,
    endpoint: str,
    payload: dict,
):
    try:
        response = requests.request(
            method=method,
            url=f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=120,
        )

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text

            st.error(
                f"API request failed ({response.status_code})"
            )

            st.code(
                json.dumps(
                    detail,
                    indent=2,
                )
            )

            return None

        return response.json()

    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the FastAPI backend. "
            "Start it with: uvicorn app.api.main:app --reload"
        )

        return None

    except requests.exceptions.Timeout:
        st.error(
            "The request timed out. Please try again."
        )

        return None

    except Exception as exc:
        st.error(
            f"Unexpected error: {exc}"
        )

        return None


def stream_api(
    endpoint: str,
    payload: dict,
):
    try:
        with requests.post(
            url=f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=120,
            stream=True,
        ) as response:

            response.raise_for_status()

            for chunk in response.iter_content(
                chunk_size=None,
                decode_unicode=True,
            ):
                if chunk:
                    yield chunk

    except requests.RequestException as exc:
        st.error(
            f"Streaming request failed: {exc}"
        )




def render_json(data: dict):
    st.json(data)


triage_tab, health_tab, tam_tab = st.tabs(
    [
        "🎫 Ticket Triage",
        "🏢 Account Health",
        "👤 TAM Summary",
    ]
)


with triage_tab:

    st.header("Ticket Triage")

    st.write(
        "Submit a support ticket to classify the product area, "
        "category, urgency, known issue status, responder team, "
        "and first response."
    )

    subject = st.text_input(
        "Ticket Subject",
        placeholder="Example: DataBridge Pro connection timeout",
        key="triage_subject",
    )

    body = st.text_area(
        "Ticket Description",
        placeholder=(
            "Describe the customer issue, error message, "
            "impact, and any relevant context..."
        ),
        height=220,
        key="triage_body",
    )

    if st.button(
        "Analyze Ticket",
        type="primary",
        key="triage_button",
    ):

        if not subject.strip():
            st.warning(
                "Please enter a ticket subject."
            )

        elif not body.strip():
            st.warning(
                "Please enter the ticket description."
            )

        else:

            with st.spinner(
                "Analyzing ticket..."
            ):

                result = call_api(
                    "POST",
                    "/triage",
                    {
                        "subject": subject,
                        "body": body,
                    },
                )

            if result:

                st.success(
                    "Ticket triage completed."
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Product",
                        result.get(
                            "product",
                            "Unknown",
                        ),
                    )

                with col2:
                    st.metric(
                        "Category",
                        result.get(
                            "category",
                            "Unknown",
                        ),
                    )

                with col3:
                    st.metric(
                        "Urgency",
                        result.get(
                            "urgency",
                            "Unknown",
                        ),
                    )

                with col4:
                    st.metric(
                        "Known Issue",
                        "Yes"
                        if result.get(
                            "known_issue",
                            False,
                        )
                        else "No",
                    )

                st.subheader(
                    "Triage Details"
                )

                st.write(
                    "**Product Area:**",
                    result.get(
                        "product_area",
                        "Not available",
                    ),
                )

                st.write(
                    "**Recommended Responder Team:**",
                    result.get(
                        "recommended_responder_team",
                        "Not available",
                    ),
                )

                if result.get("kb_document"):
                    st.write(
                        "**Knowledge Base Document:**",
                        result["kb_document"],
                    )

                st.subheader(
                    "Reasoning"
                )

                st.info(
                    result.get(
                        "reasoning",
                        "No reasoning available.",
                    )
                )

                st.subheader(
                    "Suggested First Response"
                )

                st.text_area(
                    "Customer Response",
                    value=result.get(
                        "first_response",
                        "",
                    ),
                    height=150,
                    disabled=True,
                    key="triage_response",
                )

                with st.expander(
                    "View complete response"
                ):
                    render_json(result)



    st.divider()

    st.subheader("Streaming Demo")

    st.caption(
        "Streams the LLM response progressively from the "
        "technical-support triage pipeline."
    )

    if st.button(
        "▶ Stream Analysis",
        key="triage_stream_button",
    ):
        if not subject.strip():
            st.warning(
                "Please enter a ticket subject."
            )

        elif not body.strip():
            st.warning(
                "Please enter the ticket description."
            )

        else:
            st.write("### Live Response")

            stream = stream_api(
                "/triage/stream",
                {
                    "subject": subject,
                    "body": body,
                },
            )

            st.write_stream(stream)


with health_tab:

    st.header("Account Health")

    st.write(
        "Review deterministic account-health metrics "
        "for a customer account."
    )

    account_id = st.text_input(
        "Account ID",
        placeholder="Example: ACC-3336",
        key="health_account_id",
    )

    reference_time = st.text_input(
        "Reference Time (optional)",
        placeholder="2026-05-22T00:23:32.203871Z",
        key="health_reference_time",
    )

    if st.button(
        "Analyze Account",
        type="primary",
        key="health_button",
    ):

        if not account_id.strip():
            st.warning(
                "Please enter an account ID."
            )

        else:

            payload = {
                "account_id": account_id.strip(),
            }

            if reference_time.strip():
                payload[
                    "reference_time"
                ] = reference_time.strip()

            with st.spinner(
                "Calculating account health..."
            ):

                result = call_api(
                    "POST",
                    f"/accounts/{account_id.strip()}/health",
                    payload,
                )

            if result:

                st.success(
                    "Account health calculated."
                )

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric(
                        "Account",
                        result.get(
                            "account_name",
                            account_id,
                        ),
                    )

                with col2:
                    st.metric(
                        "Health Score",
                        result.get(
                            "health_score",
                            "N/A",
                        ),
                    )

                with col3:
                    st.metric(
                        "Status",
                        result.get(
                            "health_status",
                            "N/A",
                        ),
                    )

                with col4:
                    st.metric(
                        "Open Tickets",
                        result.get(
                            "open_ticket_count",
                            0,
                        ),
                    )

                st.subheader(
                    "Account Overview"
                )

                overview_col1, overview_col2 = st.columns(2)

                with overview_col1:

                    st.write(
                        "**TAM:**",
                        result.get(
                            "tam",
                            "N/A",
                        ),
                    )

                    st.write(
                        "**Plan:**",
                        result.get(
                            "plan_tier",
                            "N/A",
                        ),
                    )

                    st.write(
                        "**ARR:**",
                        result.get(
                            "arr_usd",
                            "N/A",
                        ),
                    )

                    st.write(
                        "**Usage Trend:**",
                        result.get(
                            "usage_trend",
                            "N/A",
                        ),
                    )

                with overview_col2:

                    st.write(
                        "**90-Day Tickets:**",
                        result.get(
                            "ticket_count_90d",
                            0,
                        ),
                    )

                    st.write(
                        "**30-Day Tickets:**",
                        result.get(
                            "recent_ticket_count_30d",
                            0,
                        ),
                    )

                    st.write(
                        "**Days to Renewal:**",
                        result.get(
                            "days_to_renewal",
                            "N/A",
                        ),
                    )

                    st.write(
                        "**Seat Utilization:**",
                        f"{result.get('seats_utilization_percent', 0):.2f}%",
                    )

                warnings = result.get(
                    "data_quality_warnings",
                    [],
                )

                if warnings:

                    st.subheader(
                        "Data Quality Warnings"
                    )

                    for warning in warnings:
                        st.warning(
                            warning
                        )

                with st.expander(
                    "View complete account health"
                ):
                    render_json(result)


with tam_tab:

    st.header("TAM Executive Summary")

    st.write(
        "Generate an actionable customer brief for "
        "TAM preparation and customer conversations."
    )

    tam_account_id = st.text_input(
        "Account ID",
        placeholder="Example: ACC-3336",
        key="tam_account_id",
    )

    tam_reference_time = st.text_input(
        "Reference Time (optional)",
        placeholder="2026-05-22T00:23:32.203871Z",
        key="tam_reference_time",
    )

    if st.button(
        "Generate TAM Summary",
        type="primary",
        key="tam_button",
    ):

        if not tam_account_id.strip():
            st.warning(
                "Please enter an account ID."
            )

        else:

            payload = {
                "account_id": tam_account_id.strip(),
            }

            if tam_reference_time.strip():
                payload[
                    "reference_time"
                ] = tam_reference_time.strip()

            with st.spinner(
                "Generating TAM executive summary..."
            ):

                result = call_api(
                    "POST",
                    f"/accounts/{tam_account_id.strip()}/tam-summary",
                    payload,
                )

            if result:

                st.success(
                    "TAM summary generated."
                )

                st.subheader(
                    "Executive Summary"
                )

                st.info(
                    result.get(
                        "executive_summary",
                        "No summary available.",
                    )
                )

                st.subheader(
                    "Open Risks"
                )

                risks = result.get(
                    "open_risks",
                    [],
                )

                if risks:

                    for risk in risks:

                        flag = risk.get(
                            "flag",
                            "Risk",
                        )

                        reason = risk.get(
                            "reason",
                            "",
                        )

                        ticket_id = risk.get(
                            "ticket_id",
                        )

                        evidence = risk.get(
                            "evidence_quote",
                        )

                        with st.expander(
                            flag
                        ):

                            st.write(
                                "**Reason:**",
                                reason,
                            )

                            if ticket_id:
                                st.write(
                                    "**Ticket:**",
                                    ticket_id,
                                )

                            if evidence:
                                st.write(
                                    "**Evidence:**"
                                )

                                st.info(
                                    evidence
                                )

                else:

                    st.write(
                        "No open risks identified."
                    )

                st.subheader(
                    "Talking Points"
                )

                talking_points = result.get(
                    "talking_points",
                    [],
                )

                for point in talking_points:
                    st.write(
                        f"• {point}"
                    )

                st.subheader(
                    "Recommended Actions"
                )

                actions = result.get(
                    "recommended_actions",
                    [],
                )

                for action in actions:
                    st.write(
                        f"• {action}"
                    )

                with st.expander(
                    "View complete TAM response"
                ):
                    render_json(result)


st.divider()

st.caption(
    "AI Support & TAM Assistant • Thin UI over the FastAPI service"
)