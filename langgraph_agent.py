"""LangGraph multi-agent routing for a fictional telecom support portfolio.

kiarash torabi.n
27/10/2026


No LLM, embedding API, vector database, PostgreSQL connection, or outbound
WhatsApp sender is invoked. The rule-based router explicitly simulates the
classification step so reviewers can understand the orchestration.
"""

from typing import Annotated, Any, Literal, TypedDict
import operator
from langgraph.graph import END, START, StateGraph
Intent = Literal["greeting", "technical", "billing", "sales", "human"]

class CustomerContext(TypedDict):
    """Authenticated in a real system; supplied as synthetic demo input here."""
    customer_id: str
    display_name: str
    plan_name: str
    invoice_amount_brl: float
    marketing_opt_in: bool
    demo_verified: bool
    preferences: list[str]
    memory_summary: str

class OfferContext(TypedDict):
    offer_id: str
    title: str
    description: str
    segment: str

class AgentState(TypedDict, total=False):
    message: str
    mode: Literal["inbound", "campaign_preview"]
    customer: CustomerContext  #
    offers: list[OfferContext]  
    intent: Intent
    answer: str
    handoff: bool
    memory_update_preview: str  
    trace: Annotated[list[str], operator.add]  

def classify(state: AgentState) -> dict[str, Any]:
    """Deterministic stand-in for an LLM intent classifier."""
    if state.get("mode") == "campaign_preview":
        return {"intent": "sales", "trace": ["classify"]}

    text = state["message"].casefold()
    keywords: tuple[tuple[Intent, tuple[str, ...]], ...] = (
        ("human", ("humano", "atendente", "pessoa real")),
        ("billing", ("fatura", "boleto", "cobrança")),
        ("sales", ("oferta", "promoção", "promocao")),
        ("technical", ("internet", "wifi", "wi-fi", "sinal")),
        ("greeting", ("olá", "ola", "oi", "bom dia")),
    )
    for intent, terms in keywords:
        if any(term in text for term in terms):
            return {"intent": intent, "trace": ["classify"]}
    return {"intent": "human", "trace": ["classify"]} 

def route(state: AgentState) -> Intent:
    return state["intent"]

def greeting_agent(state: AgentState) -> dict[str, Any]:
    return {
        "answer": f"Olá, {state['customer']['display_name']}! Posso ajudar com internet, fatura ou planos?",
        "handoff": False,
        "trace": ["greeting"],
    }

def technical_agent(state: AgentState) -> dict[str, Any]:
    context = state["customer"]["memory_summary"]
    return {
        "answer": (
            "Vamos verificar sua conexão. O problema é no Wi-Fi ou em todos os aparelhos? "
            "Você já reiniciou o roteador? "
            f"Contexto anterior (simulado): {context}"
        ),
        "handoff": False,
        "trace": ["technical"],
    }


def billing_agent(state: AgentState) -> dict[str, Any]:
    customer = state["customer"]
    if not customer["demo_verified"]:
        return {
            "answer": "Para consultar valores, preciso de autenticação. Posso encaminhar ao atendimento humano (simulação).",
            "handoff": True,
            "trace": ["billing"],}
    amount = customer["invoice_amount_brl"]
    return {
        "answer": (f"Sua fatura fictícia é de R$ {amount:.2f} no plano {customer['plan_name']}. ""Não é uma cobrança real e nenhum boleto foi emitido."),
        "handoff": False,
        "trace": ["billing"],
    }

def sales_agent(state: AgentState) -> dict[str, Any]:
    customer = state["customer"]
    if state.get("mode") == "campaign_preview" and not customer["marketing_opt_in"]:
        return {"answer": "Sem envio: cliente não autorizou marketing.", "handoff": False, "trace": ["sales"]}
    matches = [
        offer for offer in state["offers"]
        if offer["segment"] in customer["preferences"]]
    if not matches:
        return {"answer": "Ainda não tenho uma oferta adequada ao seu perfil.", "handoff": False, "trace": ["sales"]}
    chosen = matches[0]
    return {
        "answer": ( f"Uma opção que combina com seu interesse é: {chosen['title']}. "f"{chosen['description']} Esta é apenas uma prévia, sem envio comercial."
        ),"handoff": False,
        "trace": ["sales"] }
def human_agent(state: AgentState) -> dict[str, Any]:
    return {
        "answer": "Posso encaminhar sua solicitação para um atendente. Nesta demonstração, nenhum chamado real é criado.",
        "handoff": True,
        "trace": ["human"]}
def review_response(state: AgentState) -> dict[str, Any]:
    """Minimal safety/quality gate; not a substitute for production validation."""
    answer = state.get("answer", "").strip()
    if not answer:
        answer = "Não consegui responder com segurança. Encaminhamento humano sugerido (simulação)."
        handoff = True
    else:
        handoff = state.get("handoff", False)
    memory_preview = f"Última intenção classificada: {state['intent']}."
    return {
        "answer": answer,
        "handoff": handoff,
        "memory_update_preview": memory_preview,
        "trace": ["review"],
    }

def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("classify", classify)
    builder.add_node("greeting", greeting_agent)
    builder.add_node("technical", technical_agent)
    builder.add_node("billing", billing_agent)
    builder.add_node("sales", sales_agent)
    builder.add_node("human", human_agent)
    builder.add_node("review", review_response)

    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify", route,
        {"greeting": "greeting", "technical": "technical", "billing": "billing",
         "sales": "sales", "human": "human"},
    )
    for node in ("greeting", "technical", "billing", "sales", "human"):
        builder.add_edge(node, "review")
    builder.add_edge("review", END)
    return builder.compile()

AGENT_GRAPH = build_graph()
