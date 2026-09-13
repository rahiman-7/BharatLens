/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        serif: ['"Playfair Display"', 'Merriweather', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        display: ['"Newsreader"', 'Georgia', 'serif'],
      },
      colors: {
        paper: {
          50: '#FBFBFB',
          100: '#F6F6F4',
          200: '#EFEFEA',
          300: '#E4E4DC',
          800: '#1C1D1F',
          900: '#121416',
          950: '#0A0B0D',
        },
        bharat: {
          saffron: '#E26D27',
          saffronLight: '#FFF4ED',
          indigo: '#1E3A8A',
          indigoLight: '#EEF2FF',
          navy: '#0F172A',
          gold: '#D97706',
          crimson: '#991B1B',
        },
        editorial: {
          ink: '#111827',
          muted: '#4B5563',
          faint: '#9CA3AF',
          border: '#E5E7EB',
          darkBorder: '#2E3440',
        }
      },
      letterSpacing: {
        widestEditorial: '0.18em',
      }
    },
  },
  plugins: [],
}
