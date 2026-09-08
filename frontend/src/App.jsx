import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LiveAttackPanel from './components/LiveAttackPanel';
import AttackMatrix from './components/AttackMatrix';
import HashChainExplorer from './components/HashChainExplorer';
import DecisionTimeline from './components/DecisionTimeline';
import ForgeryCurveChart from './components/ForgeryCurveChart';
import QuantumStateVisualizer from './components/QuantumStateVisualizer';
import NetworkTopology from './components/NetworkTopology';
import { Shield, Zap, Database, Orbit, Network, CheckCircle, AlertTriangle } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('threats');
  const [userRole, setUserRole] = useState('auditor'); // 'standard' or 'auditor'

  // Backend state
  const [health, setHealth] = useState(null);
  const [calibration, setCalibration] = useState(null);
  const [events, setEvents] = useState([]);
  const [chainAudit, setChainAudit] = useState(null);

  // Loading states
  const [isAttacking, setIsAttacking] = useState(false);
  const [isCalibrating, setIsCalibrating] = useState(false);
  const [isVerifyingChain, setIsVerifyingChain] = useState(false);
  const [isTampering, setIsTampering] = useState(false);

  // Attack result state
  const [lastAttackResult, setLastAttackResult] = useState(null);
  const [lastTriggeredScenario, setLastTriggeredScenario] = useState(null);
  const [toast, setToast] = useState(null);

  const showToast = (msg, type = 'info') => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  // Fetch initial data
  const fetchData = async () => {
    try {
      // 1. Health
      const hRes = await fetch('/v1/health').catch(() => null);
      if (hRes?.ok) setHealth(await hRes.json());

      // 2. Calibration
      const cRes = await fetch('/v1/calibration/status').catch(() => null);
      if (cRes?.ok) setCalibration(await cRes.json());

      // 3. Ledger Events
      const eRes = await fetch('/v1/ledger/events?limit=50').catch(() => null);
      if (eRes?.ok) {
        const evts = await eRes.json();
        setEvents(evts);
      }

      // 4. Chain audit
      const chRes = await fetch('/v1/ledger/verify-chain').catch(() => null);
      if (chRes?.ok) setChainAudit(await chRes.json());
    } catch (err) {
      console.error('Data fetch error:', err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  // Compute stats
  const stats = {
    total: events.length,
    accepted: events.filter((e) => e.decision === 'ACCEPT').length,
    quarantined: events.filter((e) => e.decision === 'QUARANTINE').length,
    rejected: events.filter((e) => e.decision === 'REJECT').length,
    avgLatency: '1.8'
  };

  // Trigger attack scenario
  const handleTriggerAttack = async (scenario, disturbance) => {
    setIsAttacking(true);
    setLastTriggeredScenario(scenario);
    showToast(`Launching ${scenario} attack against API...`, 'info');

    try {
      const res = await fetch(`/v1/testbed/attack/${scenario}`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'x-role': userRole
        },
        body: JSON.stringify({ disturbance })
      });

      if (res.ok) {
        const data = await res.json();
        setLastAttackResult(data);
        showToast(
          `${scenario.toUpperCase()}: Result = ${data.actual_outcome || 'PROCESSED'} (${data.detected ? 'DETECTED' : 'UNCAUGHT'})`,
          data.actual_outcome === 'ACCEPT' ? 'success' : data.actual_outcome === 'QUARANTINE' ? 'warning' : 'error'
        );
        // Refresh ledger
        fetchData();
      } else {
        showToast(`Attack failed with HTTP ${res.status}`, 'error');
      }
    } catch (err) {
      showToast(`Network error triggering attack: ${err.message}`, 'error');
    } finally {
      setIsAttacking(false);
    }
  };

  // Run analytical calibration
  const handleCalibrate = async () => {
    setIsCalibrating(true);
    try {
      const res = await fetch('/v1/calibration/calibrate', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setCalibration((prev) => ({
          ...prev,
          policy_version: data.policy_version,
          thresholds: [data.tau_low, data.tau_high]
        }));
        showToast(`Calibrated policy to ${data.policy_version}`, 'success');
      }
    } catch (err) {
      showToast(`Calibration failed: ${err.message}`, 'error');
    } finally {
      setIsCalibrating(false);
    }
  };

  // Audit whole chain
  const handleVerifyChain = async () => {
    setIsVerifyingChain(true);
    try {
      const res = await fetch('/v1/ledger/verify-chain');
      if (res.ok) {
        const data = await res.json();
        setChainAudit(data);
        if (data.chain_valid) {
          showToast('Ledger audit complete: 100% hash chain & HMAC valid', 'success');
        } else {
          showToast('Ledger audit failed: Integrity violation detected!', 'error');
        }
      }
    } catch (err) {
      showToast(`Audit failed: ${err.message}`, 'error');
    } finally {
      setIsVerifyingChain(false);
    }
  };

  // Tamper database
  const handleTamperDb = async () => {
    setIsTampering(true);
    try {
      const res = await fetch('/v1/ledger/tamper', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        showToast(`Adversarial mutation executed on Block #${data.seq_num}. Auditing chain...`, 'warning');
        // Audit chain immediately
        handleVerifyChain();
        fetchData();
      }
    } catch (err) {
      showToast(`Tamper failed: ${err.message}`, 'error');
    } finally {
      setIsTampering(false);
    }
  };

  return (
    <div className="container">
      {/* Toast Notification Banner */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.75rem 1.25rem',
          borderRadius: '10px',
          background: toast.type === 'success' ? '#064e3b' : toast.type === 'error' ? '#881337' : toast.type === 'warning' ? '#78350f' : '#0c4a6e',
          color: '#fff',
          border: '1px solid rgba(255,255,255,0.2)',
          boxShadow: '0 8px 30px rgba(0,0,0,0.5)',
          fontFamily: 'var(--font-main)',
          fontSize: '0.85rem',
          fontWeight: 600,
          animation: 'slideIn 0.2s ease-out'
        }}>
          {toast.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
          {toast.msg}
        </div>
      )}

      {/* Global Header */}
      <Header
        health={health}
        calibration={calibration}
        userRole={userRole}
        setUserRole={setUserRole}
        onCalibrate={handleCalibrate}
        isCalibrating={isCalibrating}
        stats={stats}
        onRefresh={fetchData}
      />

      {/* Navigation Tabs */}
      <div className="glass-panel" style={{ padding: '0.25rem', marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
        <button 
          className={`nav-tab ${activeTab === 'threats' ? 'active' : ''}`}
          onClick={() => setActiveTab('threats')}
        >
          <Zap size={16} />
          Live Threat Suite & Defense Matrix
        </button>
        <button 
          className={`nav-tab ${activeTab === 'ledger' ? 'active' : ''}`}
          onClick={() => setActiveTab('ledger')}
        >
          <Database size={16} />
          Evidence Ledger & Timeline (L4)
        </button>
        <button 
          className={`nav-tab ${activeTab === 'physics' ? 'active' : ''}`}
          onClick={() => setActiveTab('physics')}
        >
          <Orbit size={16} />
          Quantum Physics & Security Bounds (L1/L2)
        </button>
        <button 
          className={`nav-tab ${activeTab === 'network' ? 'active' : ''}`}
          onClick={() => setActiveTab('network')}
        >
          <Network size={16} />
          Network Isolation Topology & Role Tiering
        </button>
      </div>

      {/* Tab 1: Live Threat Suite & Attack Matrix */}
      {activeTab === 'threats' && (
        <div>
          <LiveAttackPanel
            onTriggerAttack={handleTriggerAttack}
            isAttacking={isAttacking}
            lastAttackResult={lastAttackResult}
            userRole={userRole}
          />
          <AttackMatrix lastTriggeredScenario={lastTriggeredScenario} />
        </div>
      )}

      {/* Tab 2: Evidence Ledger & Decision Timeline */}
      {activeTab === 'ledger' && (
        <div>
          <HashChainExplorer
            events={events}
            onVerifyChain={handleVerifyChain}
            chainAuditResult={chainAudit}
            isVerifyingChain={isVerifyingChain}
            onTamperDb={handleTamperDb}
            isTampering={isTampering}
            onRefreshEvents={fetchData}
          />
          <DecisionTimeline events={events} />
        </div>
      )}

      {/* Tab 3: Quantum Physics & Security Bounds */}
      {activeTab === 'physics' && (
        <div>
          <QuantumStateVisualizer />
          <ForgeryCurveChart />
        </div>
      )}

      {/* Tab 4: Network Isolation & Role Tiering */}
      {activeTab === 'network' && (
        <div>
          <NetworkTopology />
          {/* Detailed Role Tiering Explanation */}
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: '0.5rem', color: 'var(--neon-violet)' }}>
              Role-Based Response Tiering (Active Role: {userRole === 'auditor' ? 'Auditor / Security Officer' : 'Standard Verifier (Bob)'})
            </h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '1rem' }}>
              To prevent adversaries from probing detection thresholds or profiling internal probe weights through trial-and-error reconnaissance, Q-SENTINEL v9 strictly tiers verification responses:
            </p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div style={{ background: 'rgba(56, 189, 248, 0.05)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#38bdf8', marginBottom: '0.4rem' }}>
                  Standard Verifier (e.g. Bob / Public API Consumer)
                </div>
                <ul style={{ fontSize: '0.75rem', color: 'var(--text-muted)', paddingLeft: '1.2rem', lineHeight: 1.6 }}>
                  <li>Binary ACCEPT / REJECT verdicts.</li>
                  <li>Granular probe metrics (mismatch rates, basis tomography, nonces) are <strong>redacted</strong> on REJECT.</li>
                  <li>Returns safe generic security policy notice.</li>
                </ul>
              </div>

              <div style={{ background: 'rgba(168, 85, 247, 0.05)', padding: '1rem', borderRadius: '10px', border: '1px solid rgba(168, 85, 247, 0.2)' }}>
                <div style={{ fontWeight: 700, fontSize: '0.85rem', color: '#c084fc', marginBottom: '0.4rem' }}>
                  Authorized Auditor / Security Officer (Auditor Mode)
                </div>
                <ul style={{ fontSize: '0.75rem', color: 'var(--text-muted)', paddingLeft: '1.2rem', lineHeight: 1.6 }}>
                  <li>Unredacted forensic diagnostic telemetry.</li>
                  <li>Full detector findings: `IdentityGuard`, `StatisticalProbe`, `TomographyProbe`.</li>
                  <li>Exact mismatch percentages, basis counts, and evidence block IDs for regulatory compliance.</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
