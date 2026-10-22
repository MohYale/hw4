const places = [
  {
    src: '/campus/harkness.jpg',
    name: 'Harkness Tower',
    credit: 'Public domain',
    href: 'https://commons.wikimedia.org/wiki/File:Harkness_Tower_in_full.jpg',
  },
  {
    src: '/campus/cross-campus.jpg',
    name: 'Cross Campus',
    credit: 'Carol M. Highsmith, public domain',
    href: 'https://commons.wikimedia.org/wiki/File:Cross_Campus_Highsmith.jpg',
  },
  {
    src: '/campus/evans-hall.jpg',
    name: 'Evans Hall',
    credit: 'Nick Allen, CC BY-SA 3.0',
    href: 'https://commons.wikimedia.org/wiki/File:Yale_School_of_Management_Evans_Hall_front.JPG',
  },
  {
    src: '/campus/old-campus.jpg',
    name: 'Old Campus',
    credit: 'Carol M. Highsmith, public domain',
    href: 'https://commons.wikimedia.org/wiki/File:Dwight_Hall_Woolsey_statue_Highsmith.jpg',
  },
  {
    src: '/campus/medical-school.jpg',
    name: 'Yale School of Medicine',
    credit: 'Ajay Suresh, CC BY 2.0',
    href: 'https://commons.wikimedia.org/wiki/File:Yale_School_of_Medicine_(54106346034).jpg',
  },
  {
    src: '/campus/payne-whitney.jpg',
    name: 'Payne Whitney Gym',
    credit: 'Public domain',
    href: 'https://commons.wikimedia.org/wiki/File:Yale_Cathedral_of_Sweat.JPG',
  },
]

export function CampusGallery() {
  return (
    <section className="campus-gallery" aria-label="Yale University">
      <div className="section-heading">
        <h2>The university around the shop</h2>
      </div>
      <p className="page-note">
        Harkness Tower, Cross Campus, Evans Hall, Old Campus, the School of
        Medicine, and Payne Whitney Gym. These photographs are of the university
        itself.
      </p>
      <div className="campus-grid">
        {places.map((place) => (
          <figure key={place.src}>
            <img src={place.src} alt={place.name} />
            <figcaption>
              <strong>{place.name}</strong>
              <span>
                <a href={place.href}>{place.credit}</a>
              </span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  )
}
