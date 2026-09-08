import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine
} from 'recharts'

// Calibrated reference baseline for the six-state |+⟩ QDS protocol:
// X-basis projection is 1.0 (|0⟩/|+⟩ eigenstate), Y and Z are unbiased 0.5.
const PROTOCOL_BASELINE = { X: 1.0, Y: 0.5, Z: 0.5 }

function getBasisProb(obj, key, fallback) {
  if (!obj) return fallback
  if (typeof obj[key] === 'number') return obj[key]
  if (obj[key] && typeof obj[key] === 'object') {
    if (obj[key]['0'] !== undefined) return Number(obj[key]['0'])
    if (obj[key]['1'] !== undefined) return 1.0 - Number(obj[key]['1'])
  }
  return fallback
}

function buildChartData(basisProbs, baseline) {
  const pX = getBasisProb(basisProbs, 'X', 1.0)
  const pY = getBasisProb(basisProbs, 'Y', 0.5)
  const pZ = getBasisProb(basisProbs, 'Z', 0.5)

  const bX = getBasisProb(baseline, 'X', PROTOCOL_BASELINE.X)
  const bY = getBasisProb(baseline, 'Y', PROTOCOL_BASELINE.Y)
  const bZ = getBasisProb(baseline, 'Z', PROTOCOL_BASELINE.Z)

  return [
    {
      basis: 'Pauli X (|0⟩)',
      empirical: +pX.toFixed(4),
      baseline: +bX.toFixed(4),
      delta: +(pX - bX).toFixed(4),
      name: 'Pauli X (Phase / Bit)',
      ideal: bX
    },
    {
      basis: 'Pauli Y (|0⟩)',
      empirical: +pY.toFixed(4),
      baseline: +bY.toFixed(4),
      delta: +(pY - bY).toFixed(4),
      name: 'Pauli Y (Circular)',
      ideal: bY
    },
    {
      basis: 'Pauli Z (|0⟩)',
      empirical: +pZ.toFixed(4),
      baseline: +bZ.toFixed(4),
      delta: +(pZ - bZ).toFixed(4),
      name: 'Pauli Z (Computational)',
      ideal: bZ
    },
  ]
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const emp = payload.find(p => p.dataKey === 'empirical')
  const base = payload.find(p => p.dataKey === 'baseline')
  const delta = emp && base ? (emp.value - base.value).toFixed(4) : null
  const absDelta = Math.abs(+delta)

  return (
    <div className="glass-card px-3.5 py-2.5 text-xs font-mono border border-cyan-500/30 bg-slate-900/90 shadow-xl">
      <p className="text-white font-bold mb-1.5 flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full bg-cyan-400" />
        {label}
      </p>
      {emp && <p className="text-cyan-300">Empirical p̂ (|0⟩): <span className="font-bold">{emp.value}</span></p>}
      {base && <p className="text-slate-400">Baseline μ (|0⟩): {base.value}</p>}
      {delta !== null && (
        <p className={`mt-1 font-semibold ${absDelta > 0.15 ? 'text-rose-400' : absDelta > 0.05 ? 'text-amber-400' : 'text-emerald-400'}`}>
          Deviation Δ = {delta > 0 ? `+${delta}` : delta}
        </p>
      )}
    </div>
  )
}

export default function PauliBarChart({ result, calibration }) {
  const data = buildChartData(result?.basis_probabilities, calibration?.baseline)
  const xItem = data[0]
  const xDeviation = Math.abs(xItem.delta)
  const isXDisturbed = xDeviation > 0.05

  return (
    <div className="glass-card p-5 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="text-sm font-semibold text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#c6f135] shadow-[0_0_6px_#c6f135]" />
              Pauli Measurement Distributions (p̂ vs μ)
            </h3>
            <p className="text-[11px] text-[#8b8e97] font-mono mt-0.5">
              Reference State: |+⟩ (|0⟩ probability per Pauli observable)
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-2 rounded-sm bg-[#c6f135]" />
              <span className="text-slate-300 font-mono text-[11px]">p̂ Empirical</span>
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-2 rounded-sm bg-slate-600" />
              <span className="text-[#8b8e97] font-mono text-[11px]">μ Baseline</span>
            </span>
          </div>
        </div>

        <div className="h-[210px] w-full mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} barCategoryGap="25%" barGap={6}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis
                dataKey="basis"
                tick={{ fill: '#cbd5e1', fontSize: 11, fontFamily: 'Plus Jakarta Sans', fontWeight: 500 }}
                axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
                tickLine={false}
              />
              <YAxis
                domain={[0, 1.05]}
                ticks={[0.0, 0.25, 0.5, 0.75, 1.0]}
                tick={{ fill: '#8b8e97', fontSize: 11, fontFamily: 'JetBrains Mono' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={v => v.toFixed(2)}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
              <ReferenceLine y={1.0} stroke="#c6f135" strokeDasharray="3 3" opacity={0.5} />
              <ReferenceLine y={0.5} stroke="#8b8e97" strokeDasharray="3 3" opacity={0.5} />
              <Bar dataKey="empirical" fill="#c6f135" radius={[4, 4, 0, 0]} maxBarSize={36} fillOpacity={0.9} />
              <Bar dataKey="baseline" fill="#475569" radius={[4, 4, 0, 0]} maxBarSize={36} fillOpacity={0.65} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Real-time Tomography Analysis Pill */}
      <div className="mt-3 pt-3 border-t border-white/5 grid grid-cols-3 gap-2 text-center font-mono">
        <div className="bg-white/[0.02] rounded-lg p-2 border border-white/5">
          <span className="text-[10px] text-[#8b8e97] block uppercase">Pauli X Observ.</span>
          <span className={`text-xs font-bold ${isXDisturbed ? 'text-amber-400' : 'text-[#c6f135]'}`}>
            {(xItem.empirical * 100).toFixed(1)}%
          </span>
          <span className="text-[9px] text-[#8b8e97] block">
            {isXDisturbed ? `Δ ${(xItem.delta * 100).toFixed(1)}%` : 'Aligned'}
          </span>
        </div>
        <div className="bg-white/[0.02] rounded-lg p-2 border border-white/5">
          <span className="text-[10px] text-[#8b8e97] block uppercase">Pauli Y Observ.</span>
          <span className="text-xs font-bold text-slate-200">
            {(data[1].empirical * 100).toFixed(1)}%
          </span>
          <span className="text-[9px] text-[#8b8e97] block">
            Δ {(data[1].delta * 100).toFixed(1)}%
          </span>
        </div>
        <div className="bg-white/[0.02] rounded-lg p-2 border border-white/5">
          <span className="text-[10px] text-[#8b8e97] block uppercase">Pauli Z Observ.</span>
          <span className="text-xs font-bold text-slate-200">
            {(data[2].empirical * 100).toFixed(1)}%
          </span>
          <span className="text-[9px] text-[#8b8e97] block">
            Δ {(data[2].delta * 100).toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  )
}
