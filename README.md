# The Core Edge player

The Core Edge order bump, as an app: six core circuits of three exercises, start and end photos
for every move, demos that play inside the page, Play mode with the plank timer and rest timer,
list view, print pages, and a home-screen icon. Built from the Youth Athlete Edge player.

- `data/core.json` holds the program: one group, six workouts, every exercise with its name, note,
  YouTube demo and photos.
- `start.html` home page (next workout, when to do these, the six workouts).
- `index.html` list view (`#core-3` locks one workout, `#all` shows the picker), `play.html` play mode,
  `print.html` one page per workout, `install.html` add-to-home-screen guide.

Live at `https://michellemariefit.github.io/core-edge-player/`.

## Rebuilding

`tools/build_workouts.py` reads `tools/pdf/core.pdf` (from Dropbox, PRODUCTS & PROGRAMS / The Core Edge)
and writes `data/core.json`. `tools/match_sources.py` and `tools/grab_frames.py` make the start and end
photos from the recordings in `tools/cache/` (Dropbox, The Core Edge / EXERCISE VIDEOS). Hand picks go in
`tools/overrides.json`. `tools/review.html` shows every pair.
