import React, { useState } from 'react';
import { Database, Link, AlertOctagon, CheckCircle, Shield, AlertTriangle, ChevronRight, FileCode, RefreshCw } from 'lucide-react';

export default function HashChainExplorer({ 
  events, 
  onVerifyChain, 
  chainAuditResult, 
  isVerifyingChain,
  onTamperDb,
  isTampering,
  onRefreshEvents
}) {
  const [selectedBlock, setSelectedBlock] = useState(null);

  const isChainValid = chainAuditResult?.chain_valid !== false;

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Database size={18} color="var(--neon-blue)" />
            Live Evidence Ledger & Hash-Chain Explorer (L4)
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Append-only SQLite evidence ledger with continuous SHA-256 hash chaining and HMAC-SHA256 cryptographic signatures.
          </p>
        </div>

        {/* Chain Verification and Tamper Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '0.5rem', 
            padding: '0.4rem 0.75rem', 
            borderRadius: '8px', 
            background: isChainValid ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.15)',
            border: isChainValid ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(244, 63, 94, 0.5)'
          }}>
            {isChainValid ? <CheckCircle size={15} color="var(--neon-emerald)" /> : <AlertOctagon size={15} color="var(--neon-rose)" />}
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: isChainValid ? 'var(--neon-emerald)' : 'var(--neon-rose)', fontFamily: 'var(--font-mono)' }}>
              {isChainValid ? 'CHAIN INTEGRITY: VERIFIED' : 'INTEGRITY VIOLATION DETECTED'}
            </span>
          </div>

          <button
            onClick={onVerifyChain}
            disabled={isVerifyingChain}
            className="cyber-btn cyber-btn-primary"
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }}
          >
            <Shield size={13} />
            {isVerifyingChain ? 'Auditing...' : 'Audit Chain'}
          </button>

          <button
            onClick={onTamperDb}
            disabled={isTampering}
            className="cyber-btn cyber-btn-danger"
            style={{ padding: '0.4rem 0.8rem', fontSize: '0.75rem' }}
            title="Simulate adversarial SQLite tampering to test L4 detection"
          >
            <AlertTriangle size={13} />
            {isTampering ? 'Tampering...' : 'Tamper Database'}
          </button>

          <button
            onClick={onRefreshEvents}
            className="cyber-btn"
            style={{ padding: '0.4rem 0.6rem' }}
          >
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      {/* Horizontal Scrollable Block Chain */}
      <div style={{ marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: 'max-content' }}>
          {events && events.length > 0 ? (
            events.slice(0, 15).map((evt, idx) => {
              const isSelected = selectedBlock?.seq_num === evt.seq_num;
              const isTamperedEvent = !isChainValid && idx === 0;

              return (
                <React.Fragment key={evt.seq_num || idx}>
                  {/* Block Card */}
                  <div
                    onClick={() => setSelectedBlock(evt)}
                    className="glass-card"
                    style={{
                      width: '240px',
                      cursor: 'pointer',
                      border: isTamperedEvent 
                        ? '1px solid var(--neon-rose)' 
                        : isSelected 
                          ? '1px solid var(--neon-cyan)' 
                          : '1px solid var(--border-subtle)',
                      boxShadow: isTamperedEvent 
                        ? '0 0 15px rgba(244, 63, 94, 0.4)' 
                        : isSelected 
                          ? '0 0 15px rgba(0, 245, 212, 0.25)' 
                          : 'none',
                      background: isTamperedEvent 
                        ? 'rgba(244, 63, 94, 0.08)' 
                        : 'rgba(14, 23, 38, 0.9)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem', color: 'var(--neon-blue)' }}>
                        #{evt.seq_num}
                      </span>
                      <span className={`badge ${evt.decision === 'ACCEPT' ? 'badge-accept' : evt.decision === 'QUARANTINE' ? 'badge-quarantine' : 'badge-reject'}`} style={{ fontSize: '0.65rem' }}>
                        {evt.decision}
                      </span>
                    </div>

                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                      Event: <span style={{ color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{evt.event_id?.substring(0, 16)}...</span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                      Signer: <span style={{ color: 'var(--text-secondary)' }}>{evt.signer_id}</span> • Verifier: <span style={{ color: 'var(--text-secondary)' }}>{evt.verifier_id}</span>
                    </div>
                    
                    <div style={{ background: 'rgba(0,0,0,0.3)', padding: '4px 6px', borderRadius: '4px', fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      Hash: {evt.current_hash?.substring(0, 18)}...
                    </div>
                  </div>

                  {/* Hash Link Connector Line */}
                  {idx < Math.min(events.length, 15) - 1 && (
                    <div style={{ display: 'flex', alignItems: 'center', color: isTamperedEvent ? 'var(--neon-rose)' : 'var(--neon-cyan)', opacity: 0.7 }}>
                      <Link size={16} />
                      <div style={{ width: '12px', height: '2px', background: isTamperedEvent ? 'var(--neon-rose)' : 'var(--neon-cyan)' }} />
                    </div>
                  )}
                </React.Fragment>
              );
            })
          ) : (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)', width: '100%' }}>
              No evidence blocks recorded yet. Execute an attack or verification to populate the ledger.
            </div>
          )}
        </div>
      </div>

      {/* Detailed Block Inspector Drawer */}
      {selectedBlock && (
        <div style={{ background: 'rgba(7, 12, 22, 0.95)', border: '1px solid var(--border-active)', borderRadius: '12px', padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileCode size={16} color="var(--neon-cyan)" />
              Block #{selectedBlock.seq_num} Evidence Inspector
            </h3>
            <button 
              onClick={() => setSelectedBlock(null)}
              style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', fontSize: '0.8rem' }}
            >
              Close
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', marginBottom: '0.75rem', fontSize: '0.75rem' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Current Hash: </span>
              <div className="code-val" style={{ marginTop: '2px', wordBreak: 'break-all' }}>{selectedBlock.current_hash}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Previous Hash: </span>
              <div className="code-val" style={{ marginTop: '2px', wordBreak: 'break-all' }}>{selectedBlock.previous_hash}</div>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>HMAC Signature: </span>
              <div className="code-val" style={{ marginTop: '2px', wordBreak: 'break-all', color: 'var(--neon-violet)' }}>{selectedBlock.signature}</div>
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.4)', borderRadius: '8px', padding: '0.75rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.35rem' }}>Full Canonical Event:</div>
            <pre style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: '#cbd5e1', overflowX: 'auto' }}>
              {JSON.stringify(selectedBlock, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
