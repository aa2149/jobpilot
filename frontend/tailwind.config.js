/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Fraunces"', 'serif'],
        sans: ['"Geist"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      colors: {
        ink: {
          50: '#FAFAF7',
          100: '#F2F1EB',
          200: '#E0DED4',
          300: '#B8B5A6',
          400: '#7A7868',
          500: '#4A4940',
          600: '#2E2D27',
          700: '#1F1E1A',
          800: '#161510',
          900: '#0C0B08',
        },
        accent: {
          DEFAULT: '#D97757',
          light: '#E8B59C',
          deep: '#B45A3D',
        },
        emerald: {
          ink: '#1F4D3F',
        },
      },
      animation: {
        'fade-up': 'fadeUp 0.6s ease-out forwards',
        'pulse-soft': 'pulseSoft 3s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: 0, transform: 'translateY(12px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.4 },
        },
      },
    },
  },
  plugins: [],
}
