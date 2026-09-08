import { useState } from 'react'
import { ChevronDown, ChevronRight, ShieldCheck, ShieldAlert, RefreshCw, Database, Loader2 } from 'lucide-react'
import { verifyLedgerChain } from '../services/api'

const DECISION_STYLE = {
  ACCEPT: 'text-[#c6f135] bg-[#c6f135]/10 border-[#c6f135]/30',
  REJECT: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  QUARANTINE: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  INTEGRITY_ALARM: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
}

function HashCell({ hash }) {
  if (!hash) return <span className="text-[#8b8e97] font-mono text-xs">—</span>
  return (
    <span className="font-mono text-xs text-[#8b8e97] tracking-tight">
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
        <td className="px-3 py-2.5 text-[#8b8e97] text-xs font-mono">{index + 1}</td>
        <td className="px-3 py-2.5">
          <span className="font-mono text-xs text-[#c6f135]/90">{event.event_id?.slice(0, 18)}…</span>
        </td>
        <td className="px-3 py-2.5 text-[#8b8e97] text-xs whitespace-nowrap">
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
        <td className="px-3 py-2.5 text-[#8b8e97] text-xs font-mono">{event.verifier_id}</td>
        <td className="px-3 py-2.5">
          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold border ${style}`}>
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
        <tr className="bg-black/30 border-b border-white/5">
          <td colSpan={9} className="px-6 py-3">
            <pre className="text-xs font-mono text-slate-400 whitespace-pre-wrap max-h-48 overflow-y-auto">
              {JSON.stringify(event, null, 2)}
            </pre>
          </td>
        </tr>
      )}
    </>
  )
}

export default function LedgerInspector({ events = [], onRefresh }) {
  const [auditing, setAuditing] = useState(false)
  const [auditResult, setAuditResult] = useState(null)

  const handleAudit = async () => {
    setAuditing(true)
    const res = await verifyLedgerChain()
    setAuditResult(res)
    setAuditing(false)
  }

  return (
    <section className="px-6 pb-8">
      {/* Section Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <Database size={17} className="text-[#c6f135]" />
          <h2 className="text-base font-semibold text-white">Tamper-Evident Evidence Ledger</h2>
          <span className="text-xs text-[#8b8e97] font-mono">({events.length} records)</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRefresh}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
              border border-white/10 bg-slate-900/60 text-[#8b8e97]
              hover:border-[#c6f135]/40 hover:text-white transition-all"
          >
            <RefreshCw size={11} /> Refresh
          </button>
          <button
            onClick={handleAudit}
            disabled={auditing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
              border border-[#c6f135]/40 bg-[#c6f135]/10 text-[#c6f135]
              hover:bg-[#c6f135]/20 transition-all disabled:opacity-50"
          >
            {auditing
              ? <><Loader2 size={11} className="animate-spin" /> Auditing…</>
              : <><ShieldCheck size={11} /> Verify Hash Chain</>
            }
          </button>
        </div>
      </div>

      {/* Audit result banner */}
      {auditResult && (
        <div className={`mb-4 flex items-center gap-3 px-4 py-3 rounded-xl border text-xs font-mono animate-slide-in
          ${auditResult.valid
            ? 'border-[#c6f135]/40 bg-[#c6f135]/10 text-[#c6f135]'
            : 'border-rose-500/40 bg-rose-500/10 text-rose-300'
          }`}>
          {auditResult.valid
            ? <><ShieldCheck size={15} /> Hash-chain integrity VERIFIED — {auditResult.events_checked} events audited. Ledger is immutable.</>
            : <><ShieldAlert size={15} /> INTEGRITY VIOLATION — chain broken at event: {auditResult.broken_at}</>
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
