# Integration verification

Verified locally on 2026-10-28 with Python 3.13.1 on Windows.

## Findings and fixes

- The inspected GitHub graph.py could not compile because an author/date line
  was bare Python text. Removed it; the FastAPI application now imports.
- langgraph_agent.py still existed as a one-byte empty placeholder. Removed it;
  graph.py is the sole workflow implementation.
- Added word-boundary matching to avoid routing contato as billing via conta.
  Added Portuguese support, cancellation, human handoff and sales phrases.
  Accents, case and repeated whitespace are handled; mixed requests prioritize
  support, then billing, then sales. Classification remains a keyword demo.
- Offers now require explicit True consent before any catalogue cache access.
  Missing/malformed consent fails closed. Consent is neither captured nor
  persisted by the endpoint; refusal does not block requested billing/support.
- Corrected the HLD edge label offers to the actual intent offer.
- Added reproducible integration tests, test dependencies and CI. main.py and
  postgres.py required no behavior changes after checking their contracts.

## Executed checks

- python -m unittest discover -s tests -v: **19 tests passed**.
- Real in-process HTTP requests through FastAPI validation, response serialization
  and compiled LangGraph: technical support, billing for all three profiles,
  sales by interest, human handoff, cancellation, FAQ and mixed-intent priority.
- Consent: refusal never invokes catalogue access, consent is rechecked after
  cache hits, malformed/missing consent is refused, nonmarketing help still works.
- Invalid/missing/whitespace/oversized/non-string messages return HTTP 422 before
  the customer loader runs. Health and the real random-loader HTTP flow pass.
- Independent profile copies, no cross-request handoff state, empty-interest
  fallback, cache version separation and the 32-entry cache bound pass.
- Mocked Psycopg connection: parameterized ID (including SQL-like input), Decimal
  formatting, unknown ID returning None, timeout and adapter-to-graph billing pass.
  These checks do not establish actual PostgreSQL connectivity or execute DDL.
- HLD XML: unique cell IDs, valid edge references, route names and optional/future
  dashed boxes verified. Diagram appearance was not visually reviewed.
- Python compilation passed. pip check: no broken requirements found.

## Runtime versions used

| Package | Version |
| --- | --- |
| langgraph | 1.0.6 |
| fastapi | 0.128.0 |
| pydantic | 2.12.5 |
| psycopg / psycopg-binary | 3.3.4 |
| uvicorn | 0.38.0 |
| httpx | 0.28.1 |
| starlette | 0.50.0 |
| anyio | 4.11.0 |

Dependencies were already installed locally; a clean dependency installation and
other version combinations were not locally tested. CI is configured to test
fresh installs on Python 3.11/3.13; its results must be checked separately.

## Limitations and blockers

- Live SQL integration was unavailable: DATABASE_URL was unset and the Docker
  engine was not running. No real database schema or rows were changed.
- Windows asyncio's loopback socket-pair initialization hung inside the sandbox.
  The hung test process was stopped, and the same integration command passed
  outside that sandbox after automatic approval.
- No live TCP/Uvicorn listener, deployment, real customer data, LLM provider,
  WhatsApp delivery or real human-agent transfer was exercised. Handoff remains
  a response flag and queue name.
