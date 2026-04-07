import { useState, useRef, useEffect } from 'react'

export default function InputArea({ onSendMessage, isLoading, onResetChat }) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef(null)

  const handleSend = () => {
    if (message.trim() && !isLoading) {
      onSendMessage(message)
      setMessage('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 100) + 'px'
    }
  }, [message])

  return (
    <div className="border-t border-dark-border bg-dark-bg-secondary p-4">
      <div className="flex gap-3">
        <div className="flex-1 flex gap-2 bg-dark-card border border-dark-border rounded-xl p-2 focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/10 transition-all">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about metrics, trends, comparisons..."
            rows={1}
            className="flex-1 bg-transparent outline-none text-sm text-dark-text placeholder-dark-text-muted resize-none px-2 py-1 font-medium"
          />
        </div>

        <button
          onClick={handleSend}
          disabled={isLoading || !message.trim()}
          className="px-4 py-2 bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-semibold text-sm transition-colors"
        >
          Send
        </button>

        <button
          onClick={onResetChat}
          className="px-3 py-2 bg-dark-card hover:bg-dark-card-hover text-dark-text rounded-lg transition-colors"
          title="Clear conversation"
        >
          🔄
        </button>
      </div>
    </div>
  )
}
