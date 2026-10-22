import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { CampusGallery } from '../components/CampusGallery.tsx'
import { fetchProducts } from '../api.ts'
import { useAuth } from '../auth.tsx'
import { formatPrice } from '../format.ts'
import type { Product } from '../types.ts'

export function HomePage() {
  const { shopper } = useAuth()
  const [preview, setPreview] = useState<Product[]>([])
  const savedSize = shopper?.preferred_size ?? ''

  useEffect(() => {
    let ignore = false
    fetchProducts(savedSize)
      .then((products) => {
        if (!ignore) {
          setPreview(products.filter((product) => product.colors.length > 0).slice(0, 3))
        }
      })
      .catch(() => {
        if (!ignore) {
          setPreview([])
        }
      })
    return () => {
      ignore = true
    }
  }, [savedSize])

  return (
    <div className="page home-page">
      <section className="hero">
        <p className="eyebrow">A Broadway shop for Yale clothing</p>
        <h1>The rack, before you cross the street.</h1>
        <p className="lede">
          Campus Customs keeps sweatshirts, college crests, team layers, and
          family pieces in one room in New Haven. This site is that room written
          down: the photo from the catalogue, the price on the tag, and a way to
          see which sizes are still on the shelf.
        </p>
        <Link className="button" to="/products">
          Browse the garments
        </Link>
      </section>

      <section className="story-grid" aria-label="What the shop carries">
        <article>
          <h2>College marks</h2>
          <p>
            Quarter-zips and crewnecks carry a residential college crest on the
            chest. The big Yale wordmark sits on its own pile, for days when the
            lettering should be the whole design.
          </p>
        </article>
        <article>
          <h2>Team layers</h2>
          <p>
            Baseball, hockey, football, and the other squads each have a
            left-chest mark. The product page says how many of each size are
            left, including a zero when that size is gone.
          </p>
        </article>
        <article>
          <h2>The family shelf</h2>
          <p>
            Parents, grandparents, and the rest of a visit have garments that
            name them outright. Pick one before the weekend, or stop in with the
            student.
          </p>
        </article>
      </section>

      <CampusGallery />

      {preview.length > 0 ? (
        <section className="preview">
          <div className="section-heading">
            <h2>{savedSize ? 'In your saved size' : 'Three pieces from the catalogue'}</h2>
            <Link to="/products">See every item</Link>
          </div>
          <div className="preview-row">
            {preview.map((product) => (
              <Link
                key={product.product_id}
                to={`/products/${product.product_id}`}
                className="preview-card"
              >
                <img
                  src={`/${product.image_file_path}`}
                  alt={product.name}
                />
                <span>{product.name}</span>
                <strong>{formatPrice(product.price)}</strong>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}
