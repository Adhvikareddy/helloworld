from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.routes import verify, ledger, calibration, distribute, reveal, testbed
from contextlib import asynccontextmanager
import os
import json
import base64
from src.security.identity import global_pqc_identity

def load_identities():
    """Load test identities into the global PQC identity manager."""
    candidate_paths = [
        "attacker/credentials/public_registry.json",
        "/app/keys/public_registry.json",
        "keys/public_registry.json",
        "/app/attacker/credentials/public_registry.json"
    ]
    registry_path = next((p for p in candidate_paths if os.path.exists(p)), None)
    try:
        if registry_path:
            with open(registry_path, "r") as f:
                registry = json.load(f)
                
            for name, pk_b64 in registry.items():
                pk = base64.b64decode(pk_b64)
                is_verifier = (name in ["bob", "charlie", "auditor", "admin"])
                global_pqc_identity.register_participant(name, pk, is_verifier=is_verifier)
                
            # Register auditor and admin roles for tiering demonstration
            if "bob" in registry:
                bob_pk = base64.b64decode(registry["bob"])
                if "auditor" not in registry:
                    global_pqc_identity.register_participant("auditor", bob_pk, is_verifier=True)
                if "admin" not in registry:
                    global_pqc_identity.register_participant("admin", bob_pk, is_verifier=True)
        else:
            print(f"Warning: No public registry found in candidates: {candidate_paths}", flush=True)
    except Exception as e:
        print(f"Warning: Could not load identities from registry: {e}", flush=True)

# Auto-load on module initialization
load_identities()

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_identities()
    from src.detection.policy import global_policy
    if global_policy.get_version() == "uncalibrated" or not os.path.exists("data/calibration/thresholds.json"):
        print("[Startup] System uncalibrated. Running automatic Qiskit-Aer calibration...", flush=True)
        try:
            from src.calibration.grid_search import run_calibration as run_grid
            run_grid(baseline_runs=5, adversarial_runs=3, shots=256)
            from apps.api.routes.calibration import baseline_mgr, decision_policy
            baseline_mgr.load_baseline()
            decision_policy.load_thresholds()
            global_policy.load_thresholds()
            print(f"[Startup] Calibration complete: version={global_policy.get_version()}, thresholds={global_policy.get_thresholds()}", flush=True)
        except Exception as e:
            print(f"[Startup] Error during calibration: {e}. Falling back to analytical.", flush=True)
            global_policy.calibrate()
    yield
    # Cleanup

app = FastAPI(title="Q-SENTINEL API", version="9.1.0", lifespan=lifespan)

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

