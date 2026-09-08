import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

// ─── Mock Data & Fallback Cache ───────────────────────────────────────────────

const MOCK_BASELINE = { X: 1.0, Y: 0.5, Z: 0.5 }

const MOCK_SCENARIOS = {
  legitimate: {
    decision: 'ACCEPT',
    reason: 'within_baseline',
    qds_valid: true,
    deviation_score: 0.0022,
    chi_square: 2.05,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-legit-001',
    latency_ms: 112.3,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 1.0, Y: 0.496, Z: 0.504 },
    layer_stopped: null,
    pipeline_stages: ['L3_PASS', 'L1_PASS', 'L2_PASS', 'L4_PASS'],
  },
  forgery: {
    decision: 'REJECT',
    reason: 'invalid_qds_signature',
    qds_valid: false,
    deviation_score: 0.1970,
    chi_square: 64.20,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-forgery-002',
    latency_ms: 98.7,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.688, Y: 0.523, Z: 0.518 },
    layer_stopped: 'L1',
    pipeline_stages: ['L3_PASS', 'L1_FAIL', 'L2_SKIP', 'L4_PASS'],
  },
  impersonation: {
    decision: 'REJECT',
    reason: 'invalid_identity_binding',
    qds_valid: false,
    deviation_score: 0.2840,
    chi_square: 88.50,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-impersonate-003',
    latency_ms: 12.1,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.584, Y: 0.512, Z: 0.520 },
    layer_stopped: 'L3',
    pipeline_stages: ['L3_FAIL', 'L1_SKIP', 'L2_SKIP', 'L4_PASS'],
  },
  replay: {
    decision: 'REJECT',
    reason: 'replay_detected',
    qds_valid: false,
    deviation_score: 0.3120,
    chi_square: 94.10,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-replay-004',
    latency_ms: 8.4,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.550, Y: 0.510, Z: 0.520 },
    layer_stopped: 'L3',
    pipeline_stages: ['L3_FAIL', 'L1_SKIP', 'L2_SKIP', 'L4_PASS'],
  },
  unauthorized: {
    decision: 'REJECT',
    reason: 'unauthorized_verifier',
    qds_valid: false,
    deviation_score: 0.3200,
    chi_square: 96.40,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-unauth-005',
    latency_ms: 9.2,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.560, Y: 0.515, Z: 0.525 },
    layer_stopped: 'L3',
    pipeline_stages: ['L3_FAIL', 'L1_SKIP', 'L2_SKIP', 'L4_PASS'],
  },
  channel: {
    decision: 'QUARANTINE',
    reason: 'statistical_deviation',
    qds_valid: true,
    deviation_score: 0.0861,
    chi_square: 18.7,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-channel-006',
    latency_ms: 178.9,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.797, Y: 0.541, Z: 0.510 },
    layer_stopped: 'L2',
    pipeline_stages: ['L3_PASS', 'L1_PASS', 'L2_WARN', 'L4_PASS'],
  },
  ledger: {
    decision: 'INTEGRITY_ALARM',
    reason: 'hash_chain_broken',
    qds_valid: null,
    deviation_score: 0.4500,
    chi_square: 112.0,
    shot_count: 0,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-ledger-007',
    latency_ms: 22.1,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.500, Y: 0.500, Z: 0.500 },
    layer_stopped: 'L4',
    pipeline_stages: ['L3_PASS', 'L1_PASS', 'L2_PASS', 'L4_FAIL'],
  },
}

// Stable deterministic fallback events (never randomly change on refresh)
const STABLE_FALLBACK_LEDGER = [
  {
    event_id: 'evt-genesis-000',
    timestamp: Date.now() - 3600000,
    signer_id: 'system',
    verifier_id: 'system',
    decision: 'INFO',
    reason: 'genesis_block',
    previous_hash: '0'.repeat(64),
    current_hash: 'd06184597e8d6068f739ad4ce72cb476030ff5447fe356bc8c0c9556f3e24af2',
  },
  {
    event_id: 'evt-anchor-001',
    timestamp: Date.now() - 1800000,
    signer_id: 'alice@qnet',
    verifier_id: 'verifier-alpha',
    decision: 'ACCEPT',
    reason: 'within_baseline',
    previous_hash: 'd06184597e8d6068f739ad4ce72cb476030ff5447fe356bc8c0c9556f3e24af2',
    current_hash: '3d4952633cec04caebb47307bc4b8794ff288b8d3b91cd59d41de98d561299fc',
  },
  {
    event_id: 'evt-anchor-002',
    timestamp: Date.now() - 900000,
    signer_id: 'alice@qnet',
    verifier_id: 'verifier-alpha',
    decision: 'QUARANTINE',
    reason: 'statistical_deviation',
    previous_hash: '3d4952633cec04caebb47307bc4b8794ff288b8d3b91cd59d41de98d561299fc',
    current_hash: '86c1afff97e37b4de9eb1c9d855c8f2cf0644fd588d8fe26b52140204f0f8740',
  }
]

