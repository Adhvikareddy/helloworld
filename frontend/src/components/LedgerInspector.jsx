import { useState, useMemo } from 'react'
import { ChevronDown, ChevronRight, ShieldCheck, ShieldAlert, RefreshCw, Database, Loader2, Clock } from 'lucide-react'
import { verifyLedgerChain } from '../services/api'

const DECISION_STYLE = {
  ACCEPT: 'text-[#c6f135] bg-[#c6f135]/10 border-[#c6f135]/30',
  REJECT: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  QUARANTINE: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
  INTEGRITY_ALARM: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
  INFO: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30',
}

function HashCell({ hash }) {
  if (!hash) return <span className="text-[#8b8e97] font-mono text-xs">—</span>
  return (
    <span className="font-mono text-xs text-[#8b8e97] tracking-tight">
      {hash.slice(0, 8)}…{hash.slice(-8)}
    </span>
  )
}

function EventRow({ event, index, isLatest }) {
  const [expanded, setExpanded] = useState(false)
  const style = DECISION_STYLE[event.decision] || DECISION_STYLE.REJECT

  const seqDisplay = event.seq_num !== undefined && event.seq_num !== null
    ? `#${event.seq_num}`
    : `idx-${index + 1}`

  return (
    <>
      <tr
        onClick={() => setExpanded(v => !v)}
        className={`border-b border-white/5 hover:bg-white/[0.04] cursor-pointer transition-colors
          ${isLatest ? 'bg-[#c6f135]/[0.03]' : ''}
        `}
      >
        <td className="px-3 py-2.5 text-xs font-mono whitespace-nowrap">
          <div className="flex items-center gap-1.5">
            {isLatest && (
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#c6f135] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#c6f135]"></span>
              </span>
            )}
            <span className={isLatest ? 'text-[#c6f135] font-bold' : 'text-[#8b8e97]'}>
              {seqDisplay}
            </span>
          </div>
        </td>
        <td className="px-3 py-2.5">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[#c6f135]/90">
              {event.event_id || event.evidence_id || '—'}
            </span>
            {isLatest && (
              <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-[#c6f135]/15 text-[#c6f135] border border-[#c6f135]/30">
                Latest
              </span>
            )}
          </div>
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
        <tr className="bg-black/40 border-b border-white/5">
          <td colSpan={9} className="px-6 py-3">
            <div className="text-[11px] font-mono text-slate-400 mb-2 flex items-center justify-between">
              <span className="text-slate-500">Block Details ({seqDisplay})</span>
              {event.reason && <span className="text-[#c6f135]">Reason: {event.reason}</span>}
            </div>
            <pre className="text-xs font-mono text-slate-300 whitespace-pre-wrap max-h-56 overflow-y-auto bg-black/40 p-3 rounded-lg border border-white/5">
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

  // Guarantee most recent event is always at index 0 (top of the ledger)
  const sortedEvents = useMemo(() => {
    return [...events].sort((a, b) => {
      const seqA = a.seq_num != null ? Number(a.seq_num) : null
      const seqB = b.seq_num != null ? Number(b.seq_num) : null
      if (seqA !== null && seqB !== null) return seqB - seqA
      const tA = typeof a.timestamp === 'number' ? a.timestamp : 0
      const tB = typeof b.timestamp === 'number' ? b.timestamp : 0
      return tB - tA
    })
  }, [events])

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
          <span className="text-xs text-[#8b8e97] font-mono">({sortedEvents.length} records · Newest on top)</span>
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
                {['Seq / Block', 'Event ID', 'Timestamp', 'Signer', 'Verifier', 'Decision', 'Prev Hash', 'Curr Hash', ''].map(h => (
                  <th key={h} className="px-3 py-2.5 text-slate-500 text-xs font-semibold uppercase tracking-wide whitespace-nowrap">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedEvents.length === 0 ? (
                <tr>
                  <td colSpan={9} className="px-4 py-8 text-center text-slate-600 text-sm font-mono">
                    No ledger events yet — run a scenario to generate records.
                  </td>
                </tr>
              ) : (
                sortedEvents.map((evt, i) => (
                  <EventRow key={evt.event_id || evt.evidence_id || i} event={evt} index={i} isLatest={i === 0} />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}
