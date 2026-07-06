# Cinemap — Static React Movie Site

**Date:** 2026-07-05  
**Status:** Approved

## Overview

A static React movie discovery site inspired by Cineby, focused on movies only. Lives in `cinemap/` folder at the repo root. No backend, no API calls — all data is hardcoded mock data shaped like the TMDB API response format.

## Tech Stack

- **Vite + React** (no SSR, no router needed for v1)
- **Plain CSS** (index.css + component-level style objects or CSS modules)
- **No external dependencies** beyond React and Vite

## Folder Structure

```
cinemap/
├── src/
│   ├── data/
│   │   └── movies.js          # ~30 TMDB-shaped movie objects + genre map
│   ├── components/
│   │   ├── Navbar.jsx
│   │   ├── HeroBanner.jsx
│   │   ├── MovieRow.jsx
│   │   ├── MovieCard.jsx
│   │   └── MovieModal.jsx
│   ├── pages/
│   │   └── Home.jsx
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── index.html
├── package.json
└── vite.config.js
```

## Data Model

Each movie object is TMDB-shaped to allow easy real-API swap later:

```js
{
  id: 550,
  title: "Fight Club",
  overview: "A ticking-time-bomb insomniac...",
  poster_path: "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
  backdrop_path: "/hZkgoQYus5vegHoetLkCJzVPrWl.jpg",
  release_date: "1999-10-15",
  vote_average: 8.4,
  vote_count: 26280,
  genre_ids: [18, 53],
  runtime: 139,
  tagline: "Mischief. Mayhem. Soap."
}
```

- Posters served from `https://image.tmdb.org/t/p/w500{poster_path}` — public CDN, no API key needed
- Backdrops from `https://image.tmdb.org/t/p/original{backdrop_path}`
- Genre IDs match TMDB's official genre list (28=Action, 18=Drama, 878=Sci-Fi, etc.)

## Rows (Home page)

| Row Title | Source |
|-----------|--------|
| Trending Now | first 6 movies |
| Top Rated | movies sorted by vote_average desc |
| Action | movies filtered by genre_id 28 |
| Drama | movies filtered by genre_id 18 |
| Sci-Fi | movies filtered by genre_id 878 |

## Components

**Navbar**
- Sticky dark bar
- "Cinemap" logo (left)
- Search icon + Browse text (right, no-op for v1)

**HeroBanner**
- Full-bleed backdrop of featured movie
- Auto-rotates every 5s through 3 hardcoded featured movies
- Overlaid: title, star rating, year, genre pills, truncated synopsis
- Two CTAs: `▶ Play` (no-op) and `ℹ More Info` (opens MovieModal)

**MovieRow**
- Section label with red left-border accent
- Horizontal scroll with prev/next arrow buttons
- Renders a list of MovieCard components

**MovieCard**
- Poster image
- On hover: scale up slightly + dark overlay showing title + rating
- Click → opens MovieModal

**MovieModal**
- Full-screen semi-transparent overlay
- Backdrop image as background
- Left: poster thumbnail
- Right: title, tagline, rating, runtime, genres, full overview
- `✕` button closes modal
- Click outside modal → close

## Visual Design

- Background: `#0d0d0d`
- Primary accent: `#e50914` (red)
- Text: `#ffffff` primary, `#aaaaaa` secondary
- Font: system sans-serif stack
- Card hover: `scale(1.05)` with `transition: transform 0.2s`
- Modal backdrop: `rgba(0,0,0,0.85)`

## Out of Scope (v1)

- Real API integration
- Routing / dedicated movie pages
- Search functionality
- Login / watchlist
- Trailers / video embeds
