import { useState, useEffect, useCallback } from 'react'
import ShootingStarsBackground from './components/ShootingStarsBackground'
import Header from './components/Header'
import AttackMatrix from './components/AttackMatrix'
import PipelineTracker from './components/PipelineTracker'
import PauliBarChart from './components/PauliBarChart'
import DeviationGauge from './components/DeviationGauge'
import LedgerInspector from './components/LedgerInspector'
import { useHealthPoller } from './hooks/useHealthPoller'
import { runScenario, getCalibrationStatus, getLedgerEvents } from './services/api'
import { Activity, Layers, BookOpen } from 'lucide-react'

const TABS = [
  { id: 'control', label: 'Control Room', icon: Activity },
  { id: 'telemetry', label: 'Telemetry', icon: Layers },
  { id: 'ledger', label: 'Evidence Ledger', icon: BookOpen },
]

export default function App() {
  const healthStatus = useHealthPoller(3000)
  const [activeTab, setActiveTab] = useState('control')
  const [activeScenarioKey, setActiveScenarioKey] = useState(null)
  const [lastResult, setLastResult] = useState(null)
  const [calibration, setCalibration] = useState(null)
  const [ledgerEvents, setLedgerEvents] = useState([])

  // Load calibration on mount
  useEffect(() => {
    getCalibrationStatus().then(setCalibration)
  }, [])

  // Load ledger events on mount and when tab changes to ledger
  const refreshLedger = useCallback(() => {
    getLedgerEvents().then(setLedgerEvents)
  }, [])

  useEffect(() => {
    refreshLedger()
  }, [refreshLedger])

  useEffect(() => {
    if (activeTab === 'ledger') refreshLedger()
  }, [activeTab, refreshLedger])

  const handleRunScenario = async (scenario) => {
    setActiveScenarioKey(scenario.key)
    setActiveTab('control')

    const result = await runScenario(scenario.key, scenario.payload)
    setLastResult(result)

    // Auto-switch to telemetry to show analytics
    setTimeout(() => setActiveTab('telemetry'), 300)

    // Refresh ledger in background
    getLedgerEvents().then(setLedgerEvents)
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #07090e 0%, #0d1117 50%, #070b12 100%)' }}>
      <ShootingStarsBackground />

      <div className="relative z-10 max-w-screen-2xl mx-auto">

        {/* Header */}
        <Header healthStatus={healthStatus} />

        {/* Tab Navigation */}
        <nav className="px-6 mb-6">
          <div className="inline-flex gap-1 p-1 rounded-xl bg-slate-900/60 border border-white/8 backdrop-blur">
            {TABS.map(tab => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200
                    ${isActive
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 shadow-lg shadow-cyan-500/10'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'
                    }`}
                >
                  <Icon size={14} />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </nav>

        {/* Tab Content */}
        {activeTab === 'control' && (
          <div className="animate-fade-in">
            <AttackMatrix
              onRun={handleRunScenario}
              activeKey={activeScenarioKey}
              lastResult={lastResult}
            />

            {/* Quick result banner */}
            {lastResult && (
              <div className="px-6 mb-4">
                <div className={`glass-card px-5 py-3 flex flex-wrap items-center gap-4 animate-slide-in
                  ${lastResult.decision === 'ACCEPT'
                    ? 'border-emerald-500/30'
                    : lastResult.decision === 'QUARANTINE'
                    ? 'border-amber-500/30'
                    : 'border-rose-500/30'
                  }`}>
                  <span className="text-slate-400 text-xs font-mono">Last Result:</span>
                  <span className={`text-sm font-black
                    ${lastResult.decision === 'ACCEPT' ? 'text-emerald-400'
                    : lastResult.decision === 'QUARANTINE' ? 'text-amber-400'
                    : 'text-rose-400'}`}>
                    {lastResult.decision}
                  </span>
                  <span className="text-slate-500 text-xs font-mono">{lastResult.reason}</span>
                  {lastResult.latency_ms && (
                    <span className="text-slate-500 text-xs font-mono ml-auto">
                      {Math.round(lastResult.latency_ms)}ms · {lastResult._mock ? 'MOCK' : 'LIVE'}
                    </span>
                  )}
                  <button
                    onClick={() => setActiveTab('telemetry')}
                    className="text-cyan-400 text-xs hover:text-cyan-300 underline underline-offset-2"
                  >
                    View Telemetry →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'telemetry' && (
          <div className="px-6 pb-8 space-y-4 animate-fade-in">
            {/* Pipeline Tracker */}
            <PipelineTracker result={lastResult} />

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <PauliBarChart result={lastResult} calibration={calibration} />
              <DeviationGauge result={lastResult} calibration={calibration} />
            </div>

            {/* Calibration info card */}
            {calibration && (
              <div className="glass-card px-5 py-4 grid grid-cols-2 sm:grid-cols-4 gap-4">
                {[
                  { label: 'Baseline Version', value: calibration.baseline_version },
                  { label: 'Policy Version', value: calibration.policy_version },
                  { label: 'T_low', value: (calibration.thresholds?.tau_low ?? (Array.isArray(calibration.thresholds) ? calibration.thresholds[0] : 0.05))?.toFixed(4) },
                  { label: 'T_high', value: (calibration.thresholds?.tau_high ?? (Array.isArray(calibration.thresholds) ? calibration.thresholds[1] : 0.15))?.toFixed(4) },
                ].map(item => (
                  <div key={item.label} className="flex flex-col gap-1">
                    <span className="text-slate-500 text-xs">{item.label}</span>
                    <span className="text-slate-200 text-sm font-mono font-semibold">{item.value ?? '—'}</span>
                  </div>
                ))}
              </div>
            )}

            {!lastResult && (
              <div className="glass-card py-16 text-center text-slate-600 font-mono text-sm">
                No telemetry yet — go to Control Room and run a scenario.
              </div>
            )}
          </div>
        )}

        {activeTab === 'ledger' && (
          <div className="animate-fade-in">
            <LedgerInspector events={ledgerEvents} onRefresh={refreshLedger} />
          </div>
        )}
      </div>
    </div>
  )
}
