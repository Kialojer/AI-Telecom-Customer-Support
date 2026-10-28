"""FastAPI demo ingress. It does not send WhatsApp messages or run a server."""
#kiarash
from fastapi import FastAPI
from pydantic import BaseModel, Field
from graph import respond
from postgres import get_random_customer
app = FastAPI(title="Telecom Agentic Portfolio", version="1.0.0")
class DemoMessage(BaseModel):
    message: str = Field(min_length=1, max_length=2000, pattern=r"\S")
class DemoReply(BaseModel):
    demo: bool = True
    customer_id: str
    intent: str
    reply: str
    handoff: bool
    queue: str

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": "synthetic-demo"}

@app.post("/webhook/demo", response_model=DemoReply)
def demo_webhook(payload: DemoMessage) -> DemoReply:
    customer = get_random_customer()
    result = respond(customer, payload.message)
    return DemoReply(customer_id=customer["id"], intent=result["intent"], reply=result["reply"],handoff=result["handoff"], queue=result["queue"])
