# PDF Import Job Feature

Status: implemented feature plan  
Scope: backend-first implementation plus a minimal frontend test page  
Goal: upload `/Users/gabrieloliveira/Gabrr/gabrr-budget/backend/file_examples/rico-maio.pdf`, create an `import_jobs` row, process it in a separate worker, stream progress with Server-Sent Events (SSE), save transactions as `is_draft=true`, and let the frontend print a simple event timeline.

## Chosen Decisions

- Keep the first upload entrypoint inside `backend/app/api/agents_routes.py` at `POST /agents/process-file`.
- Store PDF bytes outside the database using the current `FileSystemService`.
- Create only one `import_jobs` row for this first version.
- Do not create `imports`, `import_events`, or `agent_runs` in the first implementation.
- Save agent input and output JSON directly on `import_jobs`.
- Use a separate database-backed worker command. This is Option A from the planning page.
- Use Server-Sent Events (SSE) for progress, with normal status polling available as fallback.
- Use fixed progress milestones: `25`, `45`, `70`, `85`, `100`.
- Hardcode transaction currency to `BRL` in the mapper for now.
- Agent JSON contract is minimal: top-level `{ "transactions": [...] }`.
- Do not add `transactions.source_import_job_id` for now.
- Keep only the existing transaction concept. Imported rows are normal transactions with `is_draft=true`.
- The only way to differentiate imported draft rows for now is by querying/filtering transactions, for example `is_draft=true`, date range, or frontend filtering.
- Ignored transactions stay as drafts with `is_draft=true`.
- Accepted transactions become committed in place with `is_draft=false`.

## Product And API Contract

Canonical job statuses:

```text
pending -> processing -> done
pending -> processing -> failed
```

Do not use `queued` in this first version. The UI can display a friendly label, but the backend should persist only `pending`, `processing`, `done`, or `failed`.

Progress milestones:

```text
25 processing: worker claimed the job
45 processing: agent request prepared and saved
70 processing: agent returned JSON
85 processing: drafts validated and saved
100 done: job finished successfully
100 failed: job reached terminal failure
```

Endpoints:

```text
POST /agents/process-file
GET  /import-jobs/{job_id}
GET  /import-jobs/{job_id}/events
GET  /transactions?is_draft=true
PATCH /transactions/{transaction_id}
```

`POST /agents/process-file` accepts multipart form data:

```text
file: PDF upload
user_id: optional form field, defaults to settings.default_user_id for this development version
Idempotency-Key: required header
```

Responses:

```text
202 new job created
200 same Idempotency-Key and same file hash returned existing job
409 same Idempotency-Key reused with different file content
413 file too large
415 unsupported content type
422 missing required request parts, including Idempotency-Key
```

Example response:

```json
{
  "job_id": "job_123",
  "status": "pending",
  "progress": 5,
  "current_step": "Upload received",
  "status_url": "/import-jobs/job_123",
  "events_url": "/import-jobs/job_123/events"
}
```

This is a breaking response-contract change for the existing synchronous `POST /agents/process-file` route. For this feature, that is intentional. If compatibility becomes important, create a new `POST /import-jobs` route instead and leave the old route synchronous.

Implementation note: if the route decorator defaults to `status_code=202`, return an explicit `JSONResponse(status_code=200, content=...)` for idempotent replay.

User ownership for development:

- Upload may accept `user_id`, but the frontend test should rely on `settings.default_user_id`.
- Status and Server-Sent Events endpoints must query by the same user id.
- Transaction filtering should also be scoped by the same user id.
- Server-Sent Events created with browser `EventSource` cannot send custom headers. Do not design the first version around an authorization header on the event stream. Use the development default user now, then replace it with cookie/session auth later.

## Current Codebase Caveats

These were confirmed by code inspection and must be handled during implementation.

