from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any
import numpy as np
from sklearn.metrics import cohen_kappa_score

app = FastAPI(
    title="Agent Evaluation & Governance Suite",
    description="Benchmarking and evaluation framework for autonomous AI agent systems",
    version="1.0.0"
)

# --- Schemas ---
class AgentOutputEvaluation(BaseModel):
    code_correctness: float = Field(..., ge=0.0, le=1.0)
    logical_reasoning: float = Field(..., ge=0.0, le=1.0)
    guideline_compliance: float = Field(..., ge=0.0, le=1.0)
    structural_integrity: float = Field(..., ge=0.0, le=1.0)

class EvaluationRequest(BaseModel):
    agent_id: str
    prompt: str
    response_text: str
    scores: AgentOutputEvaluation

class EvaluationResponse(BaseModel):
    agent_id: str
    composite_score: float
    passed_guardrails: bool
    status: str

class IAACalculationRequest(BaseModel):
    annotator_a_scores: List[int]
    annotator_b_scores: List[int]

# --- Endpoints ---
@app.get("/health")
async def health_check():
    return {"status": "active", "system": "Agent Governance Suite"}

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_agent_output(payload: EvaluationRequest):
    # Multi-axis weighted scoring
    weights = [0.35, 0.25, 0.20, 0.20]
    raw_scores = [
        payload.scores.code_correctness,
        payload.scores.logical_reasoning,
        payload.scores.guideline_compliance,
        payload.scores.structural_integrity
    ]
    composite_score = float(np.dot(raw_scores, weights))
    
    # Runtime Guardrail check
    passed_guardrails = composite_score >= 0.75 and payload.scores.code_correctness >= 0.70
    
    return EvaluationResponse(
        agent_id=payload.agent_id,
        composite_score=round(composite_score, 4),
        passed_guardrails=passed_guardrails,
        status="APPROVED" if passed_guardrails else "REJECTED_HALLUCINATION_OR_FAIL"
    )

@app.post("/metrics/iaa")
async def calculate_inter_annotator_agreement(payload: IAACalculationRequest):
    if len(payload.annotator_a_scores) != len(payload.annotator_b_scores):
        raise HTTPException(status_code=400, detail="Annotator score arrays must be equal in length")
    
    try:
        kappa = cohen_kappa_score(payload.annotator_a_scores, payload.annotator_b_scores)
        return {
            "cohens_kappa": round(float(kappa), 4),
            "agreement_quality": "High" if kappa > 0.80 else "Moderate" if kappa > 0.60 else "Low"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
