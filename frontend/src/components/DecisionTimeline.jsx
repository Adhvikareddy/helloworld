import React, { useState } from 'react';
import { Activity, Clock, ShieldCheck, ShieldAlert, Filter, ChevronDown } from 'lucide-react';

export default function DecisionTimeline({ events }) {
  const [filter, setFilter] = useState('ALL');

  const filteredEvents = events.filter((evt) => {
    if (filter === 'ALL') return true;
    return evt.decision === filter;
  });

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={18} color="var(--neon-emerald)" />
            Live Verification Decision Timeline
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Chronological audit of incoming QDS verification decisions with granular layer finding attribution.
          </p>
        </div>

        {/* Filter buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', background: 'rgba(0,0,0,0.3)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          {['ALL', 'ACCEPT', 'QUARANTINE', 'REJECT'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                background: filter === f ? 'rgba(255,255,255,0.1)' : 'transparent',
                color: filter === f ? '#fff' : 'var(--text-muted)',
                border: 'none',
                borderRadius: '6px',
                padding: '0.3rem 0.6rem',
                fontSize: '0.7rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Stream */}
      <div style={{ maxHeight: '420px', overflowY: 'auto', paddingRight: '0.5rem' }}>
        {filteredEvents && filteredEvents.length > 0 ? (
          filteredEvents.map((evt, idx) => {
            const dateStr = evt.timestamp ? new Date(evt.timestamp * 1000).toLocaleTimeString() : 'N/A';
            const findingsList = Array.isArray(evt.findings) ? evt.findings : [];

            return (
              <div
                key={evt.seq_num || idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '1rem',
                  padding: '0.85rem 1rem',
                  borderRadius: '10px',
                  background: 'rgba(14, 23, 38, 0.6)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: '0.65rem',
                  transition: 'all 0.2s ease'
                }}
              >
                {/* Status Indicator Icon */}
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: evt.decision === 'ACCEPT' 
                    ? 'rgba(16, 185, 129, 0.15)' 
                    : evt.decision === 'QUARANTINE' 
                      ? 'rgba(245, 158, 11, 0.15)' 
                      : 'rgba(244, 63, 94, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0
                }}>
                  {evt.decision === 'ACCEPT' ? (
                    <ShieldCheck size={16} color="var(--neon-emerald)" />
                  ) : (
                    <ShieldAlert size={16} color={evt.decision === 'QUARANTINE' ? 'var(--neon-amber)' : 'var(--neon-rose)'} />
                  )}
                </div>

                {/* Event Summary & Findings */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.8rem', color: 'var(--neon-blue)' }}>
                        #{evt.seq_num}
                      </span>
                      <span className={`badge ${evt.decision === 'ACCEPT' ? 'badge-accept' : evt.decision === 'QUARANTINE' ? 'badge-quarantine' : 'badge-reject'}`}>
                        {evt.decision}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        {evt.signer_id} → {evt.verifier_id}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                      <Clock size={12} />
                      <span style={{ fontFamily: 'var(--font-mono)' }}>{dateStr}</span>
                    </div>
                  </div>

                  {/* Findings pills */}
                  {findingsList.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem', marginTop: '0.35rem' }}>
                      {findingsList.map((f, fIdx) => (
                        <span 
                          key={fIdx}
                          style={{
                            fontSize: '0.68rem',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            background: f.severity === 'REJECT' 
                              ? 'rgba(244, 63, 94, 0.12)' 
                              : f.severity === 'QUARANTINE'
                                ? 'rgba(245, 158, 11, 0.12)'
                                : 'rgba(16, 185, 129, 0.12)',
                            color: f.severity === 'REJECT' 
                              ? 'var(--neon-rose)' 
                              : f.severity === 'QUARANTINE'
                                ? 'var(--neon-amber)'
                                : 'var(--neon-emerald)',
                            border: '1px solid rgba(255,255,255,0.05)',
                            fontFamily: 'var(--font-mono)'
                          }}
                        >
                          {f.detector || f.detector_name}: {f.description || f.severity}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        ) : (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            No verification events match filter {filter}.
          </div>
        )}
      </div>
    </div>
  );
}