- `backend/app/db/schemas/import_jobs.py` currently has a required `import_id` foreign key to `imports.id`.
- `backend/app/db/schemas/imports.py` has the reverse `jobs` relationship. Removing only `import_jobs.import_id` will break mapper configuration.
- `backend/app/db/repositories/transactions.py` has basic CRUD and bulk create. For this version, extend filtering around `is_draft` instead of adding job-scoped draft helpers.
- `backend/app/db/repositories/transactions.py` normal listing must be checked so draft imports do not appear in the regular transactions screen before the user accepts them.
- `backend/app/api/agents_routes.py` currently calls ADK synchronously and returns the agent result.
- `backend/app/api/routes.py` does not mount an import-jobs router yet.
- `backend/app/services/agent_service.py` returns an envelope from `run_json`: `{ "status": "success" | "error", "data": ... }`.
- `backend/app/services/agent_service.py` has an ADK `stream_run_sse` method, but the selected design needs persisted job progress SSE, not direct ADK streaming.
- `backend/app/db/session.py` exposes `SessionLocal`; the worker and SSE generator should use it directly because they run outside normal request-scoped dependency timing.

## Implementation Requirements

### Database Schema

Preferred first implementation: remove the first-version dependency from `import_jobs.import_id`, and also remove the reverse relationship from `imports.jobs`. If that migration is too risky after inspection, keep `import_id` nullable temporarily and stop using it in new code.

Migration sequence:

1. Add new nullable columns to `import_jobs`.
2. Backfill or assert that local `import_jobs` data can tolerate removing `import_id`.
3. Drop relationship-dependent constraints and `import_jobs.import_id`.
4. Make required new job columns non-null if the table is empty or after backfill.
5. Add the unique constraint on `(user_id, idempotency_key)`.

Target `ImportJobSchema` shape:

```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column


class ImportJobSchema(TimestampMixin, Base):
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: new_id("job"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(120))
    source_type: Mapped[str] = mapped_column(String(40), default="pdf", nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(120))
    size_bytes: Mapped[int | None] = mapped_column(Integer)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    agent_input_payload_json: Mapped[dict | None] = mapped_column(JSON)
    agent_output_payload_json: Mapped[dict | None] = mapped_column(JSON)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_by: Mapped[str | None] = mapped_column(String(120))
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(String(1000))

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_import_jobs_user_idempotency_key"),
    )
```

Transaction schema and model changes:

- Do not add `source_import_job_id` in this version.
- Keep `source_import_id` untouched.
- Ensure `is_draft` can be queried and updated through the normal transaction repository/API.

Tradeoff: without a job foreign key on transactions, the backend cannot reliably fetch “transactions created by job X.” That is accepted for this learning/testing version. If two PDF imports run at the same time, the frontend may see all draft transactions unless it applies additional filters.

### Idempotency And Upload Atomicity

Idempotency is based on the client-provided `Idempotency-Key`, scoped to the user. The file hash is used to verify that the same key is not accidentally reused for different content.

```python
existing_job = import_job_repository.get_by_idempotency_key(
    session,
    user_id=user_id,
    idempotency_key=idempotency_key,
)
if existing_job is not None:
    if existing_job.file_hash != file_hash:
        raise HTTPException(status_code=409, detail="Idempotency-Key reused with different file content.")
    return job_response(existing_job)
```

The unique database constraint on `(user_id, idempotency_key)` is still required because two duplicate uploads can arrive at the same time. The route should catch unique-constraint failure, re-query the existing job, compare the file hash, and return that job when hashes match.

File storage and database insert are not atomic. For version 1, handle this with best-effort cleanup:

```python
storage_path = await file_service.save(...)
try:
    job = import_job_repository.create_pending(...)
    session.flush()
except IntegrityError:
    session.rollback()
    existing_job = import_job_repository.get_by_idempotency_key(...)
    file_service.delete_if_exists(storage_path)
    return replay_or_conflict(existing_job, file_hash)
except Exception:
    file_service.delete_if_exists(storage_path)
    raise
```

