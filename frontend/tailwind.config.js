import daisyui from 'daisyui'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      maxWidth: { md: '28rem' },
      fontFamily: {
        // Newake (brand display) and Gotham (brand body) aren't free web fonts;
        // Space Grotesk + Montserrat are the closest Google equivalents (as in the prototype).
        sans: ['Montserrat', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [daisyui],
  daisyui: {
    logs: false,
    themes: [
      {
        // Official Lyfter brand palette (Manual de Marca 2024).
        tokenteam: {
          primary: '#71ceff', // Lyfter blue
          'primary-content': '#0f1720',
          secondary: '#d798e7', // Lyfter purple
          'secondary-content': '#1c1224',
          accent: '#ffcc8b', // Lyfter orange
          'accent-content': '#2a1d0c',
          neutral: '#1c212c',
          'neutral-content': '#cdd4e0',
          'base-100': '#181c26',
          'base-200': '#10131a',
          'base-300': '#2d323d', // Lyfter dark navy
          'base-content': '#e7eaf1',
          info: '#71ceff',
          'info-content': '#0f1720',
          success: '#add195', // Lyfter green
          'success-content': '#11210d',
          warning: '#ffcc8b', // Lyfter orange
          'warning-content': '#2a1d0c',
          error: '#e88f95', // Lyfter coral
          'error-content': '#2a0e10',
          '--rounded-box': '1.25rem',
          '--rounded-btn': '0.75rem',
          '--rounded-badge': '1rem',
          '--tab-radius': '0.75rem',
        },
      },
      {
        // Light variant of the brand palette (opt-in via Settings → Light mode).
        // Brand accents are darkened a touch so they stay legible on light surfaces.
        'tokenteam-light': {
          primary: '#1f9fe0',
          'primary-content': '#ffffff',
          secondary: '#a45cc2',
          'secondary-content': '#ffffff',
          accent: '#e08a2b',
          'accent-content': '#ffffff',
          neutral: '#e7eaf1',
          'neutral-content': '#1c212c',
          'base-100': '#ffffff',
          'base-200': '#f4f6fb',
          'base-300': '#dbe0ea',
          'base-content': '#1c212c',
          info: '#1f9fe0',
          'info-content': '#ffffff',
          success: '#5fa843',
          'success-content': '#ffffff',
          warning: '#e08a2b',
          'warning-content': '#2a1d0c',
          error: '#d65a62',
          'error-content': '#ffffff',
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
