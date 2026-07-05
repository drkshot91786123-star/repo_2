import { useState } from 'react'
import { movies, genres, FEATURED_IDS } from '../data/movies.js'
import HeroBanner from '../components/HeroBanner.jsx'
import MovieRow from '../components/MovieRow.jsx'
import MovieModal from '../components/MovieModal.jsx'

const featuredMovies = FEATURED_IDS.map(id => movies.find(m => m.id === id)).filter(Boolean)

const rows = [
  { title: 'Trending Now', movies: movies.slice(0, 8) },
  { title: 'Top Rated', movies: [...movies].sort((a, b) => b.vote_average - a.vote_average).slice(0, 10) },
  { title: 'Action', movies: movies.filter(m => m.genre_ids.includes(28)) },
  { title: 'Drama', movies: movies.filter(m => m.genre_ids.includes(18)) },
  { title: 'Sci-Fi', movies: movies.filter(m => m.genre_ids.includes(878)) },
  { title: 'Crime & Thriller', movies: movies.filter(m => m.genre_ids.includes(80) || m.genre_ids.includes(53)) },
]

export default function Home() {
  const [selected, setSelected] = useState(null)

  return (
    <main>
      <HeroBanner movies={featuredMovies} genres={genres} onSelect={setSelected} />

      {rows.map(row =>
        row.movies.length > 0 && (
          <MovieRow
            key={row.title}
            title={row.title}
            movies={row.movies}
            genres={genres}
            onSelect={setSelected}
          />
        )
      )}

      {selected && (
        <MovieModal movie={selected} genres={genres} onClose={() => setSelected(null)} />
      )}
    </main>
  )
}
