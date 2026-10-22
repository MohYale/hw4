import { CampusGallery } from '../components/CampusGallery.tsx'

export function AboutPage() {
  return (
    <div className="page about-page">
      <p className="eyebrow">About us</p>
      <h1>A counter on Broadway, with the stock written out.</h1>
      <p className="lede">
        Campus Customs is the New Haven shop at 57 Broadway. People come in
        between classes, before a game, or with family in town for a weekend.
        The point of this site is to let you look through that same clothing
        without guessing what is hanging up.
      </p>

      <section>
        <h2>Who it is for</h2>
        <p>
          Students wear a college crest, a school mark, or a team name. Families
          want a hoodie or crewneck that says mom, dad, or grandparent without
          making them hunt through a rack. Graduate and professional schools have
          their own crests in the same room. None of that needs a slogan. It
          needs a clear photo and an honest size count.
        </p>
      </section>

      <section>
        <h2>What you can do here</h2>
        <p>
          Open the product list and you will see the catalogue photo, the name,
          the price, and a short line about the garment. Open one item and the
          photo gets larger, the full description sits beside it, and each size
          shows how many are left to buy. If a size is at zero, it stays on the
          page so you do not walk over for it.
        </p>
      </section>

      <section>
        <h2>The room itself</h2>
        <p>
          The shop is still a shop. This website does not replace the counter.
          It is the list you can read first, then carry down Broadway if you
          want to try something on.
        </p>
      </section>

      <CampusGallery />
    </div>
  )
}
