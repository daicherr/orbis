/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // === PALETA CÓDICE TRILUNA (XIANXIA AAA) ===
        void: {
          100: '#24243e',
          200: '#302b63',
          300: '#1a1a2e',
          DEFAULT: '#0f0c29',
        },
        jade: {
          100: '#96c93d',
          200: '#4ade80',
          DEFAULT: '#00b09b',
        },
        imperial: {
          100: '#ffd200',
          200: '#f7971e',
          DEFAULT: '#d4af37',
        },
        demon: {
          100: '#ef473a',
          DEFAULT: '#cb2d3e',
        },
        mist: {
          glass: 'rgba(255, 255, 255, 0.05)',
          border: 'rgba(255, 255, 255, 0.1)',
          glow: 'rgba(255, 255, 255, 0.2)',
        },
      },
      fontFamily: {
        title: ['Cinzel', 'serif'],
        display: ['Playfair Display', 'serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      boxShadow: {
        'glow-purple': '0 0 20px rgba(168, 85, 247, 0.5)',
        'glow-gold': '0 0 25px rgba(212, 175, 55, 0.6)',
        'glow-jade': '0 0 30px rgba(0, 176, 155, 0.4)',
        'glow-demon': '0 0 20px rgba(203, 45, 62, 0.5)',
        'inner-glow': 'inset 0 2px 8px 0 rgba(255, 255, 255, 0.1)',
        'mystic': '0 8px 32px 0 rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)',
      },
      backgroundImage: {
        'nebula-dark': 'radial-gradient(ellipse at top, #302b63 0%, #0f0c29 50%, #000000 100%)',
        'gradient-jade': 'linear-gradient(135deg, #00b09b 0%, #96c93d 100%)',
        'gradient-gold': 'linear-gradient(135deg, #f7971e 0%, #ffd200 100%)',
        'gradient-demon': 'linear-gradient(135deg, #cb2d3e 0%, #ef473a 100%)',
        'gradient-void': 'linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
      },
      animation: {
        'float': 'float 20s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'shimmer': 'shimmer 3s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translate(0, 0) rotate(0deg)' },
          '33%': { transform: 'translate(30px, -30px) rotate(120deg)' },
          '66%': { transform: 'translate(-20px, 20px) rotate(240deg)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(212, 175, 55, 0.4)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 40px rgba(212, 175, 55, 0.7)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-1000px 0' },
          '100%': { backgroundPosition: '1000px 0' },
        },
      },
    },
  },
  plugins: [],
};
