import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || ''

// ─── Module-level State & Helpers ───────────────────────────────────────────

let _useMock = false
export function isMockMode() { return _useMock }

let calibrationCache = null

// Honest substitute for v9's chi-square: a real one-degree-of-freedom binomial
// goodness-of-fit statistic computed from v91's actual mismatch counts, not a
// fabricated placeholder.
function computeBinomialChiSquare(observedRate, n, expectedRate) {
  const observed = observedRate * n
  const expected = expectedRate * n
  const observedComplement = n - observed
  const expectedComplement = n - expected
  if (expected <= 0 || expectedComplement <= 0) return null
  return ((observed - expected) ** 2) / expected
       + ((observedComplement - expectedComplement) ** 2) / expectedComplement
}

// v9's PipelineTracker parses tokens like "L3_PASS" / "L1_FAIL" via s.split('_').
// v91's real pipeline_stages are free-text step names ("distribute",
// "mutate_quantum_keys", ...) that don't fit that vocabulary, so passing them
// through leaves every stage stuck on "pending". Derive the v9-style tokens from
// v91's actual findings instead.
//
// NOTE (architecture difference, not a bug): v91 has no standalone L1 probe —
// PQC envelope/identity validity is folded into the same IdentityGuard check as
// L3 in v91's real code. L1 here mirrors L3's outcome as the closest honest
// approximation, not an independently-measured result.
function deriveV9PipelineStages(findings = [], scenarioKey, actualOutcome) {
  const severityOf = (name) => findings.find(f => (f.detector_name || f.detector) === name)?.severity

  // 1. Layer 3: Security & Identity Guard
  // Probes: IdentityGuard, AuthorizationGuard, TimestampGuard, ReplayGuard, DoubleConsumptionGuard, SessionStore
  const l3Failed = ['IdentityGuard', 'AuthorizationGuard', 'TimestampGuard', 'ReplayGuard', 'DoubleConsumptionGuard', 'SessionStore']
    .some(name => severityOf(name) === 'REJECT') ||
    (actualOutcome === 'REJECT' && ['impersonation', 'replay', 'unauthorized'].includes(scenarioKey))

  const L3 = l3Failed ? 'L3_FAIL' : 'L3_PASS'

  // 2. Layer 1: Quantum Core / Envelope Delivery
  // If L3 failed, quantum transmission was aborted/skipped
  const L1 = l3Failed ? 'L1_SKIP' : 'L1_PASS'

  // 3. Layer 2: Statistical Detector & Pauli Tomography
  const quantSev = severityOf('QuantumDetector')
  const tomoSev = severityOf('ChannelTomography')
  const l2Failed = quantSev === 'REJECT' || (actualOutcome === 'REJECT' && ['forgery', 'channel', 'adaptive_x', 'transferability'].includes(scenarioKey) && !l3Failed)
  const l2Warn = quantSev === 'QUARANTINE' || tomoSev === 'QUARANTINE' || (actualOutcome === 'QUARANTINE')

  const L2 = l3Failed ? 'L2_SKIP'
    : l2Failed ? 'L2_FAIL'
    : l2Warn ? 'L2_WARN'
    : 'L2_PASS'

  // 4. Layer 4: Evidence Ledger Hash-Chain Integrity
  const ledgerFailed = (scenarioKey === 'ledger' || scenarioKey === 'ledger_tamper') && (
    findings.some(f => (f.detector_name || f.detector) === 'HashChainVerifier' && f.severity === 'REJECT') ||
    actualOutcome === 'INTEGRITY_VIOLATION'
  )
  const L4 = ledgerFailed ? 'L4_FAIL' : 'L4_PASS'

  return [L3, L1, L2, L4]
}

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
  timing_oracle: {
    decision: 'SECURE',
    reason: 'constant_time_effective',
    qds_valid: true,
    deviation_score: null,
    chi_square: null,
    shot_count: 0,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: null,
    latency_ms: 45.0,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 1.0, Y: 0.500, Z: 0.500 },
    layer_stopped: null,
    intercepted_by: 'Constant-Time Latency Guard',
    pipeline_stages: ['L3_PASS', 'L1_PASS', 'L2_PASS', 'L4_PASS'],
  },
  adaptive_x: {
    decision: 'REJECT',
    reason: 'coherent_x_rotation_detected',
    qds_valid: false,
    deviation_score: 0.1290,
    chi_square: 34.5,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-adaptivex-009',
    latency_ms: 125.0,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.720, Y: 0.510, Z: 0.380 },
    layer_stopped: 'L2',
    intercepted_by: 'Pauli Tomography (L2)',
    pipeline_stages: ['L3_PASS', 'L1_PASS', 'L2_FAIL', 'L4_PASS'],
  },
  transferability: {
    decision: 'REJECT',
    reason: 'cross_verifier_forgery_rejected',
    qds_valid: false,
    deviation_score: 0.2917,
    chi_square: 78.4,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-transfer-010',
    latency_ms: 198.0,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.650, Y: 0.440, Z: 0.560 },
    layer_stopped: 'L2',
    intercepted_by: 'Dual-Threshold Transferability Guard',
    pipeline_stages: ['L3_PASS', 'L1_PASS', 'L2_FAIL', 'L4_PASS'],
  },
  blind: {
    decision: 'REJECT',
    reason: 'blind_trial_threat_detected',
    qds_valid: false,
    deviation_score: 0.1850,
    chi_square: 52.0,
    shot_count: 512,
    threshold_low: 0.05,
    threshold_high: 0.15,
    evidence_id: 'evt-blind-011',
    latency_ms: 110.0,
    calibration_status: 'v9.1-calibrated',
    basis_probabilities: { X: 0.750, Y: 0.500, Z: 0.500 },
    layer_stopped: 'L3',
    intercepted_by: 'Autonomous Ground-Truth Engine',
    pipeline_stages: ['L3_FAIL', 'L1_SKIP', 'L2_SKIP', 'L4_PASS'],
  },
}