`FileSystemService` currently does not expose `delete_if_exists`. Add that helper, or use an equivalent safe deletion method in the route cleanup path.

Do not call `session.commit()` inside `POST /agents/process-file` unless there is a specific reason to commit early. The existing `get_session()` dependency commits after the route returns. Use `session.flush()` and `session.refresh(job)` when the route needs the generated job id before returning.

### Worker Requirements

The worker owns slow processing. The upload route only validates, saves the file, creates the job, and returns.

The worker must:

1. Claim one pending job atomically.
2. Mark progress `25`.
3. Build and save the agent input payload.
4. Call the agent.
5. Check the `AgentService.run_json` envelope.
6. Save the raw agent output on the job.
7. Validate and map `{ "transactions": [...] }` to normal transactions with `is_draft=true`.
8. Insert those transactions with the existing transaction repository.
9. Mark progress `85`.
10. Mark the job `done` with progress `100`.

`claim_pending` must be safe for more than one worker process. Use either `SELECT ... FOR UPDATE SKIP LOCKED` inside a transaction, or a single conditional `UPDATE ... WHERE status='pending' RETURNING *`.

Worker sessions must be explicit:

```python
async def run_worker(worker_id: str) -> None:
    while True:
        with SessionLocal() as session:
            job = import_job_repository.claim_next_pending(session, worker_id=worker_id)
            session.commit()

        if job is None:
            await asyncio.sleep(2)
            continue

        await process_job(job.id, worker_id=worker_id)
```

The processing function should use short transactions around database writes instead of keeping one session open during the agent call:

```python
async def process_job(job_id: str, *, worker_id: str) -> None:
    try:
        with SessionLocal() as session:
            job = import_job_repository.get_by_id(session, job_id=job_id)
            user_id = job.user_id
            import_job_repository.mark_progress(session, job_id, progress=25, current_step="Processing started")
            session.commit()

        agent_input = build_agent_input(job)

        with SessionLocal() as session:
            import_job_repository.save_agent_input(session, job_id, input_payload_json=agent_input)
            import_job_repository.mark_progress(session, job_id, progress=45, current_step="Reading PDF with agent")
            session.commit()

        result = await agent_service.run_json(...)

        if result.get("status") != "success":
            raise ValueError("Agent failed to return valid JSON.")

        agent_data = result.get("data")

        with SessionLocal() as session:
            import_job_repository.save_agent_output(session, job_id, output_payload_json=agent_data)
            import_job_repository.mark_progress(session, job_id, progress=70, current_step="Validating transactions")
            transactions = map_agent_result_to_transactions(agent_data)
            transaction_repository.create_many(
                session,
                transactions,
                default_user_id=user_id,
                default_account_id=settings.default_account_id,
            )
            import_job_repository.mark_progress(session, job_id, progress=85, current_step="Drafts saved")
            import_job_repository.mark_done(session, job_id)
            session.commit()
    except Exception as exc:
        with SessionLocal() as session:
            import_job_repository.mark_failed(session, job_id, error_message=str(exc))
            session.commit()
```

Retry and crash behavior:

- First implementation can use `attempts < 3`.
- A stale `processing` job with `locked_at` older than 15 minutes can be reclaimed.
- Retrying a failed job should reuse the same job id, not create a new job.
- Do not retry a `done` job. Without a job link on transactions, retrying a completed job can duplicate transaction rows.

### Agent JSON Contract

The agent must return this minimal shape inside the `data` field of `AgentService.run_json`:

```json
{
  "transactions": [
    {
      "date": "2026-05-10",
      "description": "Uber",
      "amount": "-31.90"
    }
  ]
}
```

Validation rules for version 1:

- `transactions` must exist and must be a list.
- Empty `transactions` is valid and marks the job `done` with zero drafts.
- Each row must have `date`, `description`, and `amount`.
- `date` must be ISO format: `YYYY-MM-DD`.
- `description` must not be empty after trimming.
- `amount` must parse as `Decimal`.
- Unknown fields are ignored for now.
- One invalid row fails the whole job for now.
- No duplicate detection in version 1.
- Currency is hardcoded to `BRL`.

