import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, placeOrder, shipOrder } from '../api.ts'
import { useAuth } from '../auth.tsx'
import { formatPrice } from '../format.ts'
import type { ProductDetail, ShopOrder } from '../types.ts'

export function ProductPage() {
  const { productId } = useParams()
  const { shopper } = useAuth()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [size, setSize] = useState('')
  const [color, setColor] = useState('')
  const [buyNote, setBuyNote] = useState('')
  const [busy, setBusy] = useState(false)
  const [order, setOrder] = useState<ShopOrder | null>(null)
  const [shippedEmail, setShippedEmail] = useState('')

  useEffect(() => {
    if (!productId) {
      setError('This product is not in the catalogue')
      setLoading(false)
      return
    }
    let ignore = false

    async function load(initial: boolean) {
      if (initial) {
        setLoading(true)
        setError('')
      }
      try {
        const row = await fetchProduct(productId as string)
        if (!ignore) {
          setProduct(row)
          setError('')
        }
      } catch (reason: unknown) {
        if (!ignore && initial) {
          setProduct(null)
          setError(reason instanceof Error ? reason.message : 'Could not load this product')
        }
      } finally {
        if (!ignore && initial) {
          setLoading(false)
        }
      }
    }

    void load(true)
    const timer = window.setInterval(() => {
      void load(false)
    }, 4000)
    return () => {
      ignore = true
      window.clearInterval(timer)
    }
  }, [productId])

  useEffect(() => {
    setSize('')
    setColor('')
    setOrder(null)
    setShippedEmail('')
    setBuyNote('')
  }, [productId])

  async function onBuy(event: FormEvent) {
    event.preventDefault()
    if (!shopper || !product || !size || !color) {
      return
    }
    setBusy(true)
    setBuyNote('')
    try {
      const placed = await placeOrder(
        { id: shopper.id, email: shopper.email },
        product.product_id,
        size,
        color,
      )
      setOrder(placed)
      setShippedEmail('')
      setBuyNote(`${placed.product_name} is reserved in ${placed.size}. ${placed.remaining} left in that size.`)
      const fresh = await fetchProduct(product.product_id)
      setProduct(fresh)
    } catch (reason: unknown) {
      setBuyNote(reason instanceof Error ? reason.message : 'Could not buy this item')
    } finally {
      setBusy(false)
    }
  }

  async function onShip() {
    if (!shopper || !order) {
      return
    }
    setBusy(true)
    try {
      const shipped = await shipOrder({ id: shopper.id, email: shopper.email }, order.id)
      setShippedEmail(shipped.email_body)
      setOrder({ ...order, status: 'shipped' })
    } catch (reason: unknown) {
      setBuyNote(reason instanceof Error ? reason.message : 'Could not mark this order shipped')
    } finally {
      setBusy(false)
    }
  }

  const chosen = product?.sizes.find((stock) => stock.size === size)
  const canBuy = Boolean(shopper && size && color && chosen && chosen.quantity > 0 && !busy)

  return (
    <div className="page">
      <Link className="back-link" to="/products">
        Back to products
      </Link>
      {loading ? <p className="status">Loading this item…</p> : null}
      {error ? <p className="status error">{error}</p> : null}
      {product ? (
        <article className="detail">
          <img
            className="detail-image"
            src={`/${product.image_file_path}`}
            alt={product.name}
          />
          <div className="detail-copy">
            <p className="eyebrow">{product.garment_type}</p>
            <h1>{product.name}</h1>
            <p className="price detail-price">{formatPrice(product.price)}</p>
            <p className="description">{product.description}</p>
            {product.colors.length > 0 ? (
              <p className="colors">Colors: {product.colors.join(', ')}</p>
            ) : null}
            <h2>Sizes and stock</h2>
            <p className="page-note">Counts refresh while this page is open, and again when someone buys.</p>
            {product.sizes.length > 0 ? (
              <ul className="size-list">
                {product.sizes.map((stock) => (
                  <li key={stock.size}>
                    <span>{stock.size}</span>
                    <span>
                      {stock.quantity === 0
                        ? 'Out of stock'
                        : `${stock.quantity} available`}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No size counts are stored for this item.</p>
            )}
            {shopper ? (
              <form className="account-form buy-form" onSubmit={onBuy}>
                <label>
                  Size
                  <select value={size} onChange={(event) => setSize(event.target.value)}>
                    <option value="">Choose a size</option>
                    {product.sizes.map((stock) => (
                      <option key={stock.size} value={stock.size} disabled={stock.quantity === 0}>
                        {stock.size}
                        {stock.quantity === 0 ? ' — sold out' : ` — ${stock.quantity} left`}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Color
                  <select value={color} onChange={(event) => setColor(event.target.value)}>
                    <option value="">Choose a color</option>
                    {product.colors.map((offered) => (
                      <option key={offered} value={offered}>
                        {offered}
                      </option>
                    ))}
                  </select>
                </label>
                <button className="button" type="submit" disabled={!canBuy}>
                  {busy ? 'Working…' : 'Buy this size'}
                </button>
                {buyNote ? <p className="form-note">{buyNote}</p> : null}
              </form>
            ) : (
              <p className="page-note">
                <Link to="/login">Log in</Link> to buy. A sold-out size cannot be purchased.
              </p>
            )}
            {order && order.status !== 'shipped' ? (
              <button className="button" type="button" onClick={onShip} disabled={busy}>
                Mark order shipped
              </button>
            ) : null}
            {shippedEmail ? (
              <div className="email-preview">
                <p className="eyebrow">Shipping email</p>
                <pre>{shippedEmail}</pre>
              </div>
            ) : null}
          </div>
        </article>
      ) : null}
    </div>
  )
}
