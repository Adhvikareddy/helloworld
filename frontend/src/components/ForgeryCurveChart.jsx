import React, { useState } from 'react';
import { TrendingDown, Info, Sliders } from 'lucide-react';

export default function ForgeryCurveChart() {
  const [sa, setSa] = useState(0.05);
  const [activeL, setActiveL] = useState(300);

  // Compute KL divergence: D(s_a || p_err) where p_err = 1 - p_opt = 1 - 0.7887 = 0.2113
  const pErr = 0.2113;
  const computePForge = (L, s) => {
    if (s >= pErr) return 1.0;
    const kl = s * Math.log2(s / pErr) + (1 - s) * Math.log2((1 - s) / (1 - pErr));
    const exponent = -L * kl;
    return Math.pow(2, exponent);
  };

  const lengths = [50, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000];
  const dataPoints = lengths.map((L) => {
    const p = computePForge(L, sa);
    return { L, p, logP: Math.log10(Math.max(p, 1e-18)) };
  });

  const currentPForge = computePForge(activeL, sa);

  // SVG Chart Geometry
  const width = 680;
  const height = 260;
  const padding = { top: 25, right: 30, bottom: 40, left: 65 };
  const graphWidth = width - padding.left - padding.right;
  const graphHeight = height - padding.top - padding.bottom;

  // Scale mappings (X: 50 to 1000, Y: 0 to -18 log10)
  const minLog = -18;
  const maxLog = 0;
  const getX = (L) => padding.left + ((L - 50) / (1000 - 50)) * graphWidth;
  const getY = (logP) => padding.top + ((maxLog - logP) / (maxLog - minLog)) * graphHeight;

  const pointsString = dataPoints
    .map((pt) => `${getX(pt.L)},${getY(pt.logP)}`)
    .join(' ');

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <TrendingDown size={18} color="var(--neon-cyan)" />
            Quantum Forgery Security Bound Curve (P_forge vs L)
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Information-theoretic security proof: probability of an adversary successfully forging without detection decays exponentially with key length $L$.
          </p>
        </div>

        {/* sa Threshold Slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', background: 'rgba(0,0,0,0.3)', padding: '0.4rem 0.8rem', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <Sliders size={14} color="var(--neon-cyan)" />
          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Acceptance Threshold ($s_a$):</span>
          <input 
            type="range" 
            min="0.01" 
            max="0.10" 
            step="0.005"
            value={sa}
            onChange={(e) => setSa(parseFloat(e.target.value))}
            style={{ width: '90px', accentColor: 'var(--neon-cyan)', cursor: 'pointer' }}
          />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600, color: 'var(--neon-cyan)', minWidth: '35px' }}>
            {sa.toFixed(3)}
          </span>
        </div>
      </div>

      {/* SVG Interactive Chart */}
      <div style={{ overflowX: 'auto', background: 'rgba(7, 12, 22, 0.7)', borderRadius: '12px', padding: '0.75rem', border: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', display: 'block' }}>
          {/* Grid lines */}
          {[-3, -6, -9, -12, -15, -18].map((logVal) => (
            <g key={logVal}>
              <line
                x1={padding.left}
                y1={getY(logVal)}
                x2={width - padding.right}
                y2={getY(logVal)}
                stroke="rgba(255,255,255,0.06)"
                strokeDasharray="4 4"
              />
              <text
                x={padding.left - 8}
                y={getY(logVal) + 4}
                fill="var(--text-muted)"
                fontSize="10"
                fontFamily="var(--font-mono)"
                textAnchor="end"
              >
                10^{logVal}
              </text>
            </g>
          ))}

          {/* X Axis Ticks */}
          {[100, 300, 500, 700, 900].map((lVal) => (
            <g key={lVal}>
              <line
                x1={getX(lVal)}
                y1={padding.top}
                x2={getX(lVal)}
                y2={height - padding.bottom}
                stroke="rgba(255,255,255,0.04)"
              />
              <text
                x={getX(lVal)}
                y={height - padding.bottom + 18}
                fill="var(--text-muted)"
                fontSize="10"
                fontFamily="var(--font-mono)"
                textAnchor="middle"
              >
                L={lVal}
              </text>
            </g>
          ))}

          {/* Area under curve */}
          <polygon
            points={`${getX(50)},${height - padding.bottom} ${pointsString} ${getX(1000)},${height - padding.bottom}`}
            fill="url(#forgeryGrad)"
            opacity="0.3"
          />

          {/* Curve Line */}
          <polyline
            points={pointsString}
            fill="none"
            stroke="var(--neon-cyan)"
            strokeWidth="3"
            style={{ filter: 'drop-shadow(0 0 8px rgba(0,245,212,0.6))' }}
          />

          {/* Gradient Definition */}
          <defs>
            <linearGradient id="forgeryGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="var(--neon-cyan)" stopOpacity="0.4" />
              <stop offset="100%" stopColor="var(--neon-cyan)" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Interactive Marker at activeL */}
          <g>
            <line
              x1={getX(activeL)}
              y1={padding.top}
              x2={getX(activeL)}
              y2={height - padding.bottom}
              stroke="var(--neon-violet)"
              strokeWidth="2"
              strokeDasharray="3 3"
            />
            <circle
              cx={getX(activeL)}
              cy={getY(Math.log10(Math.max(currentPForge, 1e-18)))}
              r="6"
              fill="var(--neon-violet)"
              stroke="#fff"
              strokeWidth="2"
              style={{ filter: 'drop-shadow(0 0 8px var(--neon-violet))' }}
            />
          </g>
        </svg>
      </div>

      {/* Key Metric Summary Callout */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,0,0,0.3)', padding: '0.85rem 1.25rem', borderRadius: '10px', border: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Info size={16} color="var(--neon-cyan)" />
          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Selected Session Length: <strong>L = {activeL}</strong> qubits
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Theoretical P_forge bound: </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--neon-cyan)', fontSize: '0.95rem' }}>
              {currentPForge < 1e-12 ? '< 1.00e-12 (Unforgeable)' : currentPForge.toExponential(2)}
            </span>
          </div>

          <div style={{ display: 'flex', gap: '0.35rem' }}>
            {[100, 300, 500, 1000].map((presetL) => (
              <button
                key={presetL}
                onClick={() => setActiveL(presetL)}
                style={{
                  background: activeL === presetL ? 'rgba(0, 245, 212, 0.2)' : 'rgba(255,255,255,0.05)',
                  color: activeL === presetL ? 'var(--neon-cyan)' : 'var(--text-muted)',
                  border: activeL === presetL ? '1px solid var(--neon-cyan)' : '1px solid transparent',
                  borderRadius: '5px',
                  padding: '2px 8px',
                  fontSize: '0.7rem',
                  fontFamily: 'var(--font-mono)',
                  cursor: 'pointer'
                }}
              >
                {presetL}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