// ─── API Client ──────────────────────────────────────────────────────────────

let _useMock = false
export function isMockMode() { return _useMock }

export async function checkHealth() {
  const t0 = performance.now()
  try {
    const res = await axios.get(`${BASE_URL}/v1/health`, { timeout: 3000 })
    const latency = Math.round(performance.now() - t0)
    _useMock = false
    return { online: true, latencyMs: latency, data: res.data }
  } catch {
    _useMock = true
    return { online: false, latencyMs: null, data: null }
  }
}

export async function runScenario(scenarioKey, payload = {}) {
  // Always attempt live execution first
  try {
    const res = await axios.post(`${BASE_URL}/v1/testbed/run-scenario`, {
      scenario: scenarioKey,
      payload
    }, { timeout: 15000 })
    
    _useMock = false
    return { ...res.data, _mock: false }
  } catch (err) {
    // If testbed endpoint not reachable, attempt direct verify or fallback to mock
    try {
      const res = await axios.post(`${BASE_URL}/v1/qds/verify`, payload, { timeout: 10000 })
      _useMock = false
      return { ...res.data, _mock: false }
    } catch {
      _useMock = true
      await new Promise(r => setTimeout(r, 300))
      const base = MOCK_SCENARIOS[scenarioKey] || MOCK_SCENARIOS.legitimate
      return {
        ...base,
        _mock: true,
      }
    }
  }
}

export async function getCalibrationStatus() {
  try {
    const res = await axios.get(`${BASE_URL}/v1/calibration/status`, { timeout: 5000 })
    const data = res.data
    
    // Normalize thresholds if returned as list [tau_low, tau_high] or object
    let thresholds = { tau_low: 0.05, tau_high: 0.15 }
    if (data.thresholds) {
      if (Array.isArray(data.thresholds)) {
        thresholds = { tau_low: data.thresholds[0], tau_high: data.thresholds[1] }
      } else if (typeof data.thresholds === 'object') {
        thresholds = {
          tau_low: data.thresholds.tau_low ?? 0.05,
          tau_high: data.thresholds.tau_high ?? 0.15,
        }
      }
    }

    return {
      baseline_version: data.baseline_version || 'v9.1-calibrated',
      policy_version: data.policy_version || 'cal-v9-initial',
      thresholds,
      baseline: data.baseline || MOCK_BASELINE,
    }
  } catch {
    return {
      baseline_version: 'v9.1-calibrated',
      policy_version: 'cal-v9-initial',
      thresholds: { tau_low: 0.05, tau_high: 0.15 },
      baseline: MOCK_BASELINE,
    }
  }
}

export async function getLedgerEvents() {
  try {
    const res = await axios.get(`${BASE_URL}/v1/ledger/events?limit=50`, { timeout: 5000 })
    const rawEvents = res.data?.events || []
    if (Array.isArray(rawEvents) && rawEvents.length > 0) {
      return rawEvents.map(evt => {
        const rawTs = evt.timestamp
        const ts = rawTs ? (rawTs < 1e11 ? rawTs * 1000 : rawTs) : Date.now()
        return {
          ...evt,
          timestamp: ts,
          reason: evt.reason || (evt.decision === 'ACCEPT' ? 'within_baseline' : 'threat_detected'),
        }
      })
    }
    return STABLE_FALLBACK_LEDGER
  } catch {
    return STABLE_FALLBACK_LEDGER
  }
}

export async function verifyLedgerChain() {
  try {
    const res = await axios.get(`${BASE_URL}/v1/ledger/verify-chain`, { timeout: 8000 })
    const data = res.data
    return {
      valid: data.valid ?? data.chain_valid ?? true,
      chain_valid: data.chain_valid ?? data.valid ?? true,
      events_checked: data.events_checked ?? 10,
      broken_at: data.broken_at ?? null,
      _mock: false
    }
  } catch {
    return { valid: true, chain_valid: true, events_checked: 10, broken_at: null, _mock: true }
  }
}
