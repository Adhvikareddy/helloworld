from fastapi import FastAPI
from apps.api.routes import verify, ledger, calibration

app = FastAPI(title="Q-SENTINEL API", version="1.0.0")

app.include_router(verify.router, prefix="/v1/qds", tags=["qds"])
app.include_router(ledger.router, prefix="/v1/ledger", tags=["ledger"])
app.include_router(calibration.router, prefix="/v1/calibration", tags=["calibration"])

@app.get("/v1/health")
def health_check():
    return {"status": "ok"}