Mapper:

```python
from datetime import date
from decimal import Decimal


def map_agent_result_to_transactions(agent_result: dict) -> list[Transaction]:
    rows = agent_result.get("transactions")
    if not isinstance(rows, list):
        raise ValueError("Agent result must include a transactions list.")

    transactions: list[Transaction] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Invalid transaction at index {index}: row must be an object")

        missing = {"date", "description", "amount"} - set(row)
        if missing:
            raise ValueError(f"Invalid transaction at index {index}: missing {', '.join(sorted(missing))}")

        posted_at = date.fromisoformat(str(row["date"]))
        amount = Decimal(str(row["amount"]))
        description = str(row["description"]).strip()

        if not description:
            raise ValueError(f"Invalid transaction at index {index}: description is required")

        transactions.append(
            Transaction(
                posted_at=posted_at,
                description=description,
                amount=amount,
                currency="BRL",  # TODO: replace hardcoded currency when account or statement currency is available.
                is_draft=True,
            )
        )

    return transactions
```

### Repository Method Requirements

Import job repository:

```python
def get_by_id(session: Session, *, job_id: str, user_id: str | None = None) -> ImportJobSchema | None: ...
def get_by_idempotency_key(session: Session, *, user_id: str, idempotency_key: str) -> ImportJobSchema | None: ...
def create_pending(session: Session, *, user_id: str, idempotency_key: str, file_hash: str, storage_path: str, original_filename: str | None, content_type: str | None, size_bytes: int | None) -> ImportJobSchema: ...
def claim_next_pending(session: Session, *, worker_id: str) -> ImportJobSchema | None: ...
def mark_progress(session: Session, job_id: str, *, progress: int, current_step: str) -> None: ...
def save_agent_input(session: Session, job_id: str, *, input_payload_json: dict) -> None: ...
def save_agent_output(session: Session, job_id: str, *, output_payload_json: dict) -> None: ...
def mark_done(session: Session, job_id: str, *, progress: int = 100) -> None: ...
def mark_failed(session: Session, job_id: str, *, error_message: str) -> None: ...
```

Transaction repository:

```python
def list_filtered(
    self,
    session: Session,
    *,
    user_id: str,
    is_draft: bool | None = None,
) -> list[TransactionSchema]:
    ...
```

```python
def accept_transactions(
    self,
    session: Session,
    *,
    user_id: str,
    transaction_ids: list[str],
) -> int:
    result = session.execute(
        update(TransactionSchema)
        .where(
            TransactionSchema.user_id == user_id,
            TransactionSchema.id.in_(transaction_ids),
            TransactionSchema.is_draft.is_(True),
        )
        .values(is_draft=False)
    )
    return result.rowcount or 0
```

`create_many` is enough for the worker because we are not replacing rows for a specific job. Idempotency prevents duplicate job creation, and the rule “do not retry done jobs” prevents duplicate transaction insertion after success.

### Import Job Routes

Files:

- new `backend/app/api/import_jobs_routes.py`
- update `backend/app/api/routes.py`

`GET /import-jobs/{job_id}` returns current job state or `404`.

Transaction review should use the normal transactions API for now:

- `GET /transactions?is_draft=true` returns draft transactions for the user.
- `PATCH /transactions/{transaction_id}` or a bulk transaction accept endpoint can set selected rows to `is_draft=false`.
- Rows not accepted are ignored by leaving them as `is_draft=true`.

Important visibility rule: normal transaction listing should exclude `is_draft=true` by default. Drafts should appear only when the client explicitly asks for them, for example `GET /transactions?is_draft=true`.

### Server-Sent Events Route

The Server-Sent Events route must not reuse a normal request-scoped SQLAlchemy session forever. Open a short-lived session for each poll, then close it.

