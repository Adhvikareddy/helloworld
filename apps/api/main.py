from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.routes import verify, ledger, calibration, distribute, reveal, testbed

app = FastAPI(title="Q-SENTINEL API", version="9.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(distribute.router, prefix="/v1/qds", tags=["qds-distribute"])
app.include_router(reveal.router, prefix="/v1/qds", tags=["qds-reveal"])
app.include_router(verify.router, prefix="/v1/qds", tags=["qds-verify"])
app.include_router(testbed.router, prefix="/v1/testbed", tags=["testbed"])
app.include_router(ledger.router, prefix="/v1/ledger", tags=["ledger"])
app.include_router(calibration.router, prefix="/v1/calibration", tags=["calibration"])

@app.get("/v1/health")
def health_check():
    return {"status": "ok", "version": "v9.1"}

