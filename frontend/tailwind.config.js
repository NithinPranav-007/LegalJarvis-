/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          '"Plus Jakarta Sans"',
          '"Inter"',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
        serif: [
          '"Plus Jakarta Sans"',
          '"Inter"',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'sans-serif',
        ],
        mono: [
          '"Cascadia Code"',
          '"Segoe UI Mono"',
          'Consolas',
          'Menlo',
          'Monaco',
          'monospace',
        ],
      },
      colors: {
        legal: {
          950: '#071e17',
          900: '#0a231c',
          800: '#0f2c24',
          700: '#163f34',
          600: '#1e5446',
          100: '#e6f4ea',
          50: '#edf2ec',
        },
        amberLegal: {
          950: '#5c2606',
          900: '#78350f',
          800: '#92400e',
          100: '#faeae1',
          50: '#fef7f2',
        }
      },
      boxShadow: {
        '3d-hover': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04), 0 0 20px rgba(15, 44, 36, 0.08)',
        '3d-card': '0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -1px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
}
