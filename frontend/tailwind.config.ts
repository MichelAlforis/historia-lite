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
        // Cold War palette
        'coldwar': {
          'dark': '#0a0e17',
          'darker': '#080c14',
          'panel': '#0d1420',
        },
      },
      animation: {
        'shake-light': 'shake-light 0.3s ease-in-out',
        'shake-medium': 'shake-medium 0.4s ease-in-out',
        'shake-heavy': 'shake-heavy 0.5s ease-in-out',
        'shake-nuclear': 'shake-nuclear 1s ease-in-out',
        'marquee': 'marquee 10s linear infinite',
        'slide-down': 'slide-down 0.3s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'radar-sweep': 'radar-sweep 4s linear infinite',
        'typing': 'typing 0.1s steps(1)',
        'blink': 'blink 1s step-end infinite',
        'heartbeat': 'heartbeat 0.8s ease-in-out infinite',
        'static': 'static 0.5s steps(10) infinite',
      },
      keyframes: {
        'shake-light': {
          '0%, 100%': { transform: 'translateX(0)' },
          '25%': { transform: 'translateX(-2px)' },
          '75%': { transform: 'translateX(2px)' },
        },
        'shake-medium': {
          '0%, 100%': { transform: 'translateX(0) translateY(0)' },
          '25%': { transform: 'translateX(-4px) translateY(2px)' },
          '50%': { transform: 'translateX(4px) translateY(-2px)' },
          '75%': { transform: 'translateX(-4px) translateY(2px)' },
        },
        'shake-heavy': {
          '0%, 100%': { transform: 'translateX(0) translateY(0) rotate(0)' },
          '20%': { transform: 'translateX(-8px) translateY(4px) rotate(-1deg)' },
          '40%': { transform: 'translateX(8px) translateY(-4px) rotate(1deg)' },
          '60%': { transform: 'translateX(-8px) translateY(4px) rotate(-1deg)' },
          '80%': { transform: 'translateX(8px) translateY(-4px) rotate(1deg)' },
        },
        'shake-nuclear': {
          '0%, 100%': { transform: 'translateX(0) translateY(0) rotate(0)' },
          '10%': { transform: 'translateX(-15px) translateY(10px) rotate(-2deg)' },
          '20%': { transform: 'translateX(15px) translateY(-10px) rotate(2deg)' },
          '30%': { transform: 'translateX(-15px) translateY(10px) rotate(-2deg)' },
          '40%': { transform: 'translateX(15px) translateY(-10px) rotate(2deg)' },
          '50%': { transform: 'translateX(-15px) translateY(10px) rotate(-2deg)' },
          '60%': { transform: 'translateX(15px) translateY(-10px) rotate(2deg)' },
          '70%': { transform: 'translateX(-15px) translateY(10px) rotate(-2deg)' },
          '80%': { transform: 'translateX(15px) translateY(-10px) rotate(2deg)' },
          '90%': { transform: 'translateX(-10px) translateY(5px) rotate(-1deg)' },
        },
        'marquee': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(-100%)' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(100%)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'glow-pulse': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(6, 182, 212, 0.3)' },
          '50%': { boxShadow: '0 0 40px rgba(6, 182, 212, 0.6)' },
        },
        'radar-sweep': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
        'blink': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        'heartbeat': {
          '0%, 100%': { transform: 'scale(1)' },
          '14%': { transform: 'scale(1.1)' },
          '28%': { transform: 'scale(1)' },
          '42%': { transform: 'scale(1.1)' },
          '70%': { transform: 'scale(1)' },
        },
        'static': {
          '0%': { backgroundPosition: '0 0' },
          '100%': { backgroundPosition: '100% 100%' },
        },
      },
    },
  },
  plugins: [],
}
export default config
