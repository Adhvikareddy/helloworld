"""
Q-SENTINEL v9 Judge Mode Dashboard.

Every button invokes the actual attacker scenario code and displays
real returned evidence.  No fake demo buttons.

Modes:
  LIVE EXPERIMENT  — executes a fresh verification/attack against the API
  DETECTION MATRIX — displays the multi-vector matrix results
  FORGERY CURVE    — displays the forgery probability sweep
"""
import streamlit as st
import requests
import os
import json
import csv

API_URL = os.getenv("QSENTINEL_API_URL", "http://localhost:8000")

st.set_page_config(page_title="Q-SENTINEL v9 JUDGE MODE", layout="wide")

# ── CSS ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    .decision-accept { color: #00ff88; font-size: 24px; font-weight: bold; }
    .decision-reject { color: #ff4444; font-size: 24px; font-weight: bold; }
    .decision-quarantine { color: #ffaa00; font-size: 24px; font-weight: bold; }
    .metric-card {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚛️ Q-SENTINEL v9 JUDGE MODE")
st.caption("SIH 2026 · PS SIH26141 · Egreen Quanta · Blockchain & Cybersecurity")

# ── Calibration Status ─────────────────────────────────────────
try:
    cal_resp = requests.get(f"{API_URL}/v1/calibration/status", timeout=5)
    if cal_resp.status_code == 200:
        cal = cal_resp.json()
        cal_ver = cal.get("baseline_version", cal.get("version", "unknown"))
        thresholds = cal.get("thresholds", {})
        if "uncalibrated" in str(cal_ver):
            st.warning(f"⚠️ System is UNCALIBRATED — using fallback thresholds. "
                       f"Run `make calibrate` first.")
        else:
            st.success(f"✅ Calibrated: {cal_ver} | "
                       f"τ_low={thresholds.get('tau_low', '?')} | "
                       f"τ_high={thresholds.get('tau_high', '?')}")
except Exception:
    st.info("ℹ️ Could not reach API for calibration status. Is the server running?")

# ── Mode selector ──────────────────────────────────────────────
mode = st.radio("Experiment Mode", [
    "🔴 LIVE EXPERIMENT",
    "📊 DETECTION MATRIX", 
    "📈 FORGERY CURVE",
    "🛡️ OPTIMAL ADVERSARY"
], horizontal=True, index=0)

st.markdown("---")

# ── Pipeline visualisation ─────────────────────────────────────
st.markdown(
    "**Detection Pipeline:** `REQUEST → L3 Auth/Freshness → L1 QDS Teleportation → "
    "L2 Statistical Analysis → Correlation Engine → L4 Evidence Ledger`"
)

# ── Helper: display structured result ──────────────────────────
def display_result(result: dict, attack_name: str):
    """Render an attack result with colour-coded decision and evidence."""
    decision = result.get("decision", "UNKNOWN")

    st.subheader(f"{attack_name}")
    if decision == "ACCEPT":
        st.success(f"✅ Decision: {decision}")
    elif decision == "QUARANTINE":
        st.warning(f"⚠️ Decision: {decision}")
    elif decision == "REJECT":
        st.error(f"🚫 Decision: {decision}")
    else:
        st.info(f"ℹ️ Outcome: {decision}")

    # Display findings
    findings = result.get("findings", [])
    if findings:
        st.markdown("**Findings:**")
        for f in findings:
            severity = f.get("severity", "INFO")
            detector = f.get("detector", "Unknown")
            desc = f.get("description", "")
            
            if severity == "REJECT":
                st.markdown(f"- 🔴 **{detector}**: {desc}")
            elif severity == "QUARANTINE":
                st.markdown(f"- 🟡 **{detector}**: {desc}")
            else:
                st.markdown(f"- 🟢 **{detector}**: {desc}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Evidence ID", result.get("evidence_id", "—"))
    with col_b:
        st.metric("Latency", f"{result.get('latency_ms', 0):.1f} ms")
    with col_c:
        st.metric("Calibration", result.get("calibration_status", "—"))

    with st.expander("Full JSON"):
        st.json(result)


def send_verification(payload: dict, headers: dict = None) -> dict:
    """Send a verification request to the API."""
    try:
        resp = requests.post(
            f"{API_URL}/v1/qds/verify",
            json=payload,
            headers=headers or {},
            timeout=30
        )
        return resp.json()
    except Exception as e:
        return {"decision": "ERROR", "findings": [], "evidence_id": "—",
                "latency_ms": 0, "calibration_status": str(e)}


# ── LIVE EXPERIMENT ────────────────────────────────────────────
if mode == "🔴 LIVE EXPERIMENT":
    st.subheader("Attack Controls")
    
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ LEGITIMATE", use_container_width=True):
            import uuid, time
            from src.security.envelope import PQCEnvelope
            from src.keyvault import global_keyvault
            
            session = global_keyvault.create_session("alice", 300)
            payload = {
                "session_id": session.session_id,
                "signer_id": "alice",
                "verifier_id": "bob",
                "nonce": f"nonce-{uuid.uuid4()}",
                "timestamp": time.time(),
                "message_bit": 0,
                "measurement_bases": (["X", "Y", "Z"] * 101)[:300],
                "experiment_id": "judge_legitimate",
            }
            # Note: In a real scenario the signer would have a registered PK.
            # For this demo we use the API directly.
            result = send_verification(payload)
            display_result(result, "Legitimate Verification")

    with col2:
        if st.button("🔴 FORGERY", use_container_width=True):
            import uuid, time
            payload = {
                "session_id": f"session-{uuid.uuid4()}",
                "signer_id": "alice",
                "verifier_id": "bob",
                "nonce": f"nonce-{uuid.uuid4()}",
                "timestamp": time.time(),
                "message_bit": 0,
                "measurement_bases": (["X", "Y", "Z"] * 101)[:300],
                "experiment_id": "judge_forgery",
                "signature": "INVALID_SIGNATURE_DATA"
            }
            result = send_verification(payload)
            display_result(result, "Forgery A (Invalid Signature)")

    with col3:
        if st.button("🔁 REPLAY", use_container_width=True):
            import uuid, time
            nonce = f"replay-{uuid.uuid4()}"
            payload = {
                "session_id": f"session-{uuid.uuid4()}",
                "signer_id": "alice",
                "verifier_id": "bob",
                "nonce": nonce,
                "timestamp": time.time(),
                "message_bit": 0,
                "measurement_bases": (["X", "Y", "Z"] * 101)[:300],
                "experiment_id": "judge_replay",
                "signature": "sig_placeholder"
            }
            # Send once
            send_verification(payload)
            # Replay
            result = send_verification(payload)
            display_result(result, "Replay Attack")

    with col4:
        if st.button("📡 CHANNEL", use_container_width=True):
            import uuid, time
            payload = {
                "session_id": f"session-{uuid.uuid4()}",
                "signer_id": "alice",
                "verifier_id": "bob",
                "nonce": f"nonce-{uuid.uuid4()}",
                "timestamp": time.time(),
                "message_bit": 0,
                "measurement_bases": (["X", "Y", "Z"] * 101)[:300],
                "experiment_id": "judge_channel",
                "signature": "sig_placeholder"
            }
            headers = {"x-testbed-disturbance": "0.3"}
            result = send_verification(payload, headers=headers)
            display_result(result, "Channel Manipulation (d=0.3)")

    st.markdown("---")

    # Ledger chain verification
    if st.button("🔍 VERIFY FULL LEDGER CHAIN", use_container_width=True):
        try:
            resp = requests.get(f"{API_URL}/v1/ledger/verify-chain", timeout=10)
            chain = resp.json()
            if chain.get("chain_valid"):
                st.success("✅ Ledger chain integrity verified — no tampering detected.")
            else:
                st.error("🚫 INTEGRITY VIOLATION — ledger chain is broken!")
        except Exception as e:
            st.warning(f"Could not verify: {e}")

# ── DETECTION MATRIX ───────────────────────────────────────────
elif mode == "📊 DETECTION MATRIX":
    st.subheader("Multi-Vector Detection Matrix")
    
    matrix_path = "experiments/results/multi_vector_matrix.csv"
    if os.path.exists(matrix_path):
        import pandas as pd
        df = pd.read_csv(matrix_path)
        
        # Style the dataframe
        def color_cells(val):
            if val == "REJECT":
                return "background-color: #ff4444; color: white"
            elif val == "QUARANTINE":
                return "background-color: #ffaa00; color: black"
            elif val == "INFO":
                return "background-color: #00ff88; color: black"
            elif val == "ACCEPT":
                return "background-color: #00ff88; color: black"
            return ""
        
        styled = df.style.map(color_cells)
        st.dataframe(styled, use_container_width=True, height=400)
        
        st.markdown("---")
        st.markdown("**Legend:** 🔴 REJECT = attack detected | 🟡 QUARANTINE = suspicious | 🟢 INFO/ACCEPT = clean")
    else:
        st.warning("Matrix data not found. Run `python -m experiments.multi_vector_matrix` first.")
        if st.button("Generate Matrix Now"):
            with st.spinner("Running multi-vector matrix experiment..."):
                import subprocess
                subprocess.run(["python", "-m", "experiments.multi_vector_matrix"], 
                             capture_output=True, text=True)
                st.rerun()

# ── FORGERY CURVE ──────────────────────────────────────────────
elif mode == "📈 FORGERY CURVE":
    st.subheader("Forgery Probability vs Disturbance")
    
    curve_path = "experiments/results/forgery_curve.csv"
    if os.path.exists(curve_path):
        import pandas as pd
        df = pd.read_csv(curve_path)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Empirical Mismatch Rate vs Disturbance**")
            st.line_chart(df.set_index("disturbance")["avg_mismatch_rate"])
            
        with col2:
            st.markdown(f"**P_forge Bound (L={df['L'].iloc[0]})**")
            st.metric("P_forge at d=0", f"{df['p_forge_bound'].iloc[0]:.2e}")
            st.metric("Mismatch at d=0.25", 
                      f"{df[df['disturbance'] == 0.25]['avg_mismatch_rate'].iloc[0]:.4f}"
                      if 0.25 in df['disturbance'].values else "N/A")
        
        st.dataframe(df, use_container_width=True, height=400)
    else:
        st.warning("Forgery curve data not found. Run `python -m experiments.forgery_curve` first.")
        if st.button("Generate Forgery Curve Now"):
            with st.spinner("Running forgery curve experiment (this may take a few minutes)..."):
                import subprocess
                subprocess.run(["python", "-m", "experiments.forgery_curve"],
                             capture_output=True, text=True)
                st.rerun()

# ── OPTIMAL ADVERSARY ──────────────────────────────────────────
elif mode == "🛡️ OPTIMAL ADVERSARY":
    st.subheader("Optimal Adversary Bound (Differentiator D2)")
    
    oa_path = "experiments/results/optimal_adversary.csv"
    if os.path.exists(oa_path):
        import pandas as pd
        df = pd.read_csv(oa_path)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**P_forge vs Security Parameter L**")
            st.line_chart(df.set_index("L")["security_bits"])
            
        with col2:
            st.markdown("**Key Metrics**")
            st.metric("p_opt (optimal adversary)", "0.7887")
            st.metric("Per-element error rate", "0.2113")
            
            l300 = df[df["L"] == 300]
            if not l300.empty:
                st.metric("P_forge at L=300", f"{l300['p_forge'].iloc[0]:.2e}")
                st.metric("Security bits at L=300", f"{l300['security_bits'].iloc[0]:.1f}")
        
        st.markdown("---")
        st.markdown("**Full Forgery Probability Table**")
        st.dataframe(df, use_container_width=True, height=400)
        
        st.markdown("---")
        st.markdown(
            "**Interpretation:** The optimal adversary for the six-state QDS ensemble "
            "can discriminate each key element with probability p ~ 0.7887. "
            "Over the matched subset of size n = L/3, the forger needs enough correct "
            "guesses to pass the acceptance threshold s_a. The forgery probability "
            "decays *exponentially* in L, giving quantifiable security guarantees."
        )
    else:
        st.warning("Optimal adversary data not found. Run `python -m experiments.optimal_adversary_experiment` first.")
        if st.button("Generate Optimal Adversary Analysis"):
            with st.spinner("Running optimal adversary experiment..."):
                import subprocess
                subprocess.run(["python", "-m", "experiments.optimal_adversary_experiment"],
                             capture_output=True, text=True)
                st.rerun()

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Q-SENTINEL v9 · Qiskit-Aer simulator · Six-state QDS + ML-DSA-65 PQC · "
    "HMAC-SHA256 tamper-evident hash-chain evidence · Channel Tomography (D1) · "
    "Optimal Adversary Bound (D2) · No AI/ML"
)
