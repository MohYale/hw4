import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth.tsx'
import { useCatalogue } from '../catalogue.tsx'
import { fetchChatHistory, sendChat } from '../api.ts'
import type { ChatHistoryTurn, ChatPageRef } from '../api.ts'
import { formatPrice } from '../format.ts'
import type { ChatProductCard } from '../types.ts'

type ChatLine = {
  id: number
  from: 'shop' | 'shopper'
  text: string
  products?: ChatProductCard[]
}

const welcome: ChatLine = {
  id: 1,
  from: 'shop',
  text: 'Ask about a garment, a size, or a college crest.',
}

function pageFromPath(pathname: string): ChatPageRef {
  const match = pathname.match(/^\/products\/([^/]+)$/)
  return {
    path: pathname,
    product_id: match ? decodeURIComponent(match[1]) : '',
  }
}

export function ChatWidget() {
  const navigate = useNavigate()
  const location = useLocation()
  const { shopper } = useAuth()
  const { setMatches } = useCatalogue()
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [historyReady, setHistoryReady] = useState(true)
  const [lines, setLines] = useState<ChatLine[]>([welcome])
  const nextId = useRef(2)
  const logRef = useRef<HTMLDivElement>(null)
  const sessionRef = useRef<string | null>(null)
  sessionRef.current = shopper ? `${shopper.id}:${shopper.email}` : null

  useEffect(() => {
    const log = logRef.current
    if (log) {
      log.scrollTop = log.scrollHeight
    }
  }, [lines, open, busy])

  useEffect(() => {
    let ignore = false
    if (!shopper) {
      setLines([welcome])
      nextId.current = 2
      setHistoryReady(true)
      return
    }
    setHistoryReady(false)
    fetchChatHistory({ id: shopper.id, email: shopper.email })
      .then((messages) => {
        if (ignore) {
          return
        }
        if (messages.length === 0) {
          setLines([welcome])
          nextId.current = 2
        } else {
          setLines(
            messages.map((message, index) => ({
              id: index + 2,
              from: message.role === 'user' ? 'shopper' : 'shop',
              text: message.content,
              products: message.products,
            })),
          )
          nextId.current = messages.length + 2
        }
        setHistoryReady(true)
      })
      .catch(() => {
        if (ignore) {
          return
        }
        setLines([welcome])
        nextId.current = 2
        setHistoryReady(true)
      })
    return () => {
      ignore = true
    }
  }, [shopper])

  async function sendMessage(event: FormEvent) {
    event.preventDefault()
    const text = draft.trim()
    if (!text || busy || !historyReady) {
      return
    }
    const history: ChatHistoryTurn[] = shopper
      ? []
      : lines
          .filter((line) => line.id !== welcome.id)
          .map((line) => ({
            role: line.from === 'shopper' ? 'user' : 'assistant',
            content: line.text,
          }))
    const session = sessionRef.current
    const shopperId = nextId.current
    nextId.current += 1
    setLines((current) => [...current, { id: shopperId, from: 'shopper', text }])
    setDraft('')
    setBusy(true)
    try {
      const reply = await sendChat(
        text,
        history,
        shopper ? { id: shopper.id, email: shopper.email } : null,
        pageFromPath(location.pathname),
      )
      if (sessionRef.current !== session) {
        return
      }
      if (reply.matches.length > 0) {
        setMatches(text, reply.matches)
        navigate('/products')
      }
      const shopId = nextId.current
      nextId.current += 1
      setLines((current) => [
        ...current,
        {
          id: shopId,
          from: 'shop',
          text: reply.reply,
          products: reply.products,
        },
      ])
    } catch (reason: unknown) {
      if (sessionRef.current !== session) {
        return
      }
      const shopId = nextId.current
      nextId.current += 1
      setLines((current) => [
        ...current,
        {
          id: shopId,
          from: 'shop',
          text: reason instanceof Error ? reason.message : 'The shop assistant could not answer just now.',
        },
      ])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat-dock">
      {open ? (
        <section className="chat-panel" aria-label="Shop chat">
          <header className="chat-header">
            <div>
              <p className="chat-kicker">
                {shopper ? `Saved for ${shopper.first_name}` : 'Guest chat stays on this visit'}
              </p>
              <h2>Shop chat</h2>
            </div>
            <button type="button" className="chat-close" onClick={() => setOpen(false)}>
              Close
            </button>
          </header>
          <div className="chat-log" ref={logRef}>
            {lines.map((line) => (
              <div key={line.id} className={`chat-line ${line.from}`}>
                <p>{line.text}</p>
                {line.products && line.products.length > 0 ? (
                  <div className="chat-cards">
                    {line.products.map((product) => (
                      <Link
                        key={product.product_id}
                        to={`/products/${product.product_id}`}
                        className="chat-card"
                      >
                        <img src={`/${product.image_file_path}`} alt="" />
                        <span>
                          <strong>{product.name}</strong>
                          <span>{formatPrice(product.price)}</span>
                          <InStock sizes={product.sizes} />
                        </span>
                      </Link>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            {shopper && !historyReady ? (
              <p className="chat-line shop">Loading your saved chat…</p>
            ) : null}
            {busy ? <p className="chat-line shop">Looking through the catalogue…</p> : null}
          </div>
          <form className="chat-form" onSubmit={sendMessage}>
            <label className="visually-hidden" htmlFor="chat-draft">
              Message
            </label>
            <input
              id="chat-draft"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Write a message"
              disabled={busy || !historyReady}
            />
            <button type="submit" disabled={busy || !historyReady}>
              Send
            </button>
          </form>
        </section>
      ) : null}
      <button
        type="button"
        className="chat-toggle"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        {open ? 'Hide chat' : 'Chat'}
      </button>
    </div>
  )
}

function InStock({ sizes }: { sizes: ChatProductCard['sizes'] }) {
  if (sizes.length === 0) {
    return null
  }
  const available = sizes.filter((size) => size.quantity > 0).map((size) => size.size)
  const gone = sizes.filter((size) => size.quantity === 0).map((size) => size.size)
  return (
    <span className="chat-sizes">
      {available.length > 0 ? `In stock: ${available.join(', ')}` : 'No sizes in stock'}
      {gone.length > 0 ? `. Out of stock: ${gone.join(', ')}` : ''}
    </span>
  )
}
