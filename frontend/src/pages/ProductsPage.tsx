import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts } from '../api.ts'
import { useAuth } from '../auth.tsx'
import { useCatalogue } from '../catalogue.tsx'
import { formatPrice, shortDescription } from '../format.ts'
import type { Product } from '../types.ts'

const sizeNames: Record<string, string> = {
  XS: 'extra small',
  S: 'small',
  M: 'medium',
  L: 'large',
  XL: 'extra large',
  XXL: 'XXL',
}

export function ProductsPage() {
  const { shopper } = useAuth()
  const { query, matches, clearMatches } = useCatalogue()
  const [products, setProducts] = useState<Product[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [showAll, setShowAll] = useState(false)
  const savedSize = shopper?.preferred_size ?? ''
  const activeSize = showAll ? '' : savedSize

  useEffect(() => {
    let ignore = false
    setLoading(true)
    fetchProducts(activeSize)
      .then((rows) => {
        if (!ignore) {
          setProducts(rows)
        }
      })
      .catch((reason: unknown) => {
        if (!ignore) {
          setError(reason instanceof Error ? reason.message : 'Could not load the catalogue')
        }
      })
      .finally(() => {
        if (!ignore) {
          setLoading(false)
        }
      })
    return () => {
      ignore = true
    }
  }, [activeSize])

  const showingMatches = matches !== null
  const availableIds = new Set(products.map((product) => product.product_id))
  const visibleMatches =
    showingMatches && activeSize
      ? matches.filter((match) => availableIds.has(match.product_id))
      : matches

  return (
    <div className="page">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Products</p>
          <h1>{showingMatches ? 'Matching items' : 'The catalogue'}</h1>
        </div>
        {showingMatches ? (
          <button type="button" className="text-button" onClick={clearMatches}>
            Show the full catalogue
          </button>
        ) : savedSize ? (
          <button type="button" className="text-button" onClick={() => setShowAll((current) => !current)}>
            {showAll ? `Show ${sizeNames[savedSize] ?? savedSize} only` : 'Show every size'}
          </button>
        ) : null}
      </div>
      {showingMatches ? (
        <p className="page-note">
          For “{query}”. Each card uses the photo, name, price, and short
          description from the catalogue. Open a card for the full description
          and the sizes in stock.
        </p>
      ) : (
        <p className="page-note">
          {activeSize
            ? `Showing pieces with ${sizeNames[activeSize] ?? activeSize} still in stock, the size saved when you logged in.`
            : 'Each card uses the photo path stored with that product. Open a card for the full description and the sizes in stock.'}
        </p>
      )}
      {!showingMatches && loading ? <p className="status">Loading the catalogue…</p> : null}
      {error ? <p className="status error">{error}</p> : null}
      <div className="product-grid">
        {showingMatches
          ? (visibleMatches ?? []).map((match) => (
              <Link
                key={match.product_id}
                to={`/products/${match.product_id}`}
                className="product-card"
              >
                <img src={`/${match.image_file_path}`} alt={match.name} />
                <div className="card-copy">
                  <h2>{match.name}</h2>
                  <p className="price">{formatPrice(match.price)}</p>
                  <p>{match.short_description}</p>
                </div>
              </Link>
            ))
          : products.map((product) => (
              <Link
                key={product.product_id}
                to={`/products/${product.product_id}`}
                className="product-card"
              >
                <img src={`/${product.image_file_path}`} alt={product.name} />
                <div className="card-copy">
                  <h2>{product.name}</h2>
                  <p className="price">{formatPrice(product.price)}</p>
                  <p>{shortDescription(product.description)}</p>
                </div>
              </Link>
            ))}
      </div>
    </div>
  )
}