```python
@import_jobs_router.get("/import-jobs/{job_id}/events")
async def stream_import_job_events(job_id: str, request: Request):
    async def event_stream():
        while True:
            if await request.is_disconnected():
                return

            with SessionLocal() as session:
                job = job_repository.get_by_id(
                    session,
                    job_id=job_id,
                    user_id=settings.default_user_id,
                )

            if job is None:
                yield 'event: error\ndata: {"message": "Job not found"}\n\n'
                return

            payload = json.dumps({
                "id": job.id,
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
                "error_message": job.error_message,
            })
            yield f"event: progress\ndata: {payload}\n\n"

            if job.status in {"done", "failed"}:
                return

            yield ": heartbeat\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

No event replay or `Last-Event-ID` support in version 1. If the browser disconnects, the frontend can reconnect or fall back to polling `GET /import-jobs/{job_id}`.

### Minimal Frontend Test Page

Files:

- `frontend/src/app/import/page.tsx`
- optional `frontend/src/services/import.ts`

The browser cannot preselect `/Users/gabrieloliveira/Gabrr/gabrr-budget/backend/file_examples/rico-maio.pdf` for security reasons. The manual test step is: open the file picker and select that file.

Use `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000`.

```tsx
const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const form = new FormData();
form.append("file", file);

const response = await fetch(`${apiBaseUrl}/agents/process-file`, {
  method: "POST",
  headers: { "Idempotency-Key": crypto.randomUUID() },
  body: form,
});

if (!response.ok) {
  throw new Error(`Upload failed: ${response.status}`);
}

const job = await response.json();
const events = new EventSource(`${apiBaseUrl}${job.events_url}`);

events.addEventListener("progress", (event) => {
  const update = JSON.parse(event.data);
  setTimeline((items) => [...items, `${update.status} ${update.progress}% ${update.current_step ?? ""}`]);

  if (["done", "failed"].includes(update.status)) {
    events.close();
  }
});

