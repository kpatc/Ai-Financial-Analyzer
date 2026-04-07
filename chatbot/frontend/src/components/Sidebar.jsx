export default function Sidebar({ companies, onSelectCompany }) {
  const quickActions = [
    { label: '📈 Revenue Trends', query: 'What is the revenue trend?' },
    { label: '💰 Profitability', query: 'Show me profitability metrics' },
    { label: '📊 Leverage', query: 'Show debt-to-equity ratios' },
  ]

  const sectors = [
    { label: '🖥️ Technology', query: 'Tech companies analysis' },
    { label: '🏦 Finance', query: 'Financial institutions' },
    { label: '🏥 Healthcare', query: 'Healthcare sector' },
    { label: '⚡ Energy', query: 'Energy companies' },
  ]

  return (
    <div className="w-80 bg-dark-bg-secondary border-r border-dark-border overflow-y-auto p-4 flex flex-col gap-6">
      {/* Quick Actions */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-dark-text-muted mb-3 px-2">Quick Actions</h3>
        <div className="space-y-2">
          {quickActions.map((action, i) => (
            <button
              key={i}
              onClick={() => window.dispatchEvent(new CustomEvent('sendQuery', { detail: action.query }))}
              className="w-full text-left px-3 py-2 rounded-lg bg-dark-card hover:bg-dark-card-hover hover:border-accent border border-dark-border text-sm font-medium text-dark-text transition-all"
            >
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sectors */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-dark-text-muted mb-3 px-2">Sectors</h3>
        <div className="space-y-2">
          {sectors.map((sector, i) => (
            <button
              key={i}
              onClick={() => window.dispatchEvent(new CustomEvent('sendQuery', { detail: sector.query }))}
              className="w-full text-left px-3 py-2 rounded-lg bg-dark-card hover:bg-dark-card-hover hover:border-accent border border-dark-border text-sm font-medium text-dark-text transition-all"
            >
              {sector.label}
            </button>
          ))}
        </div>
      </div>

      {/* Companies */}
      <div>
        <h3 className="text-xs font-semibold uppercase tracking-wider text-dark-text-muted mb-3 px-2">Companies</h3>
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {companies.slice(0, 12).map((company) => (
            <button
              key={company.ticker}
              onClick={() => onSelectCompany(company.ticker)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg hover:bg-dark-card border border-transparent hover:border-dark-border text-sm text-dark-text transition-all"
            >
              <span className="font-medium">{company.ticker}</span>
              <span className="w-2 h-2 rounded-full bg-green-500"></span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
