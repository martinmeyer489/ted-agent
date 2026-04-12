import type { Config } from 'tailwindcss'
import tailwindcssAnimate from 'tailwindcss-animate'

export default {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}'
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1F2937',
        primaryAccent: '#111827',
        brand: '#003399',
        euBlue: '#003399',
        euYellow: '#FFCC00',
        background: {
          DEFAULT: '#FFFFFF',
          secondary: '#F9FAFB'
        },
        secondary: '#374151',
        border: '#E5E7EB',
        accent: '#F3F4F6',
        muted: '#6B7280',
        destructive: '#DC2626',
        positive: '#059669'
      },
      fontFamily: {
        geist: 'var(--font-geist-sans)',
        dmmono: 'var(--font-dm-mono)'
      },
      borderRadius: {
        xl: '10px'
      },
      animation: {
        'bounce-delay-100': 'bounce 1s infinite 100ms',
        'bounce-delay-200': 'bounce 1s infinite 200ms',
      }
    }
  },
  plugins: [tailwindcssAnimate]
} satisfies Config
