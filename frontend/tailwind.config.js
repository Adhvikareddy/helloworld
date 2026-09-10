/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'quantum-cyan': '#00F2FE',
        'quantum-blue': '#4FACFE',
        'neon-emerald': '#10B981',
        'warn-amber': '#F59E0B',
        'crimson-red': '#EF4444',
        'obsidian': '#07090e',
        'charcoal': '#0d1117',
        'glass-border': 'rgba(255,255,255,0.08)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-green': 'glowGreen 2s ease-in-out infinite alternate',
        'glow-red': 'glowRed 2s ease-in-out infinite alternate',
        'glow-cyan': 'glowCyan 2s ease-in-out infinite alternate',
        'slide-in': 'slideIn 0.4s ease-out',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        glowGreen: {
          '0%': { boxShadow: '0 0 5px rgba(16,185,129,0.4)' },
          '100%': { boxShadow: '0 0 20px rgba(16,185,129,0.8), 0 0 40px rgba(16,185,129,0.3)' },
        },
        glowRed: {
          '0%': { boxShadow: '0 0 5px rgba(239,68,68,0.4)' },
          '100%': { boxShadow: '0 0 20px rgba(239,68,68,0.8), 0 0 40px rgba(239,68,68,0.3)' },
        },
        glowCyan: {
          '0%': { boxShadow: '0 0 5px rgba(0,242,254,0.4)' },
          '100%': { boxShadow: '0 0 20px rgba(0,242,254,0.8), 0 0 40px rgba(0,242,254,0.3)' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
