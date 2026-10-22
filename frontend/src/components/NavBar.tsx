import { NavLink } from 'react-router-dom'
import { useAuth } from '../auth.tsx'

const links = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About us', end: false },
]

function itemClass(isActive: boolean): string {
  return isActive ? 'nav-link active' : 'nav-link'
}

export function NavBar() {
  const { shopper, setShopper } = useAuth()

  return (
    <header className="site-header">
      <nav className="nav-bar" aria-label="Main">
        <NavLink to="/" className="brand" end>
          Campus Customs
        </NavLink>
        <div className="nav-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => itemClass(isActive)}
            >
              {link.label}
            </NavLink>
          ))}
        </div>
        <div className="nav-account">
          {shopper ? (
            <>
              <span className="nav-hello">{shopper.first_name}</span>
              <button type="button" className="nav-link" onClick={() => setShopper(null)}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={({ isActive }) => itemClass(isActive)}>
                Log in
              </NavLink>
              <NavLink
                to="/create-account"
                className={({ isActive }) =>
                  isActive ? 'nav-link account active' : 'nav-link account'
                }
              >
                Create account
              </NavLink>
            </>
          )}
        </div>
      </nav>
    </header>
  )
}
