from __future__ import annotations

import os
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from sqlalchemy import create_engine, delete, update
from sqlalchemy.orm import Session

from app.db.schemas import Base
from app.db.schemas.accounts import AccountSchema
from app.db.schemas.activity_events import ActivityEventSchema
from app.db.schemas.agent_runs import AgentRunSchema
from app.db.schemas.budgets import BudgetSchema
from app.db.schemas.categories import CategorySchema
from app.db.schemas.draft_transactions import DraftTransactionSchema
from app.db.schemas.import_events import ImportEventSchema
from app.db.schemas.import_jobs import ImportJobSchema
from app.db.schemas.imports import ImportSchema
from app.db.schemas.learned_rules import LearnedRuleSchema
from app.db.schemas.transactions import TransactionSchema
from app.db.schemas.uploaded_files import UploadedFileSchema
from app.db.schemas.users import UserSchema


DEMO_USER_ID = "user_demo"
DEMO_IMPORT_ID = "imp_demo_may_2026"
DEMO_FILE_ID = "file_demo_statement"
DEMO_ACCOUNT_IDS = ["acct_demo_checking", "acct_demo_credit"]
DEMO_CATEGORY_IDS = [
    "cat_demo_food",
    "cat_demo_transportation",
    "cat_demo_health",
    "cat_demo_leisure",
    "cat_demo_home",
    "cat_demo_others",
]
DEMO_BUDGET_IDS = ["bdg_demo_food_may", "bdg_demo_transport_may"]
DEMO_JOB_ID = "job_demo_import"
DEMO_EVENT_IDS = [
    "ievt_demo_uploaded",
    "ievt_demo_extracting",
    "ievt_demo_draft_ready",
    "ievt_demo_committed",
]
DEMO_AGENT_RUN_ID = "arun_demo_statement"
DEMO_DRAFT_IDS = ["dtx_demo_market", "dtx_demo_uber", "dtx_demo_pharmacy"]
DEMO_TRANSACTION_IDS = ["tx_demo_market", "tx_demo_uber", "tx_demo_pharmacy"]
DEMO_RULE_ID = "rule_demo_market_food"
DEMO_ACTIVITY_IDS = [
    "act_demo_import_created",
    "act_demo_import_committed",
    "act_demo_rule_learned",
]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def database_url() -> str:
    backend_dir = Path(__file__).resolve().parents[1]
    load_env_file(backend_dir / ".env")

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add it to backend/.env or export it before running."
        )
    return url


def clear_demo_data(session: Session) -> None:
    session.execute(
        update(DraftTransactionSchema)
        .where(DraftTransactionSchema.id.in_(DEMO_DRAFT_IDS))
        .values(
            duplicate_of_transaction_id=None,
            committed_transaction_id=None,
        )
    )
    session.execute(
        update(TransactionSchema)
        .where(TransactionSchema.id.in_(DEMO_TRANSACTION_IDS))
        .values(source_draft_transaction_id=None)
    )

    delete_steps: Iterable[tuple[type, list[str]]] = [
        (ActivityEventSchema, DEMO_ACTIVITY_IDS),
        (LearnedRuleSchema, [DEMO_RULE_ID]),
        (TransactionSchema, DEMO_TRANSACTION_IDS),
        (DraftTransactionSchema, DEMO_DRAFT_IDS),
        (AgentRunSchema, [DEMO_AGENT_RUN_ID]),
        (ImportEventSchema, DEMO_EVENT_IDS),
        (ImportJobSchema, [DEMO_JOB_ID]),
        (ImportSchema, [DEMO_IMPORT_ID]),
        (UploadedFileSchema, [DEMO_FILE_ID]),
        (BudgetSchema, DEMO_BUDGET_IDS),
        (AccountSchema, DEMO_ACCOUNT_IDS),
        (CategorySchema, DEMO_CATEGORY_IDS),
        (UserSchema, [DEMO_USER_ID]),
    ]

    for schema, ids in delete_steps:
        session.execute(delete(schema).where(schema.id.in_(ids)))


