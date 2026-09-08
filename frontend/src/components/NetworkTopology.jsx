import React from 'react';
import { Network, ShieldAlert, Lock, CheckCircle2, ShieldCheck, XCircle, ArrowRight } from 'lucide-react';

export default function NetworkTopology() {
  const networks = [
    {
      name: 'qsentinel_kv',
      role: 'Key Vault Network',
      type: 'Internal Bridge (Isolated)',
      color: '#00f5d4',
      services: ['Alice Key Material', 'Bob/Charlie Key Distribution'],
      attackerAccess: false,
      desc: 'No external or attacker route. Classical key descriptions distributed point-to-point.'
    },
    {
      name: 'qsentinel_api',
      role: 'API Public Network',
      type: 'Bridge (Exposed 8000)',
      color: '#38bdf8',
      services: ['FastAPI Backend', 'Dashboard Client', 'Adversary Harness'],
      attackerAccess: true,
      desc: 'All participants submit verification requests here; requests filtered through L3/L1/L2/L4 pipeline.'
    },
    {
      name: 'qsentinel_ledger',
      role: 'Evidence Ledger Network',
      type: 'Internal Bridge (Isolated)',
      color: '#a855f7',
      services: ['SQLite Evidence Store', 'HMAC Verifier Daemon'],
      attackerAccess: false,
      desc: 'Only the API service can append events. Direct adversary write access blocked at Docker network layer.'
    },
    {
      name: 'qsentinel_mgmt',
      role: 'Management Network',
      type: 'Bridge (Exposed 8501/3000)',
      color: '#10b981',
      services: ['Security Console (Vite)', 'Audit Dashboard', 'Health Monitoring'],
      attackerAccess: false,
      desc: 'Operator interface for auditing hash chains and monitoring threat detections.'
    }
  ];

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Network size={18} color="var(--neon-blue)" />
            Track B: 4-Network Isolated Topology & Threat Boundary
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Strict Docker network isolation enforces the adversary model (§3.1): Mallory cannot tamper with the Key Vault or Ledger directly.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="badge badge-accept" style={{ fontSize: '0.68rem' }}>
            <ShieldCheck size={12} />
            Adversary Contained
          </span>
        </div>
      </div>

      {/* Network Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {networks.map((net) => (
          <div 
            key={net.name}
            className="glass-card"
            style={{ 
              borderLeft: `4px solid ${net.color}`,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '0.85rem', color: net.color }}>
                  {net.name}
                </span>
                <span style={{ 
                  fontSize: '0.65rem', 
                  fontWeight: 600,
                  padding: '2px 6px', 
                  borderRadius: '4px', 
                  background: net.attackerAccess ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                  color: net.attackerAccess ? 'var(--neon-rose)' : 'var(--neon-emerald)',
                  border: net.attackerAccess ? '1px solid rgba(244, 63, 94, 0.3)' : '1px solid rgba(16, 185, 129, 0.3)'
                }}>
                  {net.attackerAccess ? 'Attacker Reachable' : 'Adversary Blocked'}
                </span>
              </div>

              <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                {net.role}
              </div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
                {net.desc}
              </div>
            </div>

            <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '0.5rem' }}>
              <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Connected Nodes:</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.3rem' }}>
                {net.services.map((svc, sIdx) => (
                  <span key={sIdx} className="code-val" style={{ fontSize: '0.68rem' }}>
                    {svc}
                  </span>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Adversary Boundary Flow Diagram */}
      <div style={{ background: 'rgba(7, 12, 22, 0.9)', borderRadius: '12px', padding: '1rem 1.25rem', border: '1px solid var(--border-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ padding: '0.5rem 0.75rem', borderRadius: '8px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid var(--neon-rose)', color: 'var(--neon-rose)', fontWeight: 700, fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            Mallory (Attacker Client)
          </div>
          <ArrowRight size={16} color="var(--text-muted)" />
          <div style={{ padding: '0.5rem 0.75rem', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', border: '1px solid var(--neon-blue)', color: 'var(--neon-blue)', fontWeight: 700, fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
            /v1/qds/verify (API Pipeline)
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--neon-rose)', fontSize: '0.75rem', fontWeight: 600 }}>
            <XCircle size={15} />
            Direct KeyVault Access: BLOCKED
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--neon-rose)', fontSize: '0.75rem', fontWeight: 600 }}>
            <XCircle size={15} />
            Direct Ledger Access: BLOCKED
          </div>
        </div>
      </div>
    </div>
  );
}
