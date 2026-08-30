import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { FiArrowUp, FiFileText, FiPlus, FiSquare, FiTrash2 } from 'react-icons/fi'
import { chatApi } from '../api/client'

function SourceBadge({ source }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-black p-3 text-xs text-zinc-300">
      <p className="flex items-center gap-1.5 font-medium text-zinc-300">
        <FiFileText size={13} /> {source.document_name} · Page {source.page_number}
      </p>
      <p className="mt-1.5 line-clamp-2 leading-5 text-zinc-400">{source.excerpt}</p>
    </div>
  )
}

export default function ChatPanel({ selectedDocumentIds }) {
  const [conversations, setConversations] = useState([])
  const [activeConversationId, setActiveConversationId] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const bottomRef = useRef(null)
  const abortControllerRef = useRef(null)

  const loadConversations = async () => {
    const { data } = await chatApi.listConversations()
    setConversations(data)
  }

  useEffect(() => {
    loadConversations().catch(() => setError('Unable to load conversations'))
    return () => abortControllerRef.current?.abort()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const loadConversation = async (id) => {
    if (loading) return
    const { data } = await chatApi.getConversation(id)
    setActiveConversationId(id)
    setMessages(data.messages.map((msg) => ({
      ...msg,
      sources: msg.sources ? JSON.parse(msg.sources) : [],
    })))
    setError('')
  }

  const startNewChat = () => {
    if (loading) return
    setActiveConversationId(null)
    setMessages([])
    setError('')
  }

  const handleDeleteConversation = async (id, event) => {
    event.stopPropagation()
    await chatApi.deleteConversation(id)
    if (activeConversationId === id) startNewChat()
    await loadConversations()
  }

  const stopGeneration = () => {
    abortControllerRef.current?.abort()
  }

  const handleSend = async (event) => {
    event.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    const controller = new AbortController()
    abortControllerRef.current = controller
    setInput('')
    setLoading(true)
    setError('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage, sources: [], pending: true }])

    try {
      const payload = { message: userMessage, document_ids: selectedDocumentIds }
      const { data } = activeConversationId
        ? await chatApi.sendMessageToConversation(activeConversationId, payload, controller.signal)
        : await chatApi.sendMessage(payload, controller.signal)

      if (!activeConversationId) setActiveConversationId(data.conversation_id)
      setMessages((prev) => [
        ...prev.map((message) => ({ ...message, pending: false })),
        { role: 'assistant', content: data.answer, sources: data.sources || [] },
      ])
      await loadConversations()
    } catch (err) {
      setMessages((prev) => prev.filter((message) => !message.pending))
      if (err.code !== 'ERR_CANCELED') setError(err.response?.data?.detail || 'Failed to send message')
    } finally {
      if (abortControllerRef.current === controller) abortControllerRef.current = null
      setLoading(false)
    }
  }

  return (
    <section className="grid min-h-[calc(100vh-5.5rem)] overflow-hidden rounded-2xl border border-zinc-800 bg-zinc-950 shadow-2xl shadow-black/40 lg:grid-cols-[270px_minmax(0,1fr)]">
      <aside className="border-b border-zinc-800 bg-black p-3 lg:border-b-0 lg:border-r">
        <div className="mb-3 flex items-center justify-between px-1">
          <div>
            <p className="text-sm font-semibold text-white">Chats</p>
            <p className="text-xs text-zinc-500">Your document conversations</p>
          </div>
          <button onClick={startNewChat} disabled={loading} title="New chat" className="icon-button">
            <FiPlus size={18} />
          </button>
        </div>
        <div className="flex max-h-40 gap-2 overflow-x-auto pb-1 lg:max-h-none lg:flex-col lg:overflow-y-auto">
          {conversations.length === 0 && <p className="px-2 py-4 text-xs text-zinc-500">Start a new chat to see it here.</p>}
          {conversations.map((conversation) => (
            <button key={conversation.id} onClick={() => loadConversation(conversation.id)} className={`group flex min-w-48 items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition lg:min-w-0 ${activeConversationId === conversation.id ? 'bg-zinc-800 text-white ring-1 ring-inset ring-zinc-600' : 'text-zinc-300 hover:bg-zinc-900'}`}>
              <span className="truncate">{conversation.title}</span>
              <span onClick={(event) => handleDeleteConversation(conversation.id, event)} className="ml-2 rounded p-1 text-zinc-500 opacity-0 transition hover:bg-zinc-700 hover:text-zinc-100 group-hover:opacity-100"><FiTrash2 size={14} /></span>
            </button>
          ))}
        </div>
      </aside>

      <div className="flex min-w-0 flex-col">
        <header className="flex items-center justify-between border-b border-zinc-800 px-5 py-4">
          <div>
            <h1 className="text-base font-semibold text-white">Ask your documents</h1>
            <p className="mt-0.5 text-xs text-zinc-400">{selectedDocumentIds.length ? `${selectedDocumentIds.length} document${selectedDocumentIds.length === 1 ? '' : 's'} selected` : 'Searching all uploaded documents'}</p>
          </div>
          <span className="hidden rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs text-zinc-400 sm:inline">Private workspace</span>
        </header>

        <div className="flex-1 space-y-5 overflow-y-auto px-4 py-6 sm:px-8">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-80 max-w-lg flex-col items-center justify-center text-center">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border border-zinc-700 bg-zinc-800 text-zinc-200"><FiFileText size={23} /></div>
              <h2 className="text-xl font-semibold text-white">What would you like to know?</h2>
              <p className="mt-2 text-sm leading-6 text-zinc-400">Upload a PDF, then ask for summaries, key facts, comparisons, or specific details.</p>
            </div>
          ) : messages.map((message, index) => (
            <motion.article key={`${message.id || message.content}-${index}`} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className={`mx-auto max-w-3xl ${message.role === 'user' ? 'flex justify-end' : ''}`}>
              <div className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === 'user' ? 'bg-zinc-800 text-white shadow-lg shadow-black/30' : 'border border-zinc-800 bg-black text-zinc-100'}`}>
                <p className="whitespace-pre-wrap">{message.content}</p>
                {message.sources?.length > 0 && <div className="mt-4 space-y-2 border-t border-zinc-800 pt-3"><p className="text-[11px] font-semibold uppercase tracking-wider text-zinc-500">Sources</p>{message.sources.map((source, sourceIndex) => <SourceBadge key={sourceIndex} source={source} />)}</div>}
              </div>
            </motion.article>
          ))}
          {loading && <div className="mx-auto flex max-w-3xl items-center gap-3 text-sm text-zinc-400"><span className="flex gap-1"><i className="typing-dot" /><i className="typing-dot" /><i className="typing-dot" /></span> Reading your documents…</div>}
          <div ref={bottomRef} />
        </div>

        <div className="border-t border-zinc-800 bg-black p-4 sm:px-6">
          {error && <p className="mx-auto mb-2 max-w-3xl text-sm text-rose-300">{error}</p>}
          <form onSubmit={handleSend} className="mx-auto flex max-w-3xl items-end gap-2 rounded-2xl border border-zinc-700 bg-zinc-900 p-2 shadow-xl shadow-black/20 focus-within:border-zinc-400/70">
            <textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); handleSend(event) } }} rows="1" placeholder="Ask anything about your documents…" className="max-h-32 min-h-11 flex-1 resize-none bg-transparent px-3 py-2 text-sm text-white outline-none placeholder:text-zinc-500" />
            {loading ? <button type="button" onClick={stopGeneration} className="inline-flex h-10 items-center gap-2 rounded-xl bg-zinc-700 px-3 text-sm font-medium text-zinc-100 transition hover:bg-zinc-600"><FiSquare size={14} /> <span className="hidden sm:inline">Stop</span></button> : <button type="submit" disabled={!input.trim()} aria-label="Send message" className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-zinc-100 text-zinc-950 transition hover:bg-white disabled:cursor-not-allowed disabled:opacity-40"><FiArrowUp size={19} /></button>}
          </form>
          <p className="mt-2 text-center text-[11px] text-zinc-500">Answers are grounded in your uploaded documents.</p>
        </div>
      </div>
    </section>
  )
}
