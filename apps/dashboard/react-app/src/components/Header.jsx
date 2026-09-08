import { Cpu, ShieldCheck, BookLock, Wifi, WifiOff, Clock } from 'lucide-react'

const chips = [
  { icon: Cpu, label: 'Qiskit-Aer Engine', sub: 'Quantum Simulator', color: 'cyan' },
  { icon: ShieldCheck, label: 'L3 Strict Nonce', sub: 'Auth Guard Active', color: 'emerald' },
  { icon: BookLock, label: 'L4 Hash-Chain', sub: 'Ledger Valid', color: 'emerald' },
]

function StatusChip({ icon: Icon, label, sub, color }) {
  const colors = {
    cyan: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-300',
    emerald: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  }
  const dotColors = { cyan: 'bg-cyan-400', emerald: 'bg-emerald-400' }

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium ${colors[color]}`}>
      <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${dotColors[color]}`} />
      <Icon size={12} />
      <span>{label}</span>
      <span className="opacity-60 hidden sm:inline">· {sub}</span>
    </div>
  )
}

export default function Header({ healthStatus }) {
  const { online, latencyMs, mode } = healthStatus

  return (
    <header className="relative px-6 pt-8 pb-6 text-center">
      {/* Top right backend indicator */}
      <div className="absolute top-6 right-6 flex items-center gap-2">
        {online === null ? (
          <span className="status-chip border-slate-600 bg-slate-800/50 text-slate-400">
            <Clock size={11} /> Connecting…
          </span>
        ) : online ? (
          <span className="status-chip border-emerald-500/40 bg-emerald-500/10 text-emerald-300">
            <Wifi size={11} />
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LIVE · {latencyMs}ms
          </span>
        ) : (
          <span className="status-chip border-amber-500/40 bg-amber-500/10 text-amber-300">
            <WifiOff size={11} />
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            MOCK FALLBACK
          </span>
        )}
      </div>

      {/* Banner */}
      <div className="mb-2 inline-flex items-center gap-2 px-4 py-1 rounded-full border border-cyan-500/20 bg-cyan-500/5 text-cyan-400 text-xs font-semibold tracking-widest uppercase">
        SIH 2026 · PS SIH26141 · Egreen Quanta
      </div>

      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight mb-3">
        <span className="gradient-text">Q-SENTINEL</span>
        <span className="text-white/20 font-light"> v9.1</span>
      </h1>

      <p className="text-slate-400 text-sm sm:text-base font-medium tracking-wide max-w-2xl mx-auto mb-6">
        Teleportation-Based Quantum Digital Signature Threat Detection
      </p>

      {/* Status chips */}
      <div className="flex flex-wrap justify-center gap-2">
        {chips.map(c => (
          <StatusChip key={c.label} {...c} />
        ))}
      </div>

      {/* Divider */}
      <div className="mt-6 h-px bg-gradient-to-r from-transparent via-cyan-500/30 to-transparent" />
    </header>
  )
}
