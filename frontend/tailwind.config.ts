import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Faction colors
        'usa': '#3b82f6',
        'china': '#ef4444',
        'russia': '#8b5cf6',
        'europe': '#22c55e',
        'neutral': '#6b7280',
      },
    },
  },
  plugins: [],
}
export default config
