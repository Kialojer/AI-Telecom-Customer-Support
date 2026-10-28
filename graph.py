"""Small LangGraph portfolio workflow. No database or external API access here."""

kiarash torabi.n
27/10/2026

from functools import lru_cache
from typing import Literal, TypedDict
from unicodedata import combining, normalize
from langgraph.graph import END, START, StateGraph
class Customer(TypedDict):
    id: str
    name: str
    plan: str
    interests: list[str]
    marketing_opt_in: bool
    invoice_total: str

class AgentState(TypedDict, total=False):
    customer: Customer
    message: str
    intent: Literal["support", "billing", "offer", "faq"]
    reply: str
    handoff: bool
    queue: str | None

def classify(state: AgentState) -> dict:
    text = normalize("NFKD", state["message"].casefold())
    text = "".join(char for char in text if not combining(char))
    if any(word in text for word in ("lenta", "lento", "sem internet", "tecnico", "atendente", "cancelar")):
        intent = "support"
    elif any(word in text for word in ("fatura", "boleto", "conta", "pagamento")):
        intent = "billing"
    elif any(word in text for word in ("oferta", "desconto", "promocao", "plano novo")):
        intent = "offer"
    else:intent = "faq"
    return {"intent": intent}

def support(state: AgentState) -> dict:
    return {
        "reply": f"{state['customer']['name']}, vou encaminhar seu pedido ao atendimento especializado (simulacao).",
        "handoff": True,
        "queue": "customer_service",
    }
def billing(state: AgentState) -> dict:
    customer = state["customer"]
    return {"reply": f"{customer['name']}, sua fatura ficticia e de R$ {customer['invoice_total']}. Nenhuma cobranca real foi consultada."}

CATALOGUE_VERSION = "demo-v1"
OFFERS = (
    ("streaming", "Oferta ficticia: pacote de streaming por R$ 19,90/mes."),
    ("internet", "Oferta ficticia: upgrade de internet por R$ 29,90/mes."),
)

@lru_cache(maxsize=32)
def cached_offer(interests: tuple[str, ...], catalogue_version: str) -> str:
    """Cache non-personal catalogue content only; change version on updates."""
    for category, description in OFFERS:
        if category in interests:
            return description
    return "Nao encontrei uma oferta ficticia adequada aos seus interesses."

def offer(state: AgentState) -> dict:
    customer = state["customer"]
    if not customer["marketing_opt_in"]:
        return {"reply": "Seu perfil nao autoriza ofertas. Posso ajudar com seu plano ou atendimento."}
    return {"reply": cached_offer(tuple(sorted(customer["interests"])), CATALOGUE_VERSION)}

def faq(state: AgentState) -> dict:
    return {"reply": f"Oi, {state['customer']['name']}! Seu plano ficticio e {state['customer']['plan']}. Posso ajudar com fatura, ofertas ou atendimento."}

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("classify", classify)
    for name, handler in (("support", support), ("billing", billing), ("offer", offer), ("faq", faq)):
        builder.add_node(name, handler)
        builder.add_edge(name, END)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges("classify", lambda state: state["intent"],
    {name: name for name in ("support", "billing", "offer", "faq")})
    return builder.compile()

graph = build_graph()

def respond(customer: Customer, message: str) -> AgentState:
    """Receive an already loaded customer snapshot; the graph never queries SQL."""
    return graph.invoke({"customer": customer, "message": message, "handoff": False, "queue": None})
