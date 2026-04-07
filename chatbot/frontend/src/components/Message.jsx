import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import ChartDisplay from './ChartDisplay'
import FinancialTable from './FinancialTable'
import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import { Box, IconButton } from '@mui/material'
import { COMPANY_NAMES } from '../utils/companyNames'

export default function Message({ message }) {
  const isUser = message.role === 'user'
  const [showChart, setShowChart] = useState(true)
  const [showTable, setShowTable] = useState(true)

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slideIn`}>
      <div
        className={`max-w-4xl rounded-2xl px-4 py-3 ${
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
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto mb-2">
                  <table className="w-full text-xs border-collapse" {...props} />
                </div>
              ),
              th: ({ node, ...props }) => (
                <th className="border border-accent/30 px-2 py-1 text-left bg-accent/10" {...props} />
              ),
              td: ({ node, ...props }) => (
                <td className="border border-accent/20 px-2 py-1" {...props} />
              ),
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

        {/* Chart Display */}
        {message.chart && message.chart.data && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-3 gap-2">
              <span className="text-xs font-semibold text-dark-text-muted">
                {message.chart.title}
              </span>
              <IconButton
                size="small"
                onClick={() => setShowChart(!showChart)}
                sx={{ color: isUser ? 'white' : '#6366f1' }}
              >
                {showChart ? <VisibilityIcon sx={{ fontSize: 18 }} /> : <VisibilityOffIcon sx={{ fontSize: 18 }} />}
              </IconButton>
            </div>

            {showChart && (
              <div className="animate-fadeIn">
                <ChartDisplay chart={message.chart} />
              </div>
            )}
          </div>
        )}

        {/* Table Display */}
        {message.table && message.table.data && (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-3 gap-2">
              <span className="text-xs font-semibold text-dark-text-muted">
                {message.table.title}
              </span>
              <IconButton
                size="small"
                onClick={() => setShowTable(!showTable)}
                sx={{ color: isUser ? 'white' : '#6366f1' }}
              >
                {showTable ? <VisibilityIcon sx={{ fontSize: 18 }} /> : <VisibilityOffIcon sx={{ fontSize: 18 }} />}
              </IconButton>
            </div>

            {showTable && (
              <Box sx={{ bgcolor: '#1a1a2e', borderRadius: '8px', overflow: 'hidden' }}>
                <FinancialTable
                  data={message.table.data}
                  columns={message.table.columns}
                />
              </Box>
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
                {COMPANY_NAMES[source.ticker] || source.ticker || '?'} ({source.fiscal_year || '?'})
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
