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
    : (rawThresh?.tau_low ?? 0.0101)
  const tHigh = Array.isArray(rawThresh)
    ? rawThresh[1]
    : (rawThresh?.tau_high ?? 0.0259)

  const D = result?.deviation_score !== undefined && result?.deviation_score !== null ? Number(result.deviation_score) : null
  const chi2 = result?.chi_square !== undefined && result?.chi_square !== null ? Number(result.chi_square) : null
  const decision = result?.decision ?? null

  // Geometry: 220° sweep from -110° to +110°
  // Zone 1: ACCEPT:      -110° to -35° (75°) -> Green
  // Zone 2: QUARANTINE:   -35° to +35° (70°, centered at 0° top) -> Amber
  // Zone 3: REJECT:       +35° to +110° (75°) -> Red
  const START = -110
  const LOW_ANGLE = -35
  const HIGH_ANGLE = 35
  const END = 110

  const CX = 120
  const CY = 112
  const R = 70
  const STROKE_WIDTH = 12

  // Piecewise linear needle calculation ensuring clear zone mapping
  const needleAngle = useMemo(() => {
    if (!result) return -90 // neutral vertical/standby
    if (decision === 'REJECT' || decision === 'INTEGRITY_VIOLATION' || decision === 'INTEGRITY_ALARM') {
      if (D === null) {
        // Pre-quantum or integrity intercept: point firmly into the REJECT zone
        return HIGH_ANGLE + 0.65 * (END - HIGH_ANGLE) // ~84° (deep in red REJECT zone)
      }
    }
    if (decision === 'ACCEPT' && D === null) {
      return START + 0.25 * (LOW_ANGLE - START) // ~ -91° in green ACCEPT zone
    }
    if (decision === 'SECURE') {
      // Side-channel timing oracle passed constant-time verification
      return START + 0.20 * (LOW_ANGLE - START) // Green zone
    }
    if (D !== null) {
      if (D <= tLow) {
        const frac = tLow > 0 ? Math.min(1.0, Math.max(0.0, D / tLow)) : 0
        return START + frac * (LOW_ANGLE - START)
      } else if (D <= tHigh) {
        const range = Math.max(0.001, tHigh - tLow)
        const frac = Math.min(1.0, Math.max(0.0, (D - tLow) / range))
        return LOW_ANGLE + frac * (HIGH_ANGLE - LOW_ANGLE)
      } else {
        const ceiling = Math.max(0.20, tHigh * 4.0)
        const range = Math.max(0.01, ceiling - tHigh)
        const frac = Math.min(1.0, Math.max(0.0, (D - tHigh) / range))
        return HIGH_ANGLE + frac * (END - HIGH_ANGLE)
      }
    }
    return START
  }, [D, tLow, tHigh, decision, result])

  const decisionColors = {
    ACCEPT: '#c6f135',
    SECURE: '#c6f135',
    QUARANTINE: '#F59E0B',
    REJECT: '#EF4444',
    INTEGRITY_VIOLATION: '#EF4444',
    INTEGRITY_ALARM: '#EF4444',
    null: '#8b8e97',
  }
  const activeColor = decisionColors[decision] || decisionColors[null]

  const needle = polarToXY(CX, CY, R - 10, needleAngle)
  const tickLow = polarToXY(CX, CY, R + 8, LOW_ANGLE)
  const tickHigh = polarToXY(CX, CY, R + 8, HIGH_ANGLE)
  const textLow = polarToXY(CX, CY, R + 20, LOW_ANGLE)
  const textHigh = polarToXY(CX, CY, R + 20, HIGH_ANGLE)

  return (
    <div className="glass-card p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: activeColor, boxShadow: `0 0 6px ${activeColor}` }} />
          Deviation & Decision Gauge
        </h3>
        <span className="text-[11px] font-mono text-[#8b8e97]">
          τ_low: {tLow.toFixed(4)} · τ_high: {tHigh.toFixed(4)}
        </span>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-6">
        {/* SVG Gauge */}
        <div className="flex-shrink-0 flex items-center justify-center">
          <svg viewBox="0 0 240 170" width="235" height="165" className="overflow-visible">
            <defs>
              <filter id="needleGlowFixed" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor={activeColor} floodOpacity="0.85" />
              </filter>
            </defs>

            {/* Background track */}
            <path
              d={safeArc(CX, CY, R, START, END)}
              fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={STROKE_WIDTH}
              strokeLinecap="round"
            />

            {/* Zone 1: ACCEPT (START -> LOW_ANGLE) */}
            <path
              d={safeArc(CX, CY, R, START, LOW_ANGLE)}
              fill="none" stroke="#c6f135" strokeWidth={STROKE_WIDTH}
              strokeLinecap="round" opacity="0.9"
            />

            {/* Zone 2: QUARANTINE (LOW_ANGLE -> HIGH_ANGLE) */}
            <path
              d={safeArc(CX, CY, R, LOW_ANGLE, HIGH_ANGLE)}
              fill="none" stroke="#F59E0B" strokeWidth={STROKE_WIDTH}
              opacity="0.9"
            />

            {/* Zone 3: REJECT (HIGH_ANGLE -> END) */}
            <path
              d={safeArc(CX, CY, R, HIGH_ANGLE, END)}
              fill="none" stroke="#EF4444" strokeWidth={STROKE_WIDTH}
              strokeLinecap="round" opacity="0.9"
            />

            {/* Threshold Ticks */}
            <circle cx={tickLow.x} cy={tickLow.y} r="3" fill="#c6f135" />
            <circle cx={tickHigh.x} cy={tickHigh.y} r="3" fill="#EF4444" />
            <text x={textLow.x} y={textLow.y} fill="#c6f135" fontSize="8" fontFamily="JetBrains Mono" textAnchor="middle">
              τ₁
            </text>
            <text x={textHigh.x} y={textHigh.y} fill="#EF4444" fontSize="8" fontFamily="JetBrains Mono" textAnchor="middle">
              τ₂
            </text>

            {/* Needle */}
            <line
              x1={CX} y1={CY}
              x2={needle.x} y2={needle.y}
              stroke={activeColor}
              strokeWidth="3.5"
              strokeLinecap="round"
              filter="url(#needleGlowFixed)"
              style={{ transition: 'all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1)' }}
            />
            <circle cx={CX} cy={CY} r="6" fill={activeColor}
              style={{ filter: `drop-shadow(0 0 6px ${activeColor})` }} />
            <circle cx={CX} cy={CY} r="2.5" fill="#0f172a" />

            {/* Zone legend labels (adjusted so QUARANTINE never overlaps arc) */}
            <text x="38" y="156" fill="#c6f135" fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              ACCEPT
            </text>
            <text x={CX} y="18" fill="#F59E0B" fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              QUARANTINE
            </text>
            <text x="202" y="156" fill="#EF4444" fontSize="9" fontWeight="600" textAnchor="middle" fontFamily="Plus Jakarta Sans">
              REJECT
            </text>

            {/* Center digital readout */}
            <text x={CX} y={CY + 18} textAnchor="middle" fill={activeColor}
              fontSize="16" fontWeight="bold" fontFamily="JetBrains Mono">
              {D !== null
                ? D.toFixed(4)
                : (decision === 'SECURE' ? 'SECURE' : (result?.layer_stopped === 'L3' ? 'L3 SHIELD' : (result?.layer_stopped === 'L4' || decision === 'INTEGRITY_VIOLATION' ? 'L4 ALARM' : (decision ? decision : 'STANDBY'))))}
            </text>
            <text x={CX} y={CY + 32} textAnchor="middle" fill="#8b8e97" fontSize="8" fontFamily="Plus Jakarta Sans">
              {D !== null
                ? `Deviation D (vs τ_low: ${tLow.toFixed(4)})`
                : (decision === 'SECURE' ? 'Constant-time latency protected' : (result?.intercepted_by ? `Blocked: ${result.intercepted_by}` : 'Pre-Quantum Shield Active'))}
            </text>
          </svg>
        </div>

        {/* Live Metrics Stats Panel */}
        <div className="flex flex-col gap-2 flex-1 w-full bg-black/20 rounded-xl p-3.5 border border-white/5 font-mono">
          <Stat label="Decision Verdict" value={decision ?? 'STANDBY'} color={activeColor} bold />
          <Stat
            label="Deviation Score (D)"
            value={D !== null ? D.toFixed(4) : (result?.layer_stopped ? `${result.layer_stopped} Intercept` : (decision === 'SECURE' ? '0.0000 (Protected)' : '0.0000'))}
            mono
            color={activeColor}
          />
          <Stat label="χ² Metric" value={chi2 !== null ? chi2.toFixed(2) : (decision === 'SECURE' ? '0.00' : '—')} mono />
          <Stat label="τ_low Threshold (Accept)" value={tLow.toFixed(4)} mono color="#c6f135" />
          <Stat label="τ_high Threshold (Quarantine)" value={tHigh.toFixed(4)} mono color="#EF4444" />
          <Stat
            label="Policy Interpretation"
            value={
              D === null
                ? (decision === 'SECURE' ? 'Constant-time verification passed' : (result?.layer_stopped ? `Intercepted at ${result.layer_stopped} (${result.intercepted_by || 'Guard'})` : 'Awaiting trial execution'))
                : D <= tLow ? 'Authentic Signature (D ≤ τ_low)'
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
