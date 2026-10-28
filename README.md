# Telecom Agentic Portfolio

An independent educational portfolio concept inspired by customer service in
Brazilian telecommunications. Not affiliated with Claro or Vivo. All customers,
plans, prices and bills are fictional. No credentials or personal phone numbers
are included. Designed for GitHub and a CV; deployment is not required.

## Files

| File | Purpose |
| --- | --- |
| `architecture.drawio` | Editable diagrams.net high-level design (uncompressed XML) |
| `graph.py` | LangGraph classification and FAQ, billing, offer and support paths |
| `postgres.py` | Random synthetic customer snapshots, reference DDL, optional SQL lookup |
| `main.py` | FastAPI demo ingress and typed JSON response |
| `requirements.txt` | Dependency ranges; not a resolved lockfile |
| `VERIFICATION.md` | Scope and results of static verification |

## Architecture and scope

1. The demo receives a message through `POST /webhook/demo`.
2. `get_random_customer()` selects one of three fictional profiles.
3. FastAPI passes that snapshot to the compiled LangGraph workflow.
4. A small Portuguese keyword classifier routes to FAQ, billing, offers or support.
5. The graph returns a reply and optional simulated handoff queue as JSON.

There are no database calls inside graph nodes. The optional PostgreSQL adapter
uses a parameterized lookup and is separate from the default synthetic flow.
The DDL is embedded in `postgres.py`; nothing creates tables automatically.

The offer path checks marketing consent and uses a bounded application cache of
preloaded catalogue text keyed by interests and catalogue version. It illustrates
a CAG-inspired context reuse boundary. There is no LLM call, token accounting,
provider prompt/KV cache, embedding, vector database or persistent chat memory.
Consequently this demo does not claim measured token savings or generative AI.
Changing `CATALOGUE_VERSION` invalidates prior cache keys; restart also clears it.

Each request selects a new random profile. There is no conversation identity or
cross-request history. Support handoff is a response flag, not a real ticket or
agent transfer. Billing only reads the supplied fictional snapshot.

## Open the editable HLD

Visit https://app.diagrams.net/ and choose **File > Open From > Device**, then
select `architecture.drawio`. Shapes, labels and connectors are editable.
Solid arrows represent implemented demo paths. Dashed boxes/arrows describe
optional or future integrations, including WhatsApp and PostgreSQL.

## Review without running

Open the diagram and three Python files in GitHub or an editor. The delivered
project has not been launched, deployed or connected to an external service.
Static checks are described in `VERIFICATION.md`.

## Optional local demonstration (only if you later choose to run it)

Use Python 3.11+ in a virtual environment. From this folder:

```sh
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs and send this body to `POST /webhook/demo`:

```json
{"message": "Minha internet esta lenta, preciso de um atendente"}
```

Expected route: `support`, `handoff: true`, `queue: "customer_service"`.
Try `Quero ver minha fatura` for billing, `Tem alguma oferta?` for an offer
(or consent refusal), and `Ola` for the FAQ introduction.

The dependency ranges express intended compatibility, not tested runtime
versions. No dependencies were installed and no live runtime was tested during
delivery verification.

## Optional PostgreSQL integration

If implemented later, create `portfolio_customers` using `SCHEMA_SQL`, insert
synthetic rows, set `DATABASE_URL` privately, and call
`load_customer_from_postgres(customer_id)` before `respond(...)`. An unknown ID
returns `None`, which the caller must handle. Never commit connection strings.
The adapter is not exposed through the HTTP demo endpoint.

## Future WhatsApp integration

The JSON demo endpoint is not a Meta WhatsApp Cloud API webhook. An adapter
would need actual payload parsing, verification challenge handling, signature
validation, authenticated customer resolution, event deduplication and a send
API implementation. Keep those responsibilities outside the graph. Real billing
requires verified identity and authorization; the random-profile demo must
remain restricted to fictional data.

## Design references

- LangGraph graph API: https://reference.langchain.com/python/langgraph/graph
- FastAPI request bodies: https://fastapi.tiangolo.com/tutorial/body/
- Psycopg usage: https://www.psycopg.org/psycopg3/docs/basic/usage.html
- Psycopg dictionary rows: https://www.psycopg.org/psycopg3/docs/advanced/rows.html

## CV wording (Portuguese)

Prototipo de portfolio de atendimento para telecomunicacoes com LangGraph,
FastAPI e adaptador PostgreSQL: roteamento por intencao, contexto de cliente
simulado, cache de ofertas e encaminhamento simulado para atendimento humano.
