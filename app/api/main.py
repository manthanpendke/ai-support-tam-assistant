from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.agents.factory import build_retriever
from app.agents.tam_agent import TAMAgent
from app.agents.triage_agent import TriageAgent
from app.services.account_health import AccountHealthService
from app.services.data_loader import get_account


app = FastAPI(
    title="AI Support & TAM Assistant",
    description=(
        "AI-powered technical support ticket triage, "
        "account health analysis, and TAM executive summaries."
    ),
    version="1.0.0",
)


_retriever = build_retriever()

_triage_agent = TriageAgent(
    retriever=_retriever,
    top_k=8,
)

_account_health_service = AccountHealthService()

_tam_agent = TAMAgent()


class TriageRequest(BaseModel):
    subject: str = Field(
        min_length=1,
        description="Support ticket subject.",
    )

    body: str = Field(
        min_length=1,
        description="Support ticket body.",
    )


class AccountHealthRequest(BaseModel):
    account_id: str = Field(
        min_length=1,
        description="Customer account ID.",
    )

    reference_time: datetime | None = Field(
        default=None,
        description=(
            "Reference timestamp used for deterministic "
            "90-day and 30-day ticket calculations."
        ),
    )


@app.get("/")
def root():
    return {
        "service": "AI Support & TAM Assistant",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "triage": "/triage",
            "account_health": "/accounts/{account_id}/health",
            "tam_summary": "/accounts/{account_id}/tam-summary",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Support & TAM Assistant",
    }


@app.post("/triage")
def triage_ticket(
    request: TriageRequest,
):
    try:
        result = _triage_agent.triage(
            subject=request.subject,
            body=request.body,
        )

        return result.model_dump()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Ticket triage failed.",
        ) from exc



@app.post("/triage/stream")
def triage_ticket_stream(
    request: TriageRequest,
):
    def generate():
        try:
            yield from _triage_agent.triage_stream(
                subject=request.subject,
                body=request.body,
            )
        except ValueError as exc:
            yield f"\nError: {exc}"
        except Exception:
            yield "\nError: Ticket triage streaming failed."

    return StreamingResponse(
        generate(),
        media_type="text/plain",
    )


@app.post(
    "/accounts/{account_id}/health",
)
def account_health(
    account_id: str,
    request: AccountHealthRequest | None = None,
):
    account = get_account(account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_id}' was not found.",
        )

    reference_time = (
        request.reference_time
        if request is not None
        and request.reference_time is not None
        else datetime.now(timezone.utc)
    )

    try:
        result = _account_health_service.analyze(
            account_id=account_id,
            reference_time=reference_time,
        )

        return result.model_dump()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Account health calculation failed.",
        ) from exc


@app.post(
    "/accounts/{account_id}/tam-summary",
)
def tam_summary(
    account_id: str,
    request: AccountHealthRequest | None = None,
):
    account = get_account(account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail=f"Account '{account_id}' was not found.",
        )

    reference_time = (
        request.reference_time
        if request is not None
        and request.reference_time is not None
        else datetime.now(timezone.utc)
    )

    try:
        health_result = _account_health_service.analyze(
            account_id=account_id,
            reference_time=reference_time,
        )

        result = _tam_agent.analyze(
            account_health=health_result,
            account=account,
        )

        return result.model_dump()

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="TAM executive summary generation failed.",
        ) from exc