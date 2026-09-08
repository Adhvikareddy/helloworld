"""
Q-SENTINEL Judge Mode Dashboard.

Every button invokes the actual attacker scenario code and displays
real returned evidence.  No fake demo buttons.

Modes:
  LIVE EXPERIMENT  — executes a fresh verification/attack against the API
  RECORDED RESULT  — (future) displays a previously saved experiment result
"""
import streamlit as st
import requests
import os
import json

API_URL = os.getenv("QSENTINEL_API_URL", "http://qsentinel-api:8000")

st.set_page_config(page_title="Q-SENTINEL JUDGE MODE", layout="wide")

st.title("⚛️ Q-SENTINEL JUDGE MODE")
st.caption("SIH 2026 · PS26141 · Egreen Quanta · Blockchain & Cybersecurity")

# ── Calibration Status ─────────────────────────────────────────
try:
    cal_resp = requests.get(f"{API_URL}/v1/calibration/status", timeout=5)
    if cal_resp.status_code == 200:
        cal = cal_resp.json()
        cal_ver = cal.get("baseline_version", "unknown")
        thresholds = cal.get("thresholds", {})
        if "uncalibrated" in str(cal_ver):
            st.warning(f"⚠️ System is UNCALIBRATED — using fallback thresholds. "
                       f"Run `make calibrate` first.")
        else:
            st.success(f"✅ Calibrated: {cal_ver} | "
                       f"τ_low={thresholds.get('tau_low', '?')} | "
                       f"τ_high={thresholds.get('tau_high', '?')}")
except Exception:
    st.info("ℹ️ Could not reach API for calibration status.")

# ── Mode selector ──────────────────────────────────────────────
mode = st.radio("Experiment Mode", ["🔴 LIVE EXPERIMENT", "📁 RECORDED RESULT"],
                horizontal=True, index=0)

st.markdown("---")

# ── Pipeline visualisation ─────────────────────────────────────
st.markdown(
    "**Pipeline:** `REQUEST → L3 Security → L1 QDS → X/Y/Z Measurement "
    "→ L2 Statistics → Decision → L4 Evidence`"
)

# ── Helper: display structured result ──────────────────────────
def display_result(result: dict, attack_name: str):
    """Render an attack result with colour-coded decision and evidence."""
    decision = result.get("actual_outcome", result.get("decision", "UNKNOWN"))

    st.subheader(f"{attack_name}")
    if decision == "ACCEPT":
        st.success(f"Decision: {decision}")
    elif decision == "QUARANTINE":
        st.warning(f"Decision: {decision}")
    elif decision in ("REJECT", "integrity_violation"):
        st.error(f"Decision: {decision}")
    else:
        st.info(f"Outcome: {decision}")

    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Primary Layer", result.get("expected_primary_layer", "—"))
        st.metric("Event ID", result.get("event_id", "—"))
    with col_b:
        st.metric("Detected", "✅" if result.get("detected") else "❌")
        st.metric("Reason", result.get("reason", "—"))

    measurements = result.get("measurements", {})
    if measurements and any(v is not None for v in measurements.values()):
        st.markdown("**Measurement Evidence**")
        mcols = st.columns(4)
        mcols[0].metric("D (deviation)", f"{measurements.get('deviation_score', '—')}")
        mcols[1].metric("χ²", f"{measurements.get('chi_square', '—')}")
        mcols[2].metric("τ_low", f"{measurements.get('threshold_low', '—')}")
        mcols[3].metric("τ_high", f"{measurements.get('threshold_high', '—')}")

    with st.expander("Full JSON"):
        st.json(result)


def run_live_scenario(scenario_func, attack_name: str, **kwargs):
    """Execute a live attack scenario and display the results."""
    with st.spinner(f"Executing {attack_name}…"):
        try:
            results = scenario_func(**kwargs)
            if isinstance(results, list):
                for r in results:
                    display_result(r, attack_name)
            else:
                display_result(results, attack_name)
        except Exception as exc:
            st.error(f"Error: {exc}")


# ── Attack buttons ─────────────────────────────────────────────
st.subheader("Attack Controls")

if mode == "🔴 LIVE EXPERIMENT":
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✅ LEGITIMATE", use_container_width=True):
            from attacker.client import get_base_payload, send_verify
            from attacker.reporting import make_attack_result
            payload = get_base_payload(experiment_id="judge_legitimate")
            raw = send_verify(payload)
            resp = raw["response"]
            result = make_attack_result(
                attack_type="legitimate",
                target="/v1/qds/verify",
                expected_primary_layer="L1/L2",
                expected_outcome="ACCEPT",
                actual_outcome=resp.get("decision", "ERROR"),
                detected=False,
                event_id=resp.get("evidence_id"),
                reason=resp.get("reason"),
                measurements={
                    "deviation_score": resp.get("deviation_score"),
                    "chi_square": resp.get("chi_square"),
                    "threshold_low": resp.get("threshold_low"),
                    "threshold_high": resp.get("threshold_high"),
                },
            )
            display_result(result, "Legitimate Verification")

    with col2:
        if st.button("🔴 FORGERY", use_container_width=True):
            from attacker.scenarios.forgery import run_forgery_a
            run_live_scenario(run_forgery_a, "Forgery A (Invalid Signature)", count=1)

    with col3:
        if st.button("🔁 REPLAY", use_container_width=True):
            from attacker.scenarios.replay import run_replay
            run_live_scenario(run_replay, "Replay Attack", count=1)

    with col4:
        if st.button("🎭 IMPERSONATION", use_container_width=True):
            from attacker.scenarios.impersonation import run_impersonation
            run_live_scenario(run_impersonation, "Impersonation Attack", count=1)

    col5, col6, col7 = st.columns(3)

    with col5:
        if st.button("🚫 UNAUTHORIZED", use_container_width=True):
            from attacker.scenarios.unauthorized_verifier import run_unauthorized
            run_live_scenario(run_unauthorized, "Unauthorized Verification", count=1)

    with col6:
        if st.button("📡 CHANNEL", use_container_width=True):
            from attacker.scenarios.channel import run_channel
            run_live_scenario(run_channel, "Channel Manipulation",
                              levels=["low", "medium", "high"], repeats=1)

    with col7:
        if st.button("🔗 TAMPER LEDGER", use_container_width=True):
            from attacker.scenarios.ledger_tamper import run_ledger_tamper
            run_live_scenario(run_ledger_tamper, "Ledger Tampering")

    st.markdown("---")

    # Ledger chain verification
    if st.button("🔍 VERIFY FULL LEDGER CHAIN", use_container_width=True):
        from attacker.client import verify_chain
        chain = verify_chain()
        if chain.get("valid"):
            st.success(f"Chain intact — {chain.get('records_verified', '?')} records verified")
        elif chain.get("valid") is False:
            st.error(f"INTEGRITY VIOLATION: {chain.get('reason')}")
        else:
            st.warning(f"Could not verify: {chain.get('reason')}")

else:
    st.info("Recorded experiment mode is not yet implemented.  "
            "Use LIVE EXPERIMENT mode to run attacks in real time.")

# ── Footer ─────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Q-SENTINEL v8 · Qiskit-Aer simulator · No AI/ML · "
    "Tamper-evident hash-linked evidence (not decentralized blockchain)"
)
