import { useState } from 'react'
import {
  Play, Zap, User, RefreshCw, Shield, Radio, Database,
  Loader2, Shuffle
} from 'lucide-react'

const SCENARIOS = [
  {
    key: 'legitimate',
    label: 'Legitimate Teleportation',
    desc: 'Pure Bell-state teleportation & calibrated Pauli correction channel',
    targetLayer: 'L1/L2 End-to-End Baseline',
    vectorType: 'Reference Quantum Signature',
    icon: Play,
    payload: {
      session_id: 'sess-legit',
      signer_id: 'alice@qnet',
      verifier_id: 'verifier-alpha',
      disturbance_prob: 0.0,
      shots: 512,
    },
  },
  {
    key: 'channel',
    label: 'Channel Noise Injection',
    desc: 'Stochastic Pauli transverse & depolarizing perturbations along quantum link',
    targetLayer: 'L2 Pauli Tomography',
    vectorType: 'Stochastic Channel Noise',
    icon: Radio,
    payload: {
      session_id: 'sess-channel',
      signer_id: 'alice@qnet',
      verifier_id: 'verifier-alpha',
      shots: 512,
    },
  },
  {
    key: 'forgery',
    label: 'Signature Bit Mutation',
    desc: 'Dynamic random key element alteration attempting state forgery',
    targetLayer: 'L1 Quantum Digital Signature',
    vectorType: 'Cryptographic State Mutation',
    icon: Shuffle,
    payload: {
      session_id: 'sess-forgery',
      signer_id: 'mallory@qnet',
      verifier_id: 'verifier-alpha',
      shots: 512,
    },
  },
  {
    key: 'impersonation',
    label: 'Signer Identity Violation',
    desc: 'Unregistered rogue participant attempting unauthorized PQC envelope issuance',
    targetLayer: 'L3 Security & Identity Guard',
    vectorType: 'Session Identity Spoofing',
    icon: User,
    payload: {
      session_id: 'sess-impersonate',
      verifier_id: 'verifier-alpha',
      shots: 512,
    },
  },
  {
    key: 'replay',
    label: 'Temporal Nonce Replay',
    desc: 'Duplicated cryptographic nonce resubmission across temporal boundaries',
    targetLayer: 'L3 Freshness & Nonce Policy',
    vectorType: 'Historical Message Injection',
    icon: RefreshCw,
    payload: {
      session_id: 'sess-replay',
      signer_id: 'alice@qnet',
      verifier_id: 'verifier-alpha',
      shots: 512,
    },
  },
  {
    key: 'unauthorized',
    label: 'Verifier Boundary Check',
    desc: 'Query submission to an untrusted verifier not recognized in federation topology',
    targetLayer: 'L3 Authorization Protocol',
    vectorType: 'Untrusted Boundary Access',
    icon: Shield,
    payload: {
      session_id: 'sess-unauth',
      signer_id: 'alice@qnet',
      shots: 512,
    },
  },
  {
    key: 'ledger',
    label: 'Evidence Chain Audit',
    desc: 'Cryptographic hash chain audit validating HMAC-SHA256 tamper-evidence',
    targetLayer: 'L4 Evidence Ledger',
    vectorType: 'Merkle/Chain Verification',
    icon: Database,
    payload: null,
  },
]

export default function AttackMatrix({ onRun, activeKey, lastResult }) {
  const [loadingKey, setLoadingKey] = useState(null)

  const handleRun = async (scenarioKey, customPayload) => {
    if (loadingKey) return
    setLoadingKey(scenarioKey)
    await onRun({ key: scenarioKey, payload: customPayload })
    setLoadingKey(null)
  }

  return (
    <section className="px-6 pb-6 space-y-5">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2.5">
          <Zap size={16} className="text-[#c6f135]" />
          <h2 className="text-sm font-semibold text-white tracking-wide">
            Adversarial Scenarios & Verification Matrix
          </h2>
        </div>
      </div>

      {/* Neutral Scenario Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3.5">
        {SCENARIOS.map((scenario) => {
          const Icon = scenario.icon
          const isLoading = loadingKey === scenario.key
          const isActive = activeKey === scenario.key
          const result = isActive && lastResult && activeKey !== 'blind' ? lastResult : null

          return (
            <div
              key={scenario.key}
              className={`glass-card p-4 flex flex-col gap-3 transition-all duration-200 hover:border-white/20
                ${isActive ? 'ring-1 ring-[#c6f135]/40 border-[#c6f135]/40' : 'border-white/10'}
              `}
            >
              {/* Header Icon + Label */}
              <div className="flex items-start gap-2.5">
                <div className="p-2 rounded-lg bg-slate-900/80 border border-white/5 text-[#c6f135]">
                  <Icon size={14} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white text-xs font-semibold leading-tight">{scenario.label}</p>
                  <p className="text-[#8b8e97] text-[11px] font-light mt-0.5 leading-snug">{scenario.desc}</p>
                </div>
              </div>

              {/* Neutral Cyber Defense Tags (No spoiler badges) */}
              <div className="flex flex-col gap-1.5 pt-1">
                <div className="flex items-center justify-between text-[11px] font-mono text-[#8b8e97]">
                  <span className="text-slate-500">Layer:</span>
                  <span className="text-slate-300">{scenario.targetLayer}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] font-mono text-[#8b8e97]">
                  <span className="text-slate-500">Vector:</span>
                  <span className="text-slate-300">{scenario.vectorType}</span>
                </div>
              </div>

              {/* Calculated Live Result (Revealed ONLY after execution) */}
              {result && (
                <div className={`text-xs px-2.5 py-1.5 rounded-lg font-mono border animate-fade-in ${
                  result.decision === 'ACCEPT' ? 'text-[#c6f135] border-[#c6f135]/30 bg-[#c6f135]/10' :
                  result.decision === 'QUARANTINE' ? 'text-amber-400 border-amber-500/30 bg-amber-500/10' :
                  'text-rose-400 border-rose-500/30 bg-rose-500/10'
                }`}>
                  <div className="flex items-center justify-between">
                    <span className="font-bold tracking-wide">▶ {result.decision}</span>
                    <span className="text-[10px] opacity-75">{Math.round(result.latency_ms)}ms</span>
                  </div>
                  <div className="text-[10px] opacity-80 mt-1 flex justify-between">
                    <span>D: {Number(result.deviation_score).toFixed(5)}</span>
                    <span>χ²: {Number(result.chi_square).toFixed(1)}</span>
                  </div>
                  {result.trial_parameters?.nonce && (
                    <div className="text-[9px] opacity-60 truncate mt-0.5">
                      {result.trial_parameters.nonce}
                    </div>
                  )}
                </div>
              )}

              {/* Action button */}
              <button
                onClick={() => handleRun(scenario.key, scenario.payload)}
                disabled={!!loadingKey}
                className="btn-scenario border border-white/15 bg-slate-900/60 hover:border-[#c6f135]/50 hover:text-[#c6f135] text-slate-300 text-xs font-medium mt-auto disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <><Loader2 size={12} className="animate-spin" /> Calculating…</>
                ) : (
                  <><Play size={12} /> Execute Trial</>
                )}
              </button>
            </div>
          )
        })}
      </div>
    </section>
  )
}
