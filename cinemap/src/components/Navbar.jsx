import { useState, useEffect } from 'react'
import './Navbar.css'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll)
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <nav className={`navbar${scrolled ? ' scrolled' : ''}`}>
      <a href="/" className="navbar-logo">
        <div className="navbar-logo-icon">C</div>
        <span className="navbar-logo-text">Cinemap</span>
      </a>
      <div className="navbar-right">
        <a href="#" className="navbar-link">Home</a>
        <a href="#" className="navbar-link">Browse</a>
        <button className="navbar-search-btn" aria-label="Search">⌕</button>
      </div>
    </nav>
  )
}
