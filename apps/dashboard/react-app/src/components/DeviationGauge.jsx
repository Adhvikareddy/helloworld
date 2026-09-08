import { useMemo } from 'react'

function polarToXY(cx, cy, r, angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
}

function safeArc(cx, cy, r, startDeg, endDeg) {
  if (endDeg - startDeg < 0.5) return ''
  const s = polarToXY(cx, cy, r, startDeg)
  const e = polarToXY(cx, cy, r, endDeg)
  const large = endDeg - startDeg > 180 ? 1 : 0
  return `M ${s.x.toFixed(2)} ${s.y.toFixed(2)} A ${r} ${r} 0 ${large} 1 ${e.x.toFixed(2)} ${e.y.toFixed(2)}`
}

export default function DeviationGauge({ result, calibration }) {
  // Extract normalized thresholds
  const rawThresh = calibration?.thresholds
  const tLow = Array.isArray(rawThresh)
    ? rawThresh[0]
    : (rawThresh?.tau_low ?? 0.05)
  const tHigh = Array.isArray(rawThresh)
    ? rawThresh[1]
    : (rawThresh?.tau_high ?? 0.15)

  const D = result?.deviation_score ?? null
  const chi2 = result?.chi_square ?? null
  const decision = result?.decision ?? null

  // Geometry: 220° sweep from -110° to +110°
  const START = -110
  const END = 110
  const TOTAL = 220
  const CX = 120
  const CY = 105
  const R = 76
  const STROKE_WIDTH = 14

  // Dynamic scale ceiling so thresholds and deviations fit harmoniously
  const maxD = useMemo(() => {
    const candidateMax = Math.max(0.20, (tHigh || 0.15) * 1.5, ((D ?? 0) * 1.25))
    return Math.min(1.0, candidateMax)
  }, [tHigh, D])

  const toAngle = (val) => {
    if (val === null || val === undefined) return START
    const frac = Math.min(1.0, Math.max(0.0, val / maxD))
    return START + frac * TOTAL
  }

  const lowAngle = Math.min(END - 10, Math.max(START + 10, toAngle(tLow)))
  const highAngle = Math.min(END - 2, Math.max(lowAngle + 5, toAngle(tHigh)))
  const needleAngle = D !== null ? toAngle(D) : START

  const decisionColors = {
    ACCEPT: '#10B981',
    QUARANTINE: '#F59E0B',
    REJECT: '#EF4444',
    INTEGRITY_ALARM: '#a855f7',
    null: '#64748b',
  }
  const activeColor = decisionColors[decision] || decisionColors[null]

  const needle = polarToXY(CX, CY, R - 12, needleAngle)
  const tickLow = polarToXY(CX, CY, R + 9, lowAngle)
  const tickHigh = polarToXY(CX, CY, R + 9, highAngle)

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: activeColor }} />
          Deviation & Decision Gauge
        </h3>
        <span className="text-[11px] font-mono text-slate-400">
          Scale max: {maxD.toFixed(3)}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* SVG Gauge */}
        <div className="flex-shrink-0 flex items-center justify-center">
          <svg viewBox="0 0 240 160" width="230" height="154" className="overflow-visible">
            <defs>
              <filter id="needleGlow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor={activeColor} floodOpacity="0.8" />
              </filter>
            </defs>

            {/* Background track */}
            <path
              d={safeArc(CX, CY, R, START, END)}
              fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={STROKE_WIDTH}
              strokeLinecap="round"
            />

            {/* Zone 1: ACCEPT (START -> lowAngle) */}
            <path
              d={safeArc(CX, CY, R, START, lowAngle)}
              fill="none" stroke="#10B981" strokeWidth={STROKE_WIDTH}
              strokeLinecap="round" opacity="0.85"
            />

            {/* Zone 2: QUARANTINE (lowAngle -> highAngle) */}
            <path
              d={safeArc(CX, CY, R, lowAngle, highAngle)}
              fill="none" stroke="#F59E0B" strokeWidth={STROKE_WIDTH}
              opacity="0.85"
            />

            {/* Zone 3: REJECT (highAngle -> END) */}
            <path
              d={safeArc(CX, CY, R, highAngle, END)}
              fill="none" stroke="#EF4444" strokeWidth={STROKE_WIDTH}
              strokeLinecap="round" opacity="0.85"
            />

            {/* T_low indicator dot */}
            <circle cx={tickLow.x} cy={tickLow.y} r="2.5" fill="#10B981" />
            {/* T_high indicator dot */}
            <circle cx={tickHigh.x} cy={tickHigh.y} r="2.5" fill="#EF4444" />

            {/* Needle */}
            <line
              x1={CX} y1={CY}
              x2={needle.x} y2={needle.y}
              stroke={activeColor}
              strokeWidth="3"
              strokeLinecap="round"
              filter="url(#needleGlow)"
              style={{ transition: 'all 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
            />
            <circle cx={CX} cy={CY} r="6" fill={activeColor}
              style={{ filter: `drop-shadow(0 0 6px ${activeColor})` }} />
            <circle cx={CX} cy={CY} r="2.5" fill="#0f172a" />

            {/* Zone legend labels */}
            <text x="32" y="146" fill="#10B981" fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Inter">
              ACCEPT
            </text>
            <text x="120" y="24" fill="#F59E0B" fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Inter">
              QUARANTINE
            </text>
            <text x="208" y="146" fill="#EF4444" fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Inter">
              REJECT
            </text>

            {/* Center digital readout */}
            <text x={CX} y={CY + 20} textAnchor="middle" fill={activeColor}
              fontSize="16" fontWeight="bold" fontFamily="JetBrains Mono">
              {D !== null ? D.toFixed(5) : (decision ? 'L3 / L1 BLOCK' : '0.00000')}
            </text>
            <text x={CX} y={CY + 34} textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="Inter">
              {D !== null ? `Deviation D (vs τ_low: ${tLow.toFixed(4)})` : 'Quantum State Metric'}
            </text>
          </svg>
        </div>

        {/* Live Metrics Stats Panel */}
        <div className="flex flex-col gap-2.5 flex-1 w-full bg-black/20 rounded-xl p-3.5 border border-white/5">
          <Stat label="Decision Verdict" value={decision ?? 'STANDBY'} color={activeColor} bold />
          <Stat label="Deviation Score (D)" value={D !== null ? D.toFixed(5) : (decision ? 'Pre-quantum reject' : '0.00000')} mono color={activeColor} />
          <Stat label="χ² Metric" value={chi2 !== null ? chi2.toFixed(2) : '—'} mono />
          <Stat label="τ_low Threshold (Accept)" value={tLow.toFixed(4)} mono color="#10B981" />
          <Stat label="τ_high Threshold (Quarantine)" value={tHigh.toFixed(4)} mono color="#EF4444" />
          <Stat
            label="Policy Interpretation"
            value={
              D === null ? 'Pre-Quantum Check'
              : D <= tLow ? 'Honest Signature (D ≤ τ_low)'
              : D <= tHigh ? 'Channel Anomaly (τ_low < D ≤ τ_high)'
              : 'Quantum Disturbance / Attack (D > τ_high)'
            }
            color={activeColor}
          />
        </div>
      </div>
    </div>
  )
}

function Stat({ label, value, mono, color, bold }) {
  return (
    <div className="flex items-center justify-between py-1 border-b border-white/5 last:border-0">
      <span className="text-slate-400 text-xs">{label}</span>
      <span
        className={`text-xs ${bold ? 'font-black' : 'font-semibold'} ${mono ? 'font-mono' : ''}`}
        style={{ color: color || '#e2e8f0' }}
      >
        {value}
      </span>
    </div>
  )
}
