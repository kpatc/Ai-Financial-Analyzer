/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'dark-bg': '#0a0f1e',
        'dark-bg-secondary': '#0f172a',
        'dark-card': '#1e293b',
        'dark-card-hover': '#334155',
        'dark-border': '#334155',
        'dark-text': '#f1f5f9',
        'dark-text-muted': '#94a3b8',
        'accent': '#6366f1',
        'accent-hover': '#4f46e5',
      },
      fontFamily: {
        'sans': ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      animation: {
        'slideIn': 'slideIn 0.3s ease-out',
        'fadeIn': 'fadeIn 0.3s ease-out',
      },
    },
  },
  plugins: [],
}
