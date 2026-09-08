import { useState } from 'react'
import {
  CheckCircle, XCircle, AlertTriangle, Play, Zap, User,
  RefreshCw, Shield, Radio, Database, Loader2
} from 'lucide-react'

const SCENARIOS = [
  {
    key: 'legitimate',
    label: 'Run Legitimate QDS',
    desc: 'Valid Bell-state teleportation & Pauli corrections',
    expectedDecision: 'ACCEPT',
    expectedLayer: '—',
    icon: Play,
    color: 'emerald',
    payload: {
      session_id: 'sess-judge-001',
      signer_id: 'alice@qnet:sess-judge-001',
      verifier_id: 'verifier-alpha',
      nonce: `nonce-${Date.now()}-legit`,
      measurement_bases: ['X', 'Y', 'Z'],
      shots: 1024,
      signature: 'valid-sig-abc123',
      message_digest: 'sha256-abc',
      timestamp: Date.now() / 1000,
      is_invalid_signature: false,
      disturbance_prob: 0.0,
    },
  },
  {
    key: 'forgery',
    label: 'Simulate Forgery Attack',
    desc: 'Mutated signature payload → caught by L1 QDS Validity',
    expectedDecision: 'REJECT',
    expectedLayer: 'L1 QDS Validity',
    icon: XCircle,
    color: 'red',
    payload: {
      session_id: 'sess-judge-002',
      signer_id: 'mallory@qnet:sess-judge-002',
      verifier_id: 'verifier-alpha',
      nonce: `nonce-${Date.now()}-forgery`,
      measurement_bases: ['X', 'Y', 'Z'],
      shots: 1024,
      signature: 'FORGED-invalid-sig',
      message_digest: 'sha256-forged',
      timestamp: Date.now() / 1000,
      is_invalid_signature: true,
      disturbance_prob: 0.0,
    },
  },
  {
    key: 'impersonation',
    label: 'Simulate Impersonation',
    desc: 'Unbound signer context → caught by L3 Security Guard',
    expectedDecision: 'REJECT',
    expectedLayer: 'L3 Security Guard',
    icon: User,
    color: 'red',
    payload: {
      session_id: 'sess-judge-003',
      signer_id: 'imposter@qnet:wrong-session',
      verifier_id: 'verifier-alpha',
      nonce: `nonce-${Date.now()}-impersonation`,
      measurement_bases: ['X', 'Y', 'Z'],
      shots: 1024,
      signature: 'sig-imposter',
      message_digest: 'sha256-imposter',
      timestamp: Date.now() / 1000,
      is_invalid_signature: false,
      disturbance_prob: 0.0,
    },
  },
  {
    key: 'replay',
    label: 'Simulate Replay Attack',
    desc: 'Duplicate nonce resubmission → caught by L3 Freshness Policy',
    expectedDecision: 'REJECT',
    expectedLayer: 'L3 Freshness Policy',
    icon: RefreshCw,
    color: 'red',
    payload: {
      session_id: 'sess-judge-004',
      signer_id: 'alice@qnet:sess-judge-004',
      verifier_id: 'verifier-alpha',
      nonce: 'REPLAYED-NONCE-FIXED',
      measurement_bases: ['X', 'Y', 'Z'],
      shots: 1024,
      signature: 'sig-replay',
      message_digest: 'sha256-replay',
      timestamp: Date.now() / 1000,
      is_invalid_signature: false,
      disturbance_prob: 0.0,
    },
  },
  {
    key: 'unauthorized',
    label: 'Simulate Unauthorized Verifier',
    desc: 'Forbidden verifier identity → caught by L3 Authorization',
    expectedDecision: 'REJECT',
    expectedLayer: 'L3 Authorization',
    icon: Shield,
    color: 'red',
    payload: {
      session_id: 'sess-judge-005',
      signer_id: 'alice@qnet:sess-judge-005',
      verifier_id: 'verifier-FORBIDDEN',
      nonce: `nonce-${Date.now()}-unauth`,
      measurement_bases: ['X', 'Y', 'Z'],
      shots: 1024,
      signature: 'sig-unauth',
      message_digest: 'sha256-unauth',
      timestamp: Date.now() / 1000,
      is_invalid_signature: false,
      disturbance_prob: 0.0,
    },
  },
  {
    key: 'channel',
    label: 'Simulate Channel Disturbance',
    desc: 'Bit/phase noise injection → caught by L2 Statistical Detector',
    expectedDecision: 'QUARANTINE',
    expectedLayer: 'L2 Statistical Detector',
    icon: Radio,
    color: 'amber',
    payload: {
      session_id: 'sess-judge-006',
      signer_id: 'alice@qnet:sess-judge-006',
      verifier_id: 'verifier-alpha',
      nonce: `nonce-${Date.now()}-channel`,
      measurement_bases: ['X', 'Y', 'Z'],
      shots: 1024,
      signature: 'sig-channel',
      message_digest: 'sha256-channel',
      timestamp: Date.now() / 1000,
      is_invalid_signature: false,
      disturbance_prob: 0.35,
    },
  },
  {
    key: 'ledger',
    label: 'Trigger Ledger Tampering',
    desc: 'Mutated historical event → caught by L4 Ledger Verification',
    expectedDecision: 'INTEGRITY ALARM',
    expectedLayer: 'L4 Evidence Ledger',
    icon: Database,
    color: 'purple',
    payload: null,
  },
]

