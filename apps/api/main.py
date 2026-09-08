from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.routes import verify, ledger, calibration

app = FastAPI(title="Q-SENTINEL API", version="9.0.0")

# CORS — allow dashboard and RDP browser to access the API
# allow_credentials=True cannot be used with allow_origins=["*"] in modern browsers/FastAPI.
# We explicitly list origins or set allow_credentials=False for the public API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(verify.router, prefix="/v1/qds", tags=["qds"])
app.include_router(ledger.router, prefix="/v1/ledger", tags=["ledger"])
app.include_router(calibration.router, prefix="/v1/calibration", tags=["calibration"])

@app.get("/v1/health")
def health_check():
    return {"status": "ok", "version": "v9"}
