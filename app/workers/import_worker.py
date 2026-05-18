from __future__ import annotations

import argparse
import asyncio
import logging
import socket
import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.agents.factory import create_agent_gateway
from app.agents.models import AgentProgressEvent
from app.config import settings
from app.db.models.transaction import Transaction
from app.db.repositories.import_jobs import ImportJobRepository
from app.db.repositories.transactions import TransactionRepository
from app.db.session import SessionLocal

_import_job_repository = ImportJobRepository()
_transaction_repository = TransactionRepository()
logger = logging.getLogger(__name__)


def map_agent_result_to_transactions(agent_result: dict[str, Any]) -> list[Transaction]:
    rows = agent_result.get("transactions")
    if not isinstance(rows, list):
        raise ValueError("Agent result must include a transactions list.")

    transactions: list[Transaction] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid transaction at index {index}: row must be an object")

        missing = {"date", "description", "amount"} - set(row)
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"Invalid transaction at index {index}: missing {missing_fields}")

        posted_at = _parse_date(row["date"], index=index)

        try:
            amount = Decimal(str(row["amount"]))
        except (InvalidOperation, ValueError) as error:
            raise ValueError(f"Invalid transaction at index {index}: invalid amount") from error

        description = str(row["description"]).strip()
        if not description:
            raise ValueError(f"Invalid transaction at index {index}: description is required")

        transactions.append(
            Transaction(
                posted_at=posted_at,
                date=posted_at,
                description=description,
                merchant_name=_optional_string(row.get("merchant_name")),
                amount=amount,
                currency="BRL",
                payment_method=_optional_string(row.get("payment_method")),
                installments=_optional_int(row.get("installments")),
                installments_current=_optional_int(row.get("installments_current")),
                is_draft=True,
            )
        )

    return transactions


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def _parse_date(value: object, *, index: int) -> date:
    raw_value = str(value).strip()
    if not raw_value:
        raise ValueError(f"Invalid transaction at index {index}: date is required")

    for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            return datetime.strptime(raw_value, date_format).date()
        except ValueError:
            pass

    for date_format in ("%d/%m", "%d-%m"):
        try:
            parsed = datetime.strptime(raw_value, date_format)
            return date(date.today().year, parsed.month, parsed.day)
        except ValueError:
            pass

    raise ValueError(f"Invalid transaction at index {index}: invalid date")


async def process_job(job_id: str) -> None:
    with SessionLocal() as session:
        job = _import_job_repository.get_by_id(session, job_id=job_id)
        if job is None:
            return
        if job.status == "done":
            return

        user_id = job.user_id
        storage_path = job.storage_path
        _import_job_repository.mark_step(
            session,
            job_id,
            current_step="Processing started",
        )
        session.commit()

    agent_input = {"storage_path": storage_path}

    try:
        with SessionLocal() as session:
            _import_job_repository.save_agent_input(
                session,
                job_id,
                input_payload_json=agent_input,
            )
            _import_job_repository.mark_step(
                session,
                job_id,
                current_step="Reading PDF with agent",
            )
            session.commit()

        last_agent_step: str | None = None

        async def handle_agent_progress(event: AgentProgressEvent) -> None:
            nonlocal last_agent_step

            if event.message == last_agent_step:
                return

            last_agent_step = event.message
            with SessionLocal() as session:
                _import_job_repository.mark_step(
                    session,
                    job_id,
                    current_step=event.message,
                )
                session.commit()

        agent_gateway = create_agent_gateway()
        result = await agent_gateway.extract_statement_transactions(
            storage_path,
            user_id=user_id,
            on_progress=handle_agent_progress,
        )

        if result.status != "success":
            raise ValueError("Agent failed to return valid JSON.")

        agent_data = result.data
        if not isinstance(agent_data, dict):
            raise ValueError("Agent result data must be a JSON object.")

        with SessionLocal() as session:
            _import_job_repository.save_agent_output(
                session,
                job_id,
                output_payload_json={"status": result.status, "data": result.data},
            )
            _import_job_repository.mark_step(
                session,
                job_id,
                current_step="Validating transactions",
            )
            session.commit()

        with SessionLocal() as session:
            transactions = map_agent_result_to_transactions(agent_data)
            _transaction_repository.create_many(
                session,
                transactions,
                default_user_id=user_id,
                default_account_id=settings.default_account_id,
            )
            _import_job_repository.mark_step(
                session,
                job_id,
                current_step="Draft transactions saved",
            )
            _import_job_repository.mark_done(session, job_id)
            session.commit()
    except Exception as error:
        with SessionLocal() as session:
            _import_job_repository.mark_failed(session, job_id, error_message=str(error))
            session.commit()
        logger.exception("Import job %s failed", job_id)


async def run_worker(worker_id: str, *, once: bool = False) -> None:
    while True:
        with SessionLocal() as session:
            job = _import_job_repository.claim_next_pending(session, worker_id=worker_id)
            session.commit()

        if job is None:
            if once:
                return
            await asyncio.sleep(2)
            continue

        await process_job(job.id)
        if once:
            return


def _default_worker_id() -> str:
    return f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Process pending PDF import jobs.")
    parser.add_argument("--worker-id", default=_default_worker_id())
    parser.add_argument("--once", action="store_true", help="Process at most one job and exit.")
    args = parser.parse_args()

    asyncio.run(run_worker(args.worker_id, once=args.once))


if __name__ == "__main__":
    main()