const decisionStyle = {
  ACCEPT: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10',
  REJECT: 'text-rose-400 border-rose-500/40 bg-rose-500/10',
  QUARANTINE: 'text-amber-400 border-amber-500/40 bg-amber-500/10',
  'INTEGRITY ALARM': 'text-purple-400 border-purple-500/40 bg-purple-500/10',
}

const cardBorderGlow = {
  emerald: 'hover:border-emerald-500/40 hover:shadow-emerald-500/10',
  red: 'hover:border-rose-500/40 hover:shadow-rose-500/10',
  amber: 'hover:border-amber-500/40 hover:shadow-amber-500/10',
  purple: 'hover:border-purple-500/40 hover:shadow-purple-500/10',
}

const btnColorMap = {
  emerald: 'bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30',
  red: 'bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30',
  amber: 'bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30',
  purple: 'bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 border border-purple-500/30',
}

export default function AttackMatrix({ onRun, activeKey, lastResult }) {
  const [loadingKey, setLoadingKey] = useState(null)

  const handleRun = async (scenario) => {
    if (loadingKey) return
    setLoadingKey(scenario.key)
    await onRun(scenario)
    setLoadingKey(null)
  }

  return (
    <section className="px-6 pb-6">
      <div className="mb-4 flex items-center gap-3">
        <Zap size={18} className="text-cyan-400" />
        <h2 className="text-lg font-bold text-white">Judge Mode — Attack Matrix</h2>
        <span className="text-xs text-slate-500 font-mono">7 Mandatory Scenarios</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
        {SCENARIOS.map((scenario) => {
          const Icon = scenario.icon
          const isLoading = loadingKey === scenario.key
          const isActive = activeKey === scenario.key
          const result = isActive && lastResult ? lastResult : null

          return (
            <div
              key={scenario.key}
              className={`glass-card p-4 flex flex-col gap-3 transition-all duration-300 hover:shadow-2xl cursor-pointer
                ${cardBorderGlow[scenario.color]}
                ${isActive ? 'ring-1 ring-cyan-500/30' : ''}
              `}
            >
              {/* Icon + Label */}
              <div className="flex items-start gap-2">
                <div className={`p-1.5 rounded-lg bg-slate-800/80`}>
                  <Icon size={14} className={
                    scenario.color === 'emerald' ? 'text-emerald-400' :
                    scenario.color === 'red' ? 'text-rose-400' :
                    scenario.color === 'amber' ? 'text-amber-400' : 'text-purple-400'
                  } />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-xs font-bold leading-tight">{scenario.label}</p>
                  <p className="text-slate-500 text-xs mt-0.5 leading-snug">{scenario.desc}</p>
                </div>
              </div>

              {/* Expected outcome */}
              <div className="flex flex-wrap gap-1.5">
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${decisionStyle[scenario.expectedDecision]}`}>
                  {scenario.expectedDecision}
                </span>
                {scenario.expectedLayer !== '—' && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-mono text-slate-400 border border-slate-700/50 bg-slate-800/50">
                    {scenario.expectedLayer}
                  </span>
                )}
              </div>

              {/* Live result if this card was last run */}
              {result && (
                <div className={`text-xs px-2 py-1.5 rounded-lg font-mono border animate-fade-in ${decisionStyle[result.decision] || decisionStyle['REJECT']}`}>
                  ▶ {result.decision} · {result.latency_ms ? `${Math.round(result.latency_ms)}ms` : ''}
                  {result._mock && <span className="opacity-60 ml-1">[mock]</span>}
                </div>
              )}

              {/* Run button */}
              <button
                onClick={() => handleRun(scenario)}
                disabled={!!loadingKey}
                className={`btn-scenario text-xs font-semibold mt-auto ${btnColorMap[scenario.color]} disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                {isLoading ? (
                  <><Loader2 size={12} className="animate-spin" /> Running…</>
                ) : (
                  <><Play size={12} /> Run Scenario</>
                )}
              </button>
            </div>
          )
        })}
      </div>
    </section>
  )
}
