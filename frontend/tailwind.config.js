import daisyui from 'daisyui'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      maxWidth: { md: '28rem' },
    },
  },
  plugins: [daisyui],
  daisyui: {
    logs: false,
    themes: [
      {
        tokenteam: {
          primary: '#2dd4bf',
          'primary-content': '#04211c',
          secondary: '#a78bfa',
          'secondary-content': '#190f33',
          accent: '#fb7185',
          'accent-content': '#2a0a10',
          neutral: '#161a24',
          'neutral-content': '#cbd5e1',
          'base-100': '#12151d',
          'base-200': '#0d0f15',
          'base-300': '#232a3a',
          'base-content': '#e2e8f0',
          info: '#38bdf8',
          'info-content': '#04212e',
          success: '#22c55e',
          'success-content': '#04210f',
          warning: '#f59e0b',
          'warning-content': '#2a1a02',
          error: '#f43f5e',
          'error-content': '#2a0610',
          '--rounded-box': '1.25rem',
          '--rounded-btn': '0.75rem',
          '--rounded-badge': '1rem',
          '--tab-radius': '0.75rem',
        },
      },
      'dark',
    ],
    darkTheme: 'tokenteam',
  },
}