// Stable deterministic fallback events (most recent on top)
const STABLE_FALLBACK_LEDGER = [
  {
    event_id: 'evt-anchor-002',
    seq_num: 2,
    timestamp: Date.now() - 900000,
    signer_id: 'alice@qnet',
    verifier_id: 'verifier-alpha',
    decision: 'QUARANTINE',
    reason: 'statistical_deviation',
    previous_hash: '3d4952633cec04caebb47307bc4b8794ff288b8d3b91cd59d41de98d561299fc',
    current_hash: '86c1afff97e37b4de9eb1c9d855c8f2cf0644fd588d8fe26b52140204f0f8740',
  },
  {
    event_id: 'evt-anchor-001',
    seq_num: 1,
    timestamp: Date.now() - 1800000,
    signer_id: 'alice@qnet',
    verifier_id: 'verifier-alpha',
    decision: 'ACCEPT',
    reason: 'within_baseline',
    previous_hash: 'd06184597e8d6068f739ad4ce72cb476030ff5447fe356bc8c0c9556f3e24af2',
    current_hash: '3d4952633cec04caebb47307bc4b8794ff288b8d3b91cd59d41de98d561299fc',
  },
  {
    event_id: 'evt-genesis-000',
    seq_num: 0,
    timestamp: Date.now() - 3600000,
    signer_id: 'system',
    verifier_id: 'system',
    decision: 'INFO',
    reason: 'genesis_block',
    previous_hash: '0'.repeat(64),
    current_hash: 'd06184597e8d6068f739ad4ce72cb476030ff5447fe356bc8c0c9556f3e24af2',
  },
]

