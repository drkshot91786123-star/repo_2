import './MovieCard.css'

const IMG_BASE = 'https://image.tmdb.org/t/p/w500'

export default function MovieCard({ movie, genres, onSelect }) {
  const year = movie.release_date?.slice(0, 4) ?? '—'
  const primaryGenre = genres[movie.genre_ids?.[0]] ?? ''

  return (
    <div className="movie-card" onClick={() => onSelect(movie)}>
      {movie.poster_path ? (
        <img
          src={`${IMG_BASE}${movie.poster_path}`}
          alt={movie.title}
          loading="lazy"
        />
      ) : (
        <div className="movie-card-img-placeholder">{movie.title}</div>
      )}
      <div className="movie-card-overlay">
        <div className="movie-card-title">{movie.title}</div>
        <div className="movie-card-meta">
          <span className="movie-card-rating">★ {movie.vote_average.toFixed(1)}</span>
          <span>{year}</span>
          {primaryGenre && <span>{primaryGenre}</span>}
        </div>
      </div>
    </div>
  )
}
