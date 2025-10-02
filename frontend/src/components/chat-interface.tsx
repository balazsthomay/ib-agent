'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@clerk/nextjs'
import { Send, Loader2, Plus } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatInterfaceProps {
  projectId: string
}

export function ChatInterface({ projectId }: ChatInterfaceProps) {
  const { getToken } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isConnected, setIsConnected] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(true)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const streamingMessageRef = useRef<string>('')

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Load conversation history on mount
  useEffect(() => {
    const loadHistory = async () => {
      try {
        const token = await getToken()
        if (!token) return

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
        const response = await fetch(`${apiUrl}/api/chat/messages/${projectId}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          const history = await response.json()
          setMessages(history.map((msg: any) => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.created_at)
          })))
        }
      } catch (error) {
        console.error('Failed to load message history:', error)
      } finally {
        setIsLoadingHistory(false)
      }
    }

    loadHistory()
  }, [projectId, getToken])

  // WebSocket connection
  useEffect(() => {
    let ws: WebSocket | null = null
    let reconnectTimeout: NodeJS.Timeout

    const connect = async () => {
      try {
        const token = await getToken()
        if (!token) {
          console.error('No auth token available')
          return
        }

        // Determine WebSocket URL based on environment
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsHost = process.env.NEXT_PUBLIC_API_URL
          ? process.env.NEXT_PUBLIC_API_URL.replace(/^https?:\/\//, '')
          : 'localhost:8000'
        const wsUrl = `${wsProtocol}//${wsHost}/api/chat/ws/${projectId}`

        ws = new WebSocket(wsUrl)
        wsRef.current = ws

        ws.onopen = () => {
          console.log('WebSocket connected')
          setIsConnected(true)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            if (data.type === 'chunk') {
              // Streaming chunk received
              streamingMessageRef.current += data.content
              setMessages(prev => {
                const lastMessage = prev[prev.length - 1]
                if (lastMessage && lastMessage.role === 'assistant' && lastMessage.id === 'streaming') {
                  return [
                    ...prev.slice(0, -1),
                    { ...lastMessage, content: streamingMessageRef.current }
                  ]
                } else {
                  return [
                    ...prev,
                    {
                      id: 'streaming',
                      role: 'assistant',
                      content: streamingMessageRef.current,
                      timestamp: new Date()
                    }
                  ]
                }
              })
            } else if (data.type === 'done') {
              // Streaming complete - capture content before clearing ref
              const finalContent = streamingMessageRef.current
              streamingMessageRef.current = ''
              setIsStreaming(false)

              setMessages(prev => {
                const lastMessage = prev[prev.length - 1]
                if (lastMessage && lastMessage.id === 'streaming') {
                  return [
                    ...prev.slice(0, -1),
                    {
                      id: `msg-${Date.now()}`,
                      role: 'assistant',
                      content: finalContent,
                      timestamp: new Date()
                    }
                  ]
                }
                return prev
              })
            } else if (data.type === 'error') {
              console.error('WebSocket error:', data.content)
              setMessages(prev => [
                ...prev,
                {
                  id: `error-${Date.now()}`,
                  role: 'assistant',
                  content: `Error: ${data.content}`,
                  timestamp: new Date()
                }
              ])
              setIsStreaming(false)
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error)
          }
        }

        ws.onerror = (error) => {
          console.error('WebSocket error:', error)
          setIsConnected(false)
        }

        ws.onclose = () => {
          console.log('WebSocket disconnected')
          setIsConnected(false)
          wsRef.current = null

          // Attempt reconnect after 3 seconds
          reconnectTimeout = setTimeout(() => {
            console.log('Attempting to reconnect...')
            connect()
          }, 3000)
        }
      } catch (error) {
        console.error('Failed to connect WebSocket:', error)
      }
    }

    connect()

    // Cleanup
    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout)
      if (ws) {
        ws.close()
      }
    }
  }, [projectId, getToken])

  const sendMessage = async () => {
    if (!input.trim() || !isConnected || isStreaming) return

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsStreaming(true)
    streamingMessageRef.current = ''

    try {
      const token = await getToken()
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          message: userMessage.content,
          token: token
        }))
      } else {
        console.error('WebSocket not connected')
        setIsStreaming(false)
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      setIsStreaming(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearChat = async () => {
    if (!confirm('Are you sure you want to clear this chat? This cannot be undone.')) {
      return
    }

    try {
      const token = await getToken()
      if (!token) return

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/chat/messages/${projectId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        setMessages([])
      } else {
        console.error('Failed to clear chat')
      }
    } catch (error) {
      console.error('Error clearing chat:', error)
    }
  }

  return (
    <div className="flex-1 flex flex-col">
      {/* Connection status and actions */}
      <div className="px-4 py-2 bg-muted/50 border-b border-border text-xs flex items-center justify-between">
        <span className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          {isConnected ? 'Connected' : 'Connecting...'}
        </span>
        <button
          onClick={clearChat}
          disabled={messages.length === 0 || isStreaming}
          className="flex items-center gap-1 px-2 py-1 text-xs rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
          title="Start a new chat"
        >
          <Plus className="w-3 h-3" />
          New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
              <p className="text-sm">Loading conversation...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <p className="text-lg mb-2">Start a conversation</p>
              <p className="text-sm">Ask me anything about your project</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-foreground'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.id === 'streaming' && (
                  <span className="inline-block ml-1 animate-pulse">▋</span>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-border p-4 bg-background">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isConnected ? "Type your message..." : "Connecting..."}
            disabled={!isConnected || isStreaming}
            className="flex-1 px-4 py-2 rounded-md border border-border bg-background disabled:bg-muted/50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <button
            onClick={sendMessage}
            disabled={!isConnected || isStreaming || !input.trim()}
            className="px-6 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:bg-muted disabled:text-muted-foreground disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isStreaming ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Thinking...</span>
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                <span>Send</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