events.onerror = () => {
  setTimeline((items) => [...items, "Event stream disconnected; checking status by polling."]);
  events.close();
  pollJobStatus(job.status_url);
};
```

## Agent And Subagent Work Strategy

Use the main agent as the integrator. Subagents should work on bounded areas with disjoint file ownership.

Parallel Round 1:

- Subagent A: import job schema and migration.
- Subagent B: import job repository, worker, and mapper.
- Subagent C: import job routes, Server-Sent Events, transaction draft filtering, and minimal frontend page.

Sequential Round 2:

1. Main agent integrates route changes in `POST /agents/process-file`.
2. Main agent checks that repository contracts match schemas.
3. Main agent runs migrations and backend tests.
4. Main agent runs the worker and frontend manual flow with `rico-maio.pdf`.

## Step-By-Step Implementation Order

1. Create migration for `import_jobs`.
2. Update `ImportJobSchema` and remove or loosen the old `import_id` dependency.
3. Add `ImportJobRepository`.
4. Add transaction filtering by `is_draft`, and add a way to accept selected transactions by setting `is_draft=false`.
5. Add `map_agent_result_to_transactions`.
6. Modify `POST /agents/process-file` to create jobs and return job URLs.
7. Add import job status and Server-Sent Events routes.
8. Add worker command.
9. Add minimal frontend timeline upload page.
10. Run backend tests.
11. Run manual end-to-end test with `/Users/gabrieloliveira/Gabrr/gabrr-budget/backend/file_examples/rico-maio.pdf`.

## Verification Plan

Backend tests:

- Upload creates one `import_jobs` row.
- Missing `Idempotency-Key` returns a clear validation response.
- Reusing same `Idempotency-Key` and same file returns same job.
- Reusing same `Idempotency-Key` with different file returns `409`.
- Concurrent duplicate upload creates one job because of the unique constraint.
- Worker atomically claims one job.
- Worker marks job `processing`.
- Worker unwraps `AgentService.run_json` and fails when `status != "success"`.
- Worker saves agent output on job.
- Worker maps valid `{ "transactions": [...] }` JSON to transactions with `is_draft=true`.
- Empty `transactions` marks job `done` with zero drafts.
- Invalid row marks job `failed`.
- Done jobs are not retried, preventing duplicate inserted transactions.
- Transaction listing can return draft rows when explicitly filtered by `is_draft=true`.
- Transaction accept behavior flips selected rows to `is_draft=false`.
- Ignored rows stay `is_draft=true`.
- Normal transaction listing excludes `is_draft=true` rows by default.
- Server-Sent Events stream emits progress, sends heartbeat comments, and ends on `done` or `failed`.
- CORS allows the frontend origin and `Idempotency-Key` header.

Frontend smoke:

- Upload button posts the selected PDF.
- Timeline receives progress events.
- Event stream closes on terminal status.
- Event stream error falls back to polling.
- Upload failure is visible in the timeline.

Manual end-to-end:

1. Start backend.
2. Run migrations.
3. Start worker with `uv run python -m app.workers.import_worker`.
4. Start frontend.
5. Open the import test page.
6. Select `/Users/gabrieloliveira/Gabrr/gabrr-budget/backend/file_examples/rico-maio.pdf`.
7. Upload.
8. Confirm the timeline shows progress.
9. Confirm `GET /transactions?is_draft=true` returns draft transactions with `currency="BRL"`.

## Three-Cycle Plan Review

### Cycle 1: Subagent Review Findings Applied

Fixed in this version:

- Added explicit API contracts and status codes.
- Added canonical status vocabulary and progress milestones.
- Added unique-constraint handling for idempotency races.
- Added file cleanup guidance when DB insert fails after file save.
- Added schema caveat for removing `import_id` and reverse `imports.jobs`.
- Removed the earlier `source_import_job_id` decision; transactions are not linked back to jobs in this version.
- Added worker transaction boundaries using `SessionLocal`.
- Added atomic job claiming requirement.
- Added handling for the `AgentService.run_json` `{ status, data }` envelope.
- Rewrote the Server-Sent Events sample so it does not depend on an undefined session.
- Added Server-Sent Events headers, heartbeat, disconnect handling, and fallback polling.
- Moved draft visibility and accept behavior to the normal transactions API.
- Added frontend `NEXT_PUBLIC_API_BASE_URL` and manual file-picker note for `rico-maio.pdf`.
- Added normal transaction-list visibility rule so ignored drafts do not leak into committed transaction views.

### Cycle 2: Remaining Contradictions Checked

Resolved or accepted:

- Job-scoped draft replacement is removed. Idempotency controls job creation, and `done` jobs are not retried because transactions are not linked back to jobs.
- Accepted rows are protected because accept/ignore now operates on normal transaction ids.
- The worker does not keep a database transaction open while the agent runs.
- The frontend test does not require auth headers on Server-Sent Events because browser `EventSource` cannot send custom headers.
- Hardcoded `BRL` is intentionally temporary and marked in the mapper.
- Cleanup requires adding `FileSystemService.delete_if_exists` or an equivalent helper because the current service only saves files.

### Cycle 3: Residual Risks Before Coding

Open risks to check during implementation:

- The actual database may contain existing `import_jobs` rows. The migration must inspect data before dropping or making columns non-null.
- SQLite and PostgreSQL differ in row-locking support. If the local database is SQLite, use a conditional update pattern instead of relying on `FOR UPDATE SKIP LOCKED`.
- The current ADK service may not expose enough error detail. Version 1 can store a generic failure message, but better diagnostics may need an `AgentService` change.
- If frontend and backend run on different origins, confirm CORS includes the frontend URL used during testing.
- If the worker process and API process do not share the same filesystem, `storage_path` will fail. Version 1 assumes they run on the same machine.
