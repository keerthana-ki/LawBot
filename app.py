from fastapi import FastAPI
from pydantic import BaseModel
from model_utils import classify_case, get_similar_ipc_sections, generate_summary
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CaseRequest(BaseModel):
    description: str

class CaseResponse(BaseModel):
    predicted_case_type: str
    case_type_scores: dict
    ipc_sections: list
    case_summary: str

@app.post("/analyze/", response_model=CaseResponse)
def analyze_case(case: CaseRequest):
    label, scores = classify_case(case.description)
    ipc = get_similar_ipc_sections(case.description)
    summary = generate_summary(case.description)
    
    return {
        "predicted_case_type": label,
        "case_type_scores": scores,
        "ipc_sections": ipc,
        "case_summary": summary
    }