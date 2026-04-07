export default function Header({ onThemeToggle, theme }) {
  return (
    <div className="h-16 bg-dark-bg-secondary border-b border-dark-border flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="text-2xl font-bold text-accent">FinanceAI</div>
      </div>

      <button
        onClick={onThemeToggle}
        className="p-2 rounded-lg hover:bg-dark-card-hover transition-colors"
        title="Toggle theme"
      >
        {theme === 'dark' ? '🌙' : '☀️'}
      </button>
    </div>
  )
}
