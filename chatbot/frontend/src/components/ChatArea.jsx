import { useEffect, useRef, useState } from 'react'
import Message from './Message'
import InputArea from './InputArea'

export default function ChatArea({ messages, isLoading, onSendMessage, onResetChat }) {
  const messagesEndRef = useRef(null)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    const handleSendQuery = (e) => {
      onSendMessage(e.detail)
    }
    window.addEventListener('sendQuery', handleSendQuery)
    return () => window.removeEventListener('sendQuery', handleSendQuery)
  }, [onSendMessage])

  return (
    <div className="flex-1 flex flex-col bg-dark-bg">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <h1 className="text-3xl font-bold text-accent mb-2">FinanceAI</h1>
              <p className="text-dark-text-muted mb-6">
                Welcome! I'm your financial analyst assistant. Ask me anything about company metrics, trends, or comparisons.
              </p>
              <div className="space-y-2 text-sm text-dark-text-muted">
                <p>💡 Try:</p>
                <ul className="space-y-1">
                  <li>"What is Apple's revenue trend?"</li>
                  <li>"Compare Microsoft and Google"</li>
                  <li>"Show me the most profitable companies"</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex gap-2 items-end">
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-dark-text-muted animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-dark-text-muted animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-dark-text-muted animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <InputArea
        onSendMessage={onSendMessage}
        isLoading={isLoading}
        onResetChat={onResetChat}
      />
    </div>
  )
}
