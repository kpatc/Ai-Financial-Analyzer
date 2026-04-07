import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import ChartDisplay from './ChartDisplay'

export default function Message({ message }) {
  const isUser = message.role === 'user'
  const [showChart, setShowChart] = useState(true)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slideIn`}>
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-accent text-white rounded-br-none'
            : 'bg-dark-card border border-dark-border rounded-bl-none'
        }`}
      >
        {/* Text Content */}
        <div className="text-sm leading-relaxed">
          <ReactMarkdown
            components={{
              p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
              ul: ({ node, ...props }) => <ul className="list-disc list-inside mb-2" {...props} />,
              ol: ({ node, ...props }) => <ol className="list-decimal list-inside mb-2" {...props} />,
              code: ({ node, inline, ...props }) =>
                inline ? (
                  <code className={`${isUser ? 'bg-white/20' : 'bg-dark-bg'} px-1.5 py-0.5 rounded font-mono text-xs`} {...props} />
                ) : (
                  <code className={`${isUser ? 'bg-white/20' : 'bg-dark-bg'} block p-3 rounded font-mono text-xs mb-2 overflow-x-auto`} {...props} />
                ),
              a: ({ node, ...props }) => <a className="underline opacity-80 hover:opacity-100" {...props} />,
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Chart Icon & Display */}
        {message.chart && message.chart.data && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-3 gap-2">
              <button
                onClick={() => setShowChart(!showChart)}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors ${
                  isUser
                    ? 'hover:bg-white/20 text-white'
                    : 'hover:bg-accent/10 text-accent'
                }`}
                title="Click to toggle chart"
              >
                <span className="text-lg">📊</span>
                <span className="text-xs font-semibold">
                  {showChart ? 'Hide Chart' : 'Show Chart'}
                </span>
              </button>
            </div>

            {showChart && (
              <div className="animate-fadeIn">
                <div className="text-xs font-semibold text-dark-text-muted mb-3 text-center">
                  {message.chart.title}
                </div>
                <ChartDisplay chart={message.chart} />
              </div>
            )}
          </div>
        )}

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {message.sources.slice(0, 3).map((source, i) => (
              <div
                key={i}
                className={`text-xs px-2 py-1 rounded-full ${
                  isUser ? 'bg-white/20' : 'bg-accent/10 border border-accent'
                }`}
              >
                {source.ticker || '?'} ({source.fiscal_year || '?'})
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
