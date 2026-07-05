import { useState, useEffect, useCallback } from 'react'
import './HeroBanner.css'

const BACKDROP_BASE = 'https://image.tmdb.org/t/p/original'
const ROTATE_MS = 6000

export default function HeroBanner({ movies, genres, onSelect }) {
  const [index, setIndex] = useState(0)

  const next = useCallback(() => {
    setIndex(i => (i + 1) % movies.length)
  }, [movies.length])

  useEffect(() => {
    const timer = setInterval(next, ROTATE_MS)
    return () => clearInterval(timer)
  }, [next])

  if (!movies || movies.length === 0) return null

  const movie = movies[index]
  const year = movie.release_date?.slice(0, 4) ?? '—'
  const movieGenres = (movie.genre_ids ?? []).slice(0, 3).map(id => genres[id]).filter(Boolean)

  return (
    <div className="hero">
      {movie.backdrop_path && (
        <img
          key={movie.id}
          className="hero-backdrop"
          src={`${BACKDROP_BASE}${movie.backdrop_path}`}
          alt=""
        />
      )}
      <div className="hero-gradient" />

      <div className="hero-content">
        {movieGenres.length > 0 && (
          <div className="hero-genres">
            {movieGenres.map(g => (
              <span key={g} className="hero-genre-pill">{g}</span>
            ))}
          </div>
        )}

        <h1 className="hero-title">{movie.title}</h1>

        <div className="hero-meta">
          <span className="hero-rating">★ {movie.vote_average.toFixed(1)}</span>
          <span className="hero-year">{year}</span>
          {movie.runtime && (
            <span className="hero-year">{Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m</span>
          )}
        </div>

        <p className="hero-overview">{movie.overview}</p>

        <div className="hero-ctas">
          <button className="hero-btn-play">▶ Play</button>
          <button className="hero-btn-info" onClick={() => onSelect(movie)}>ℹ More Info</button>
        </div>
      </div>

      <div className="hero-dots">
        {movies.map((_, i) => (
          <button
            key={i}
            className={`hero-dot${i === index ? ' active' : ''}`}
            onClick={() => setIndex(i)}
            aria-label={`Show movie ${i + 1}`}
          />
        ))}
      </div>
    </div>
  )
}
