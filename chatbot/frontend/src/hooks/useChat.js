import { useState, useCallback, useRef } from 'react'
import { chatAPI } from '../services/api'

export const useChat = () => {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const sessionIdRef = useRef(`user_${Date.now()}`)

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || isLoading) return

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    try {
      const response = await chatAPI.send(text, sessionIdRef.current)

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.response,
        chart: response.chart,
        sources: response.sources,
        category: response.category,
        timestamp: new Date(),
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err.message || 'Failed to send message')
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: `Error: ${err.message}`,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }, [isLoading])

  const resetChat = useCallback(async () => {
    try {
      await chatAPI.reset(sessionIdRef.current)
      setMessages([])
      sessionIdRef.current = `user_${Date.now()}`
    } catch (err) {
      setError('Failed to reset chat')
    }
  }, [])

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    resetChat,
    sessionId: sessionIdRef.current,
  }
}
