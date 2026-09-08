import React from 'react';
import { Grid, ShieldCheck, ShieldAlert, Check, X, Minus } from 'lucide-react';

export default function AttackMatrix({ lastTriggeredScenario }) {
  const vectors = [
    {
      name: 'Impersonation (Mallory as Alice)',
      id: 'impersonation',
      layers: {
        l1: { active: false, label: '-' },
        l2: { active: false, label: '-' },
        l3: { active: true, label: 'IdentityGuard (REJECT)', highlight: true, color: '#f43f5e' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    },
    {
      name: 'Unauthorized Verifier (Untrusted Node)',
      id: 'unauthorized',
      layers: {
        l1: { active: false, label: '-' },
        l2: { active: false, label: '-' },
        l3: { active: true, label: 'AuthorizationGuard (REJECT)', highlight: true, color: '#f43f5e' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    },
    {
      name: 'Replay / Session Reuse',
      id: 'replay',
      layers: {
        l1: { active: false, label: '-' },
        l2: { active: false, label: '-' },
        l3: { active: true, label: 'DoubleConsumption / NonceGuard', highlight: true, color: '#f59e0b' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    },
    {
      name: 'Channel Noise / Eavesdropping',
      id: 'channel',
      layers: {
        l1: { active: true, label: 'Noise Simulated (Depol)', color: '#00f5d4' },
        l2: { active: true, label: 'Statistical & Tomography (REJECT)', highlight: true, color: '#00f5d4' },
        l3: { active: true, label: 'PQC Signature Pass', color: '#10b981' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    },
    {
      name: 'Signature Forgery (Type A: Mutated)',
      id: 'forgery_a',
      layers: {
        l1: { active: false, label: '-' },
        l2: { active: false, label: '-' },
        l3: { active: true, label: 'ML-DSA-65 Envelope (REJECT)', highlight: true, color: '#a855f7' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    },
    {
      name: 'Quantum Forgery (Type B: Blind Guess)',
      id: 'forgery_b',
      layers: {
        l1: { active: true, label: 'Circuits Evaluated', color: '#00f5d4' },
        l2: { active: true, label: 'P_forge Bound Exceeded', highlight: true, color: '#f59e0b' },
        l3: { active: true, label: 'PQC Signature Pass', color: '#10b981' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    },
    {
      name: 'Evidence Ledger Database Tamper',
      id: 'ledger_tamper',
      layers: {
        l1: { active: false, label: '-' },
        l2: { active: false, label: '-' },
        l3: { active: false, label: '-' },
        l4: { active: true, label: 'HMAC & Hash Link Breakage', highlight: true, color: '#f43f5e' }
      }
    },
    {
      name: 'Timing Side-Channel Probe',
      id: 'timing_oracle',
      layers: {
        l1: { active: false, label: '-' },
        l2: { active: false, label: '-' },
        l3: { active: true, label: 'Constant-Time Latency Guard', highlight: true, color: '#38bdf8' },
        l4: { active: true, label: 'Audit Logged', color: '#38bdf8' }
      }
    }
  ];

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Grid size={18} color="var(--neon-violet)" />
            Attack-vs-Defense Verification Matrix
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Real-time multi-layered defense mapping demonstrating zero single-point-of-failure defense causality.
          </p>
        </div>
        <span className="badge badge-violet" style={{ fontSize: '0.7rem' }}>
          4 Layers • 7 Vectors
        </span>
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-active)', textAlign: 'left' }}>
              <th style={{ padding: '0.75rem 1rem', color: 'var(--text-secondary)' }}>Threat Vector</th>
              <th style={{ padding: '0.75rem 0.5rem', color: 'var(--neon-cyan)' }}>L1: Quantum Physical</th>
              <th style={{ padding: '0.75rem 0.5rem', color: 'var(--neon-cyan)' }}>L2: Statistical & Tomo</th>
              <th style={{ padding: '0.75rem 0.5rem', color: 'var(--neon-violet)' }}>L3: Auth & Freshness</th>
              <th style={{ padding: '0.75rem 0.5rem', color: 'var(--neon-blue)' }}>L4: Evidence Ledger</th>
            </tr>
          </thead>
          <tbody>
            {vectors.map((vec) => {
              const isTriggered = lastTriggeredScenario === vec.id;
              return (
                <tr 
                  key={vec.id} 
                  style={{ 
                    borderBottom: '1px solid var(--border-subtle)',
                    background: isTriggered ? 'rgba(0, 245, 212, 0.07)' : 'transparent',
                    transition: 'background 0.3s ease'
                  }}
                >
                  <td style={{ padding: '0.85rem 1rem', fontWeight: 600, color: isTriggered ? 'var(--neon-cyan)' : 'var(--text-primary)' }}>
                    {vec.name}
                  </td>
                  
                  {['l1', 'l2', 'l3', 'l4'].map((layerKey) => {
                    const l = vec.layers[layerKey];
                    return (
                      <td key={layerKey} style={{ padding: '0.85rem 0.5rem' }}>
                        {l.active ? (
                          <span style={{ 
                            display: 'inline-flex', 
                            alignItems: 'center', 
                            gap: '4px',
                            color: l.color || 'var(--text-secondary)',
                            fontWeight: l.highlight ? 700 : 400,
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.75rem',
                            background: l.highlight ? `${l.color}15` : 'rgba(255,255,255,0.02)',
                            padding: '3px 7px',
                            borderRadius: '5px',
                            border: l.highlight ? `1px solid ${l.color}40` : '1px solid transparent'
                          }}>
                            {l.highlight && <ShieldCheck size={12} />}
                            {l.label}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', opacity: 0.4 }}>—</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