def seed_demo_data(session: Session) -> None:
    now = datetime.utcnow()

    user = UserSchema(
        id=DEMO_USER_ID,
        email="demo@gabrr.local",
        display_name="Demo User",
    )
    session.add(user)
    session.flush()

    checking = AccountSchema(
        id="acct_demo_checking",
        user_id=DEMO_USER_ID,
        name="Main Checking",
        type="checking",
        institution_name="Banco Demo",
        currency="BRL",
        opening_balance=Decimal("2500.00"),
    )
    credit = AccountSchema(
        id="acct_demo_credit",
        user_id=DEMO_USER_ID,
        name="Everyday Credit Card",
        type="credit_card",
        institution_name="Card Demo",
        currency="BRL",
        opening_balance=Decimal("0.00"),
    )
    session.add_all([checking, credit])

    categories = [
        CategorySchema(id="cat_demo_food", user_id=DEMO_USER_ID, key="food", name="Food"),
        CategorySchema(
            id="cat_demo_transportation",
            user_id=DEMO_USER_ID,
            key="transportation",
            name="Transportation",
        ),
        CategorySchema(id="cat_demo_health", user_id=DEMO_USER_ID, key="health", name="Health"),
        CategorySchema(
            id="cat_demo_leisure",
            user_id=DEMO_USER_ID,
            key="leisure",
            name="Leisure",
        ),
        CategorySchema(id="cat_demo_home", user_id=DEMO_USER_ID, key="home", name="Home"),
        CategorySchema(
            id="cat_demo_others",
            user_id=DEMO_USER_ID,
            key="others",
            name="Others",
        ),
    ]
    session.add_all(categories)
    session.flush()

    budgets = [
        BudgetSchema(
            id="bdg_demo_food_may",
            user_id=DEMO_USER_ID,
            category_id="cat_demo_food",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 31),
            amount=Decimal("1200.00"),
            currency="BRL",
        ),
        BudgetSchema(
            id="bdg_demo_transport_may",
            user_id=DEMO_USER_ID,
            category_id="cat_demo_transportation",
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 31),
            amount=Decimal("500.00"),
            currency="BRL",
        ),
    ]
    session.add_all(budgets)

    uploaded_file = UploadedFileSchema(
        id=DEMO_FILE_ID,
        user_id=DEMO_USER_ID,
        filename="demo-may-2026-statement.pdf",
        content_type="application/pdf",
        size_bytes=482102,
        checksum="demo-checksum-may-2026",
        storage_path="local://demo/demo-may-2026-statement.pdf",
        status="stored",
    )
    session.add(uploaded_file)
    session.flush()

    import_record = ImportSchema(
        id=DEMO_IMPORT_ID,
        user_id=DEMO_USER_ID,
        uploaded_file_id=DEMO_FILE_ID,
        status="committed",
        source_type="pdf",
        progress=100,
        current_step="committed",
        completed_at=now,
        committed_at=now,
    )
    session.add(import_record)
    session.flush()

    import_job = ImportJobSchema(
        id=DEMO_JOB_ID,
        import_id=DEMO_IMPORT_ID,
        status="succeeded",
        attempts=1,
        started_at=now,
        finished_at=now,
    )
    session.add(import_job)

    events = [
        ImportEventSchema(
            id="ievt_demo_uploaded",
            import_id=DEMO_IMPORT_ID,
            event_type="uploaded",
            message="Statement uploaded",
            progress=10,
            payload_json={"filename": "demo-may-2026-statement.pdf"},
        ),
        ImportEventSchema(
            id="ievt_demo_extracting",
            import_id=DEMO_IMPORT_ID,
            event_type="extracting",
            message="Extracting transactions",
            progress=45,
            payload_json={"extractor": "demo"},
        ),
        ImportEventSchema(
            id="ievt_demo_draft_ready",
            import_id=DEMO_IMPORT_ID,
            event_type="draft_ready",
            message="Draft transactions ready for review",
            progress=80,
            payload_json={"draft_count": 3},
        ),
        ImportEventSchema(
            id="ievt_demo_committed",
            import_id=DEMO_IMPORT_ID,
            event_type="committed",
            message="Approved transactions committed",
            progress=100,
            payload_json={"transaction_count": 3},
        ),
    ]
    session.add_all(events)

    agent_run = AgentRunSchema(
        id=DEMO_AGENT_RUN_ID,
        import_id=DEMO_IMPORT_ID,
        uploaded_file_id=DEMO_FILE_ID,
        agent_name="statement_normalizer",
        model_name="demo-model",
        status="succeeded",
        input_payload_json={"file_id": DEMO_FILE_ID},
        output_payload_json={
            "transactions": [
                {"description": "Market Demo", "amount": "-142.80"},
                {"description": "Uber Trip", "amount": "-26.10"},
                {"description": "Pharmacy Demo", "amount": "-58.20"},
            ]
        },
        started_at=now,
        finished_at=now,
    )
    session.add(agent_run)
    session.flush()

    drafts = [
        DraftTransactionSchema(
            id="dtx_demo_market",
            import_id=DEMO_IMPORT_ID,
            source_row_index=1,
            account_id="acct_demo_credit",
            category_id="cat_demo_food",
            posted_at=date(2026, 5, 2),
            description="MARKET DEMO SAO PAULO",
            merchant_name="Market Demo",
            amount=Decimal("-142.80"),
            currency="BRL",
            confidence=Decimal("0.9200"),
            needs_review=False,
            status="committed",
            raw_payload_json={"source": "demo row 1"},
            committed_transaction_id=None,
        ),
        DraftTransactionSchema(
            id="dtx_demo_uber",
            import_id=DEMO_IMPORT_ID,
            source_row_index=2,
            account_id="acct_demo_credit",
            category_id="cat_demo_transportation",
            posted_at=date(2026, 5, 3),
            description="UBER TRIP HELP.UBER.COM",
            merchant_name="Uber",
            amount=Decimal("-26.10"),
            currency="BRL",
            confidence=Decimal("0.9700"),
            needs_review=False,
            status="committed",
            raw_payload_json={"source": "demo row 2"},
            committed_transaction_id=None,
        ),
        DraftTransactionSchema(
            id="dtx_demo_pharmacy",
            import_id=DEMO_IMPORT_ID,
            source_row_index=3,
            account_id="acct_demo_credit",
            category_id="cat_demo_health",
            posted_at=date(2026, 5, 4),
            description="PHARMACY DEMO",
            merchant_name="Pharmacy Demo",
            amount=Decimal("-58.20"),
            currency="BRL",
            confidence=Decimal("0.7600"),
            needs_review=True,
            review_reason="Lower confidence category suggestion",
            status="committed",
            raw_payload_json={"source": "demo row 3"},
            committed_transaction_id=None,
        ),
    ]
    session.add_all(drafts)
    session.flush()

    transactions = [
        TransactionSchema(
            id="tx_demo_market",
            user_id=DEMO_USER_ID,
            account_id="acct_demo_credit",
            category_id="cat_demo_food",
            source_import_id=DEMO_IMPORT_ID,
            source_draft_transaction_id="dtx_demo_market",
            posted_at=date(2026, 5, 2),
            description="MARKET DEMO SAO PAULO",
            merchant_name="Market Demo",
            amount=Decimal("-142.80"),
            currency="BRL",
        ),
        TransactionSchema(
            id="tx_demo_uber",
            user_id=DEMO_USER_ID,
            account_id="acct_demo_credit",
            category_id="cat_demo_transportation",
            source_import_id=DEMO_IMPORT_ID,
            source_draft_transaction_id="dtx_demo_uber",
            posted_at=date(2026, 5, 3),
            description="UBER TRIP HELP.UBER.COM",
            merchant_name="Uber",
            amount=Decimal("-26.10"),
            currency="BRL",
        ),
        TransactionSchema(
            id="tx_demo_pharmacy",
            user_id=DEMO_USER_ID,
            account_id="acct_demo_credit",
            category_id="cat_demo_health",
            source_import_id=DEMO_IMPORT_ID,
            source_draft_transaction_id="dtx_demo_pharmacy",
            posted_at=date(2026, 5, 4),
            description="PHARMACY DEMO",
            merchant_name="Pharmacy Demo",
            amount=Decimal("-58.20"),
            currency="BRL",
        ),
    ]
    session.add_all(transactions)
    session.flush()

    for draft, tx_id in zip(drafts, DEMO_TRANSACTION_IDS, strict=True):
        draft.committed_transaction_id = tx_id
    session.flush()

    learned_rule = LearnedRuleSchema(
        id=DEMO_RULE_ID,
        user_id=DEMO_USER_ID,
        rule_type="merchant_category",
        match_pattern="Market Demo",
        result_payload_json={"category_id": "cat_demo_food"},
        confidence=Decimal("0.9500"),
        source="user_review",
        is_active=True,
    )
    session.add(learned_rule)

    activity_events = [
        ActivityEventSchema(
            id="act_demo_import_created",
            user_id=DEMO_USER_ID,
            event_type="import_created",
            entity_type="import",
            entity_id=DEMO_IMPORT_ID,
            import_id=DEMO_IMPORT_ID,
            payload_json={"filename": "demo-may-2026-statement.pdf"},
            undoable=False,
        ),
        ActivityEventSchema(
            id="act_demo_import_committed",
            user_id=DEMO_USER_ID,
            event_type="import_committed",
            entity_type="import",
            entity_id=DEMO_IMPORT_ID,
            import_id=DEMO_IMPORT_ID,
            payload_json={"transaction_count": 3},
            undoable=True,
        ),
        ActivityEventSchema(
            id="act_demo_rule_learned",
            user_id=DEMO_USER_ID,
            event_type="learned_rule_created",
            entity_type="learned_rule",
            entity_id=DEMO_RULE_ID,
            payload_json={"match_pattern": "Market Demo"},
            undoable=True,
        ),
    ]
    session.add_all(activity_events)


def main() -> None:
    url = database_url()
    engine = create_engine(url)

    # Helpful for first local setup. Alembic migrations should own real schema
    # evolution once the migration files are in place.
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        clear_demo_data(session)
        seed_demo_data(session)
        session.commit()

    print("Seeded demo data successfully.")
    print("Database URL was read from DATABASE_URL.")
    print("Demo user id:", DEMO_USER_ID)
    print("Demo import id:", DEMO_IMPORT_ID)


if __name__ == "__main__":
    main()