// ─── API Client ──────────────────────────────────────────────────────────────

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
    // Map scenarioKey -> v91 scenario path segment and request body
    let segment = scenarioKey
    let body = {}

    if (scenarioKey === 'channel') {
      body = { disturbance: payload?.disturbance_prob ?? +(Math.random() * (0.42 - 0.18) + 0.18).toFixed(2) }
    } else if (scenarioKey === 'ledger') {
      segment = 'ledger_tamper'
    }

    const raw = await axios.post(`${BASE_URL}/v1/testbed/attack/${segment}`, body, { timeout: 30000 })
    const d = raw.data
    const findings = d.findings || []
    const find = (name) => findings.find(f => (f.detector_name || f.detector) === name)
    const quantFinding = find('QuantumDetector')
    const tomoFinding  = find('ChannelTomography')

    const mismatch = quantFinding?.metrics?.mismatch_rate ?? (scenarioKey === 'legitimate' ? 0.0 : null)
    const n         = quantFinding?.metrics?.matched_subset_size ?? 32
    const tauLow    = quantFinding?.metrics?.tau_low  ?? calibrationCache?.thresholds?.tau_low  ?? 0.0101
    const tauHigh   = quantFinding?.metrics?.tau_high ?? calibrationCache?.thresholds?.tau_high ?? 0.0259
    const basisRates = tomoFinding?.metrics?.basis_rates ?? null

    const stages = deriveV9PipelineStages(findings, scenarioKey, d.actual_outcome)

    // Compute empirical Pauli probabilities
    let basisProbs = null
    if (basisRates) {
      const getRate = (r) => (typeof r === 'number' ? r : (r?.rate ?? 0.0))
      basisProbs = {
        X: Math.max(0.0, Math.min(1.0, 1.0 - getRate(basisRates.X))),
        Y: +(0.50 + ((getRate(basisRates.Y) - 0.1) * 0.5)).toFixed(3),
        Z: +(0.50 + ((getRate(basisRates.Z) - 0.1) * 0.5)).toFixed(3),
        outcomes: basisRates,
      }
    } else if (scenarioKey === 'legitimate') {
      basisProbs = { X: 1.0, Y: 0.50, Z: 0.50 }
    }

    const primaryRejectedDetector = findings.find(f => f.severity === 'REJECT')?.detector_name
      ?? findings.find(f => f.severity === 'REJECT')?.detector
      ?? null

    let layerStopped = null
    if (stages[0] === 'L3_FAIL') layerStopped = 'L3'
    else if (stages[2] === 'L2_FAIL' || stages[2] === 'L2_WARN') layerStopped = 'L2'
    else if (stages[3] === 'L4_FAIL') layerStopped = 'L4'

    _useMock = false
    return {
      decision: d.actual_outcome,
      reason: d.reason,
      qds_valid: d.attack_type === 'legitimate' ? true : d.actual_outcome !== 'ACCEPT' ? false : true,
      deviation_score: mismatch,
      chi_square: (mismatch !== null && n) ? computeBinomialChiSquare(mismatch, n, tauLow) : null,
      shot_count: n,
      threshold_low: tauLow,
      threshold_high: tauHigh,
      evidence_id: d.event_id,
      latency_ms: d.latency_ms,
      calibration_status: calibrationCache?.baseline_version ?? 'v9.1-calibrated',
      basis_probabilities: basisProbs,
      layer_stopped: layerStopped,
      intercepted_by: primaryRejectedDetector || (layerStopped ? `Layer ${layerStopped}` : null),
      pipeline_stages: stages,
      findings,
      trial_parameters: d.parameters,
      _mock: false,
    }
  } catch (err) {
    // If testbed attack endpoint not reachable, attempt direct verify or fallback to mock
    try {
      const res = await axios.post(`${BASE_URL}/v1/qds/verify`, payload, { timeout: 10000 })
      _useMock = false
      return { ...res.data, _mock: false }
    } catch {
      _useMock = true
      await new Promise(r => setTimeout(r, 200))
      const base = MOCK_SCENARIOS[scenarioKey] || MOCK_SCENARIOS.legitimate
      return {
        ...base,
        pipeline_stages: deriveV9PipelineStages([], scenarioKey, base.decision),
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

    const result = {
      baseline_version: data.baseline_version || 'v9.1-calibrated',
      policy_version: data.policy_version || 'cal-v9-initial',
      thresholds,
      baseline: data.baseline || MOCK_BASELINE,
    }
    calibrationCache = result
    return result
  } catch {
    const fallback = {
      baseline_version: 'v9.1-calibrated',
      policy_version: 'cal-v9-initial',
      thresholds: { tau_low: 0.05, tau_high: 0.15 },
      baseline: MOCK_BASELINE,
    }
    calibrationCache = fallback
    return fallback
  }
}

export async function getLedgerEvents() {
  try {
    const res = await axios.get(`${BASE_URL}/v1/ledger/events?limit=50`, { timeout: 5000 })
    const rawEvents = Array.isArray(res.data) ? res.data : (res.data?.events || [])
    if (Array.isArray(rawEvents) && rawEvents.length > 0) {
      const mapped = rawEvents.map(evt => {
        const rawTs = evt.timestamp
        const ts = rawTs ? (rawTs < 1e11 ? rawTs * 1000 : rawTs) : Date.now()
        return {
          ...evt,
          timestamp: ts,
          reason: evt.reason || (evt.decision === 'ACCEPT' ? 'within_baseline' : 'threat_detected'),
        }
      })
      // Ensure the MOST RECENT event is at index 0 (descending by seq_num or timestamp)
      return mapped.sort((a, b) => {
        const seqA = a.seq_num != null ? Number(a.seq_num) : null
        const seqB = b.seq_num != null ? Number(b.seq_num) : null
        if (seqA !== null && seqB !== null) return seqB - seqA
        const tA = typeof a.timestamp === 'number' ? a.timestamp : 0
        const tB = typeof b.timestamp === 'number' ? b.timestamp : 0
        return tB - tA
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
      valid: data.chain_valid,
      chain_valid: data.chain_valid,
      events_checked: data.total_records ?? null,
      broken_at: data.broken_at ?? null,
      _mock: false,
    }
  } catch {
    return { valid: true, chain_valid: true, events_checked: 10, broken_at: null, _mock: true }
  }
}
