import { Cpu, ShieldCheck, BookLock, Radio } from 'lucide-react'
import { useHealthPoller } from '../hooks/useHealthPoller'

const chips = [
  { icon: Cpu, label: 'Qiskit-Aer Engine', sub: 'Quantum Simulator' },
  { icon: ShieldCheck, label: 'L3 Strict Nonce', sub: 'Auth Guard Active' },
  { icon: BookLock, label: 'L4 Hash-Chain', sub: 'Ledger Valid' },
]

function StatusChip({ icon: Icon, label, sub }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-slate-900/60 text-slate-300 text-xs font-medium">
      <span className="w-1.5 h-1.5 rounded-full bg-[#c6f135] shadow-[0_0_6px_#c6f135]" />
      <Icon size={12} className="text-[#c6f135]" />
      <span>{label}</span>
      <span className="text-[#8b8e97] hidden sm:inline">· {sub}</span>
    </div>
  )
}

export default function Header() {
  const health = useHealthPoller(3000)

  return (
    <header className="relative px-6 pt-10 pb-6 text-center">
      {/* Banner */}
      <div className="mb-3.5 inline-flex items-center gap-2 px-3.5 py-1 rounded-full border border-[#c6f135]/25 bg-[#c6f135]/5 text-[#c6f135] text-[11px] font-medium tracking-[0.25em] uppercase">
        SIH 2026 · PS SIH26141 · Egreen Quanta
      </div>

      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-normal tracking-[0.08em] mb-3 text-white flex items-center justify-center">
        <span style={{ fontFamily: "'Cinzel', serif" }}>Q-SENTINEL</span>
      </h1>

      <p className="text-[#8b8e97] text-sm sm:text-base font-light tracking-wide max-w-2xl mx-auto mb-6">
        Teleportation-Based Quantum Digital Signature Threat Detection
      </p>

      {/* Status chips */}
      <div className="flex flex-wrap justify-center gap-2">
        {/* Live Backend Connection Status */}
        <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${
          health.online
            ? 'border-[#c6f135]/30 bg-slate-900/60 text-slate-300'
            : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${
            health.online ? 'bg-[#c6f135] shadow-[0_0_6px_#c6f135] animate-pulse' : 'bg-amber-400'
          }`} />
          <Radio size={12} className={health.online ? 'text-[#c6f135]' : 'text-amber-400'} />
          <span>{health.online ? 'Backend Live (:8000)' : 'Connecting / Mock'}</span>
          {health.latencyMs !== null && (
            <span className="text-[#8b8e97] font-mono text-[10px]">· {health.latencyMs}ms</span>
          )}
        </div>

        {chips.map(c => (
          <StatusChip key={c.label} {...c} />
        ))}
      </div>

      {/* Divider */}
      <div className="mt-7 h-px bg-gradient-to-r from-transparent via-[#c6f135]/20 to-transparent max-w-4xl mx-auto" />
    </header>
  )
}
