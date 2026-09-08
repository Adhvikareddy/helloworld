import React, { useState } from 'react';
import { Eye, Shield, RotateCw, Orbit } from 'lucide-react';

export default function QuantumStateVisualizer() {
  const [selectedBasis, setSelectedBasis] = useState('Z');
  const [rotationAngle, setRotationAngle] = useState(0);

  const basisStates = {
    Z: [
      { name: '|0⟩', basis: 'Z', vector: [0, -75], color: '#00f5d4', label: 'Comp 0 (North Pole)' },
      { name: '|1⟩', basis: 'Z', vector: [0, 75], color: '#38bdf8', label: 'Comp 1 (South Pole)' }
    ],
    X: [
      { name: '|+⟩', basis: 'X', vector: [75, 0], color: '#10b981', label: 'Diagonal +' },
      { name: '|-⟩', basis: 'X', vector: [-75, 0], color: '#a855f7', label: 'Diagonal -' }
    ],
    Y: [
      { name: '|+i⟩', basis: 'Y', vector: [52, -52], color: '#f59e0b', label: 'Circular +i' },
      { name: '|-i⟩', basis: 'Y', vector: [-52, 52], color: '#f43f5e', label: 'Circular -i' }
    ]
  };

  const activeStates = basisStates[selectedBasis];

  // Rotate coordinates based on disturbance angle
  const rad = (rotationAngle * Math.PI) / 180;
  const rotatedVector = (vec) => {
    const x = vec[0] * Math.cos(rad) - vec[1] * Math.sin(rad);
    const y = vec[0] * Math.sin(rad) + vec[1] * Math.cos(rad);
    return [x, y];
  };

  return (
    <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '0.75rem' }}>
        <div>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Orbit size={18} color="var(--neon-cyan)" />
            Six-State Quantum Encoding & Bloch Sphere Projection
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Alice prepares mutually unbiased quantum states in X, Y, Z bases. Channel noise rotates the state vector away from the ideal eigenvector.
          </p>
        </div>

        {/* Basis Selector Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: 'rgba(0,0,0,0.3)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          {['Z', 'X', 'Y'].map((b) => (
            <button
              key={b}
              onClick={() => setSelectedBasis(b)}
              style={{
                background: selectedBasis === b ? 'rgba(0, 245, 212, 0.2)' : 'transparent',
                color: selectedBasis === b ? 'var(--neon-cyan)' : 'var(--text-muted)',
                border: selectedBasis === b ? '1px solid var(--neon-cyan)' : 'none',
                borderRadius: '6px',
                padding: '0.3rem 0.75rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {b} Basis
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', alignItems: 'center' }}>
        {/* Animated Bloch 2D Projection Sphere */}
        <div style={{ background: 'rgba(7, 12, 22, 0.8)', borderRadius: '14px', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid var(--border-subtle)' }}>
          <svg viewBox="-110 -110 220 220" style={{ width: '220px', height: '220px' }}>
            {/* Outer Sphere Circle */}
            <circle cx="0" cy="0" r="85" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="1.5" strokeDasharray="3 3" />
            <circle cx="0" cy="0" r="85" fill="none" stroke="rgba(0, 245, 212, 0.15)" strokeWidth="1" />
            
            {/* Equator Ellipse */}
            <ellipse cx="0" cy="0" rx="85" ry="30" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />

            {/* Coordinate Axes */}
            <line x1="0" y1="-95" x2="0" y2="95" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
            <line x1="-95" y1="0" x2="95" y2="0" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
            <text x="0" y="-100" fill="var(--text-muted)" fontSize="9" textAnchor="middle">|0⟩ (Z+)</text>
            <text x="0" y="106" fill="var(--text-muted)" fontSize="9" textAnchor="middle">|1⟩ (Z-)</text>
            <text x="100" y="3" fill="var(--text-muted)" fontSize="9" textAnchor="start">|+⟩ (X+)</text>
            <text x="-100" y="3" fill="var(--text-muted)" fontSize="9" textAnchor="end">|-⟩ (X-)</text>

            {/* Active Basis State Vectors with Disturbance Rotation */}
            {activeStates.map((st, idx) => {
              const [rx, ry] = rotatedVector(st.vector);
              return (
                <g key={idx}>
                  {/* Arrow vector */}
                  <line 
                    x1="0" 
                    y1="0" 
                    x2={rx} 
                    y2={ry} 
                    stroke={st.color} 
                    strokeWidth="3"
                    style={{ filter: `drop-shadow(0 0 6px ${st.color})` }}
                  />
                  {/* State point */}
                  <circle cx={rx} cy={ry} r="5" fill={st.color} stroke="#fff" strokeWidth="1.5" />
                  <text 
                    x={rx * 1.25} 
                    y={ry * 1.25 + 4} 
                    fill={st.color} 
                    fontSize="11" 
                    fontWeight="bold" 
                    fontFamily="var(--font-mono)"
                    textAnchor="middle"
                  >
                    {st.name}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Interactive Controls & State Details */}
        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.75rem' }}>
            Current Basis: <span style={{ color: 'var(--neon-cyan)', fontFamily: 'var(--font-mono)' }}>{selectedBasis}</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.25rem' }}>
            {activeStates.map((st, idx) => (
              <div 
                key={idx}
                style={{ 
                  background: 'rgba(255,255,255,0.02)', 
                  padding: '0.6rem 0.85rem', 
                  borderRadius: '8px', 
                  border: `1px solid ${st.color}30`,
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'space-between'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: st.color }}>
                    {st.name}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{st.label}</span>
                </div>
                <span className="code-val" style={{ fontSize: '0.7rem' }}>Basis {selectedBasis}</span>
              </div>
            ))}
          </div>

          {/* Interactive Channel Rotation Slider */}
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '0.85rem 1rem', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <RotateCw size={12} />
                Simulate Coherent Channel Rotation (θ):
              </span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', fontWeight: 600, color: rotationAngle > 0 ? 'var(--neon-amber)' : 'var(--neon-cyan)' }}>
                {rotationAngle}°
              </span>
            </div>
            <input 
              type="range"
              min="0"
              max="90"
              step="5"
              value={rotationAngle}
              onChange={(e) => setRotationAngle(parseInt(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--neon-cyan)', cursor: 'pointer' }}
            />
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
              {rotationAngle === 0 
                ? 'Clean channel: state remains on ideal measurement axis (0% bit error rate).' 
                : `Rotated by ${rotationAngle}°: causes ~${((1 - Math.cos((rotationAngle * Math.PI)/180))/2 * 100).toFixed(1)}% error rate on orthogonal bases, caught by TomographyProbe.`}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
