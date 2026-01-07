/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        'cult-dark': '#1a1a1a',      // Preto profundo para fundos
        'cult-gold': '#c4a66a',      // Dourado para detalhes e textos importantes
        'cult-red': '#8c2d2d',       // Vermelho escuro para acentos e alertas
        'cult-light': '#f0e6d2',     // Um tom de pergaminho para texto principal
        'cult-secondary': '#4a4a4a', // Cinza escuro para bordas e elementos secundários
      },
      fontFamily: {
        'serif': ['"EB Garamond"', 'serif'], // Uma fonte serifada elegante
      },
      backgroundImage: {
        'paper-scroll': "url('/scroll-background.png')", // Imagem de fundo para a janela do jogo
      },
      borderColor: {
        'cult-gold': '#c4a66a',
      }
    },
  },
  plugins: [],
};
