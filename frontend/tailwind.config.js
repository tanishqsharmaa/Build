/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        bg:       '#0a0a0f',
        surface:  '#12121a',
        surface2: '#1a1a28',
        accent:   '#6c47ff',
        accent2:  '#00d4aa',
        muted:    'rgba(240,240,245,0.6)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'sans-serif'],
      },
      animation: {
        'fade-up':   'fadeUp 0.7s ease both',
        'pulse-glow': 'pulseGlow 3s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          from: { opacity: '0', transform: 'translateY(24px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { opacity: '0.5' },
          '50%':      { opacity: '0.2' },
        },
      },
    },
  },
  plugins: [],
};
