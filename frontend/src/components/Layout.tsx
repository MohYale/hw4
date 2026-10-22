import { Outlet } from 'react-router-dom'
import { ChatWidget } from './ChatWidget.tsx'
import { HandsomeDan } from './HandsomeDan.tsx'
import { NavBar } from './NavBar.tsx'

export function Layout() {
  return (
    <>
      <NavBar />
      <main>
        <Outlet />
      </main>
      <footer className="site-footer">
        <p>Campus Customs · 57 Broadway, New Haven</p>
      </footer>
      <HandsomeDan />
      <ChatWidget />
    </>
  )
}
