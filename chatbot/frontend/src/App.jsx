import { useState, useEffect } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatArea from './components/ChatArea'
import { useChat } from './hooks/useChat'
import { chatAPI } from './services/api'

function App() {
  const chat = useChat()
  const [companies, setCompanies] = useState([])
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'dark'
    setTheme(savedTheme)
    updateTheme(savedTheme)

    // Load companies
    chatAPI.getCompanies()
      .then(data => setCompanies(data.companies || []))
      .catch(err => console.error('Failed to load companies:', err))

    // Send welcome message
    chat.messages.length === 0 && setTimeout(() => {
      chat.sendMessage('Hello!')
    }, 100)
  }, [])

  const updateTheme = (newTheme) => {
    if (newTheme === 'light') {
      document.documentElement.classList.add('light-mode')
    } else {
      document.documentElement.classList.remove('light-mode')
    }
  }

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    updateTheme(newTheme)
  }

  return (
    <div className="flex flex-col h-screen bg-dark-bg text-dark-text">
      <Header onThemeToggle={toggleTheme} theme={theme} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar companies={companies} onSelectCompany={(ticker) => {
          chat.sendMessage(`Tell me about ${ticker} financial performance`)
        }} />

        <ChatArea
          messages={chat.messages}
          isLoading={chat.isLoading}
          onSendMessage={chat.sendMessage}
          onResetChat={chat.resetChat}
        />
      </div>
    </div>
  )
}

export default App
