import { useState, useEffect, useCallback } from 'react'
import ShootingStarsBackground from './components/ShootingStarsBackground'
import Header from './components/Header'
import AttackMatrix from './components/AttackMatrix'
import PipelineTracker from './components/PipelineTracker'
import PauliBarChart from './components/PauliBarChart'
import DeviationGauge from './components/DeviationGauge'
import LedgerInspector from './components/LedgerInspector'
import { runScenario, getCalibrationStatus, getLedgerEvents } from './services/api'
import { Activity, Layers, BookOpen } from 'lucide-react'

const TABS = [
  { id: 'control', label: 'Control Room', icon: Activity },
  { id: 'telemetry', label: 'Telemetry', icon: Layers },
  { id: 'ledger', label: 'Evidence Ledger', icon: BookOpen },
]

export default function App() {
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
    <div className="min-h-screen" style={{ backgroundColor: '#090a0d' }}>
      <ShootingStarsBackground />

      <div className="relative z-10 max-w-screen-2xl mx-auto">

        {/* Header */}
        <Header />

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
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs tracking-wider uppercase font-medium transition-all duration-200
                    ${isActive
                      ? 'bg-[#c6f135]/15 text-[#c6f135] border border-[#c6f135]/35 shadow-lg shadow-[#c6f135]/5'
                      : 'text-[#8b8e97] hover:text-white hover:bg-white/5'
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
