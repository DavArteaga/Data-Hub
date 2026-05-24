import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#00236f',
        'primary-container': '#1e3a8a',
        background: '#fbf8ff',
        surface: '#ffffff',
        'surface-container-low': '#f4f2fd',
        'on-surface': '#1a1b22',
        'on-surface-variant': '#444651',
        outline: '#757682',
        'outline-variant': '#c5c5d3',
        error: '#ba1a1a',
      },
      fontFamily: {
        inter: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      spacing: {
        'sidebar-width': '240px',
        'header-height': '56px',
      },
      fontSize: {
        'display': ['30px', { fontWeight: '700', letterSpacing: '-0.02em' }],
        'h1': ['24px', { fontWeight: '700', letterSpacing: '-0.015em' }],
        'h2': ['20px', { fontWeight: '600', letterSpacing: '-0.01em' }],
        'body': ['14px', { fontWeight: '400' }],
        'body-sm': ['12px', { fontWeight: '400' }],
        'label-caps': ['11px', { fontWeight: '600', letterSpacing: '0.05em' }],
      },
      borderRadius: {
        card: '8px',
        btn: '6px',
      },
    },
  },
  plugins: [],
}

export default config
