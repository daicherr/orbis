/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        celestial: {
          deep: '#0f0419',
          purple: '#2e1065',
          blue: '#1e3a8a',
          gold: '#d4af37',
          jade: '#10b981',
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
        'glow-gold': '0 0 25px rgba(212, 175, 55, 0.4)',
      },
    },
  },
  plugins: [],
};
