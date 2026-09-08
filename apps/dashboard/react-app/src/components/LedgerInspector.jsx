import { useState } from 'react'
import { ChevronDown, ChevronRight, ShieldCheck, ShieldAlert, RefreshCw, Database, Loader2 } from 'lucide-react'
import { verifyLedgerChain } from '../services/api'

const DECISION_STYLE = {
  ACCEPT: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  REJECT: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  QUARANTINE: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  INTEGRITY_ALARM: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
}

function HashCell({ hash }) {
  if (!hash) return <span className="text-slate-600 font-mono text-xs">—</span>
  return (
    <span className="font-mono text-xs text-slate-400 tracking-tight">
      {hash.slice(0, 8)}…{hash.slice(-8)}
    </span>
  )
}

function EventRow({ event, index }) {
  const [expanded, setExpanded] = useState(false)
  const style = DECISION_STYLE[event.decision] || DECISION_STYLE.REJECT

  return (
    <>
      <tr
        onClick={() => setExpanded(v => !v)}
        className="border-b border-white/5 hover:bg-white/[0.03] cursor-pointer transition-colors"
      >
        <td className="px-3 py-2.5 text-slate-500 text-xs font-mono">{index + 1}</td>
        <td className="px-3 py-2.5">
          <span className="font-mono text-xs text-cyan-400/80">{event.event_id?.slice(0, 18)}…</span>
        </td>
        <td className="px-3 py-2.5 text-slate-400 text-xs whitespace-nowrap">
          {(() => {
            const t = event.timestamp
            const ms = typeof t === 'number' && t < 1e11 ? t * 1000 : t
            try {
              return new Date(ms).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            } catch {
              return '—'
            }
          })()}
        </td>
        <td className="px-3 py-2.5 text-slate-300 text-xs font-mono">{event.signer_id}</td>
        <td className="px-3 py-2.5 text-slate-400 text-xs font-mono">{event.verifier_id}</td>
        <td className="px-3 py-2.5">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-bold border ${style}`}>
            {event.decision}
          </span>
        </td>
        <td className="px-3 py-2.5"><HashCell hash={event.previous_hash} /></td>
        <td className="px-3 py-2.5"><HashCell hash={event.current_hash} /></td>
        <td className="px-3 py-2.5 text-slate-600">
          {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
        </td>
      </tr>

      {expanded && (
        <tr className="bg-slate-900/60">
          <td colSpan={9} className="px-4 py-3">
            <pre className="text-xs font-mono text-slate-400 overflow-x-auto whitespace-pre-wrap leading-relaxed
              bg-black/40 rounded-lg p-3 border border-white/5 max-h-48">
              {JSON.stringify(event, null, 2)}
            </pre>
          </td>
        </tr>
      )}
    </>
  )
}

export default function LedgerInspector({ events = [], onRefresh }) {
  const [auditResult, setAuditResult] = useState(null)
  const [auditing, setAuditing] = useState(false)

  const handleAudit = async () => {
    setAuditing(true)
    setAuditResult(null)
    const result = await verifyLedgerChain()
    setAuditResult(result)
    setAuditing(false)
  }

  return (
    <section className="px-6 pb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Database size={18} className="text-cyan-400" />
          <h2 className="text-lg font-bold text-white">Tamper-Evident Evidence Ledger</h2>
          <span className="text-xs text-slate-500 font-mono">{events.length} events</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
              border border-slate-700/50 bg-slate-800/50 text-slate-400
              hover:border-cyan-500/30 hover:text-cyan-300 transition-all"
          >
            <RefreshCw size={11} /> Refresh
          </button>
          <button
            onClick={handleAudit}
            disabled={auditing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold
              border border-cyan-500/30 bg-cyan-500/10 text-cyan-300
              hover:bg-cyan-500/20 transition-all disabled:opacity-50"
          >
            {auditing
              ? <><Loader2 size={11} className="animate-spin" /> Auditing…</>
              : <><ShieldCheck size={11} /> Verify Chain</>
            }
          </button>
        </div>
      </div>

      {/* Audit result banner */}
      {auditResult && (
        <div className={`mb-4 flex items-center gap-3 px-4 py-3 rounded-xl border text-sm font-semibold animate-slide-in
          ${auditResult.valid
            ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300'
            : 'border-rose-500/40 bg-rose-500/10 text-rose-300'
          }`}>
          {auditResult.valid
            ? <><ShieldCheck size={16} /> Hash-chain integrity VERIFIED — {auditResult.events_checked} events checked. Ledger is immutable.</>
            : <><ShieldAlert size={16} /> INTEGRITY VIOLATION — chain broken at event: {auditResult.broken_at}</>
          }
          {auditResult._mock && <span className="ml-auto text-xs opacity-60">[mock]</span>}
        </div>
      )}

      {/* Table */}
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-white/8 bg-slate-900/50">
                {['#', 'Event ID', 'Timestamp', 'Signer', 'Verifier', 'Decision', 'Prev Hash', 'Curr Hash', ''].map(h => (
                  <th key={h} className="px-3 py-2.5 text-slate-500 text-xs font-semibold uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {events.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-slate-600 text-sm font-mono">
                    No ledger events yet — run a scenario to generate records.
                  </td>
                </tr>
              ) : (
                events.map((evt, i) => (
                  <EventRow key={evt.event_id || i} event={evt} index={i} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
