<p align="center"><img src="assets/social-card.png" alt="Susanna's Music Movie Brain" width="720"></p>

# 🎭 Susanna's Music Movie Brain

**Overture! Curtain up on 5,700 music films, docs, concerts and series. Pick your mood, find your next showstopper, and never run out of encores.**

**▶ Now playing: [ohsusannamarie.github.io/music-movie-brain](https://ohsusannamarie.github.io/music-movie-brain/)**

## The cast

| Act | What it does |
|---|---|
| **Surprise me** | Three picks every tap: a Safest bet, a Hidden gem and a Wild card |
| **Tonight switches** | One tap for On my services or Half-watching, applied everywhere in Discover |
| **Why you'll love it** | Every pick explains its link to a favorite, plus an honest heads-up when it shares what your skips have in common |
| **Vibe dial** | Eight moods (Car belt-along, The good cry, Kitchen dance party...) that serve three picks tuned to your ratings |
| **Mood mixer** | Stack moods, sounds and kinds, then drop the needle |
| **Library** | Every title: 238 curated, the 1,000 most-watched hand-tagged, the rest auto-tagged, with US streaming for each |
| **Artists** | 228 artist pages: every biopic, doc, concert film and series about them |
| **Series** | Music TV, from Glee to Daisy Jones & The Six and 79 more |
| **What's new** | Just landed on your services, left your services, new releases and a Coming soon radar with auto-queue |
| **Rabbit holes & double features** | Curated viewing paths and pairings that argue with each other |
| **My taste** | What your favorites share, what loses you (with thumbs-down reasons), and backup and restore |

## Backstage

- One static page (`index.html`) plus a weekly data file (`fresh.js`).
- Every Thursday night a GitHub Action runs `refresh/refresh.py`: it re-checks US streaming for ~4,100 titles on TMDB (JustWatch data), adds new music releases, updates the release radar, diffs against last week, commits `fresh.js` and republishes the site.
- Run it by hand any time: **Actions → Refresh and publish → Run workflow**.
- Needs one repository secret, `TMDB_KEY` (a TMDB v3 API key).
- Seen, queue, ratings, reasons and watch dates live in your browser's local storage. Back them up from **My taste → Your data** (download or copy a code), and restore with Merge or Replace. Installable to your home screen, and works offline after the first visit.

<sub>This product uses the TMDB API but is not endorsed or certified by TMDB. Streaming availability from JustWatch via TMDB.</sub>
