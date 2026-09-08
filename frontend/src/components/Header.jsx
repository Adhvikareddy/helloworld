import React from 'react';
import { Shield, ShieldAlert, Cpu, Activity, UserCheck, RefreshCw, Key } from 'lucide-react';

export default function Header({
  health,
  calibration,
  userRole,
  setUserRole,
  onCalibrate,
  isCalibrating,
  stats,
  onRefresh,
}) {
  const isHealthy = health?.status === 'ok';
  const isCalibrated = calibration?.policy_version && calibration.policy_version !== 'uncalibrated';

  return (
    <header className="glass-panel" style={{ padding: '1rem 1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
        {/* Brand & Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, rgba(0, 245, 212, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%)',
            border: '1px solid rgba(0, 245, 212, 0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(0, 245, 212, 0.2)'
          }}>
            <Shield size={24} color="#00f5d4" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <h1 style={{ fontSize: '1.35rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #fff, #00f5d4)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Q-SENTINEL <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#a855f7', WebkitTextFillColor: 'initial', padding: '2px 6px', background: 'rgba(168, 85, 247, 0.15)', borderRadius: '4px', border: '1px solid rgba(168, 85, 247, 0.3)' }}>v9.1</span>
              </h1>
              <span className="badge badge-info" style={{ fontSize: '0.65rem' }}>Track B • SIH PS 26141</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Quantum-Inspired Digital Signature Defense & Real-Causality Attacker Console
            </p>
          </div>
        </div>

        {/* Status Indicators & Role Switcher */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Backend Health Pill */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.4rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <div className={`pulse-dot ${isHealthy ? 'emerald' : 'rose'}`} />
            <span style={{ fontSize: '0.8rem', fontFamily: 'var(--font-mono)' }}>
              {isHealthy ? 'API ONLINE' : 'API DISCONNECTED'}
            </span>
          </div>

          {/* Calibration Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(0,0,0,0.3)', padding: '0.4rem 0.75rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <Cpu size={15} color={isCalibrated ? '#10b981' : '#f59e0b'} />
            <div style={{ fontSize: '0.75rem' }}>
              <span style={{ color: 'var(--text-muted)' }}>Policy: </span>
              <span style={{ fontWeight: 600, color: isCalibrated ? '#10b981' : '#f59e0b' }}>
                {isCalibrated ? calibration.policy_version : 'Uncalibrated'}
              </span>
              {isCalibrated && calibration.thresholds && (
                <span style={{ marginLeft: '6px', fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                  [{calibration.thresholds[0]}, {calibration.thresholds[1]}]
                </span>
              )}
            </div>
            {!isCalibrated && (
              <button 
                onClick={onCalibrate}
                disabled={isCalibrating}
                className="cyber-btn cyber-btn-primary"
                style={{ padding: '0.2rem 0.6rem', fontSize: '0.7rem', marginLeft: '0.25rem' }}
              >
                {isCalibrating ? 'Calibrating...' : 'Calibrate'}
              </button>
            )}
          </div>

          {/* Role-Based Response Tiering Toggle */}
          <div style={{ display: 'flex', alignItems: 'center', background: 'rgba(0,0,0,0.4)', borderRadius: '10px', padding: '3px', border: '1px solid var(--border-active)' }}>
            <button
              onClick={() => setUserRole('standard')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.8rem',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.2s',
                background: userRole === 'standard' ? 'rgba(56, 189, 248, 0.2)' : 'transparent',
                color: userRole === 'standard' ? '#38bdf8' : 'var(--text-muted)',
              }}
            >
              <UserCheck size={14} />
              Standard Verifier (Bob)
            </button>
            <button
              onClick={() => setUserRole('auditor')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.8rem',
                borderRadius: '8px',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                transition: 'all 0.2s',
                background: userRole === 'auditor' ? 'rgba(168, 85, 247, 0.25)' : 'transparent',
                color: userRole === 'auditor' ? '#c084fc' : 'var(--text-muted)',
                boxShadow: userRole === 'auditor' ? '0 0 10px rgba(168, 85, 247, 0.2)' : 'none'
              }}
            >
              <ShieldAlert size={14} />
              Auditor / Admin
            </button>
          </div>

          {/* Manual Refresh Button */}
          <button
            onClick={onRefresh}
            className="cyber-btn"
            title="Refresh Ledger & Metrics"
            style={{ padding: '0.5rem', borderRadius: '8px' }}
          >
            <RefreshCw size={15} />
          </button>
        </div>
      </div>

      {/* Global Live Stats Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.75rem', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ background: 'rgba(255,255,255,0.02)', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.04)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Events</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{stats.total}</div>
        </div>
        <div style={{ background: 'rgba(16, 185, 129, 0.05)', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.15)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--neon-emerald)', textTransform: 'uppercase' }}>Accepted</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--neon-emerald)' }}>{stats.accepted}</div>
        </div>
        <div style={{ background: 'rgba(245, 158, 11, 0.05)', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(245, 158, 11, 0.15)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--neon-amber)', textTransform: 'uppercase' }}>Quarantined</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--neon-amber)' }}>{stats.quarantined}</div>
        </div>
        <div style={{ background: 'rgba(244, 63, 94, 0.05)', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(244, 63, 94, 0.15)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--neon-rose)', textTransform: 'uppercase' }}>Rejected</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--neon-rose)' }}>{stats.rejected}</div>
        </div>
        <div style={{ background: 'rgba(0, 245, 212, 0.05)', padding: '0.5rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(0, 245, 212, 0.15)' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--neon-cyan)', textTransform: 'uppercase' }}>Avg Latency</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--neon-cyan)' }}>{stats.avgLatency} ms</div>
        </div>
      </div>
    </header>
  );
}
