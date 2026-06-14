// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Linear design tokens — exact values from DESIGN.md
        linear: {
          canvas:              '#010102',
          surface1:            '#0f1011',
          surface2:            '#141516',
          surface3:            '#18191a',
          surface4:            '#191a1b',
          hairline:            '#23252a',
          'hairline-strong':   '#34343a',
          'hairline-tertiary': '#3e3e44',
          accent:              '#5e6ad2',
          'accent-hover':      '#828fff',
          'accent-focus':      '#5e69d1',
          ink:                 '#f7f8f8',
          'ink-muted':         '#d0d6e0',
          'ink-subtle':        '#8a8f98',
          'ink-tertiary':      '#62666d',
          success:             '#27a644',
        },
        // gauntlet.* remapped to Linear values — existing classNames get Linear colors
        gauntlet: {
          bg:      '#010102',  // linear.canvas
          surface: '#0f1011',  // linear.surface1
          border:  '#23252a',  // linear.hairline
          accent:  '#5e6ad2',  // linear.accent
          success: '#27a644',  // linear.success
          warning: '#F59E0B',
          danger:  '#EF4444',
          muted:   '#8a8f98',  // linear.ink-subtle
          text:    '#f7f8f8',  // linear.ink
        },
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Display', '-apple-system', 'system-ui', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SF Mono', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
