# AGENTS.md

## Cursor Cloud specific instructions

This repo is a **fully static, dependency-free Progressive Web App** for learning the Śrī Viṣṇu Sahasranāmam. There is no build system, no package manager lockfile, no automated test suite, and no lint tooling. Vanilla JS is loaded directly via `<script>` tags in `index.html`; Python is only used offline to regenerate data files.

### Services / how to run

- **Dev server (the app):** serve the repo root as static files. Use `npm start` (which runs `python3 -m http.server 4173`) or `python3 -m http.server 4173`, then open `http://localhost:4173/`. This is the only long-running service. Node 22 and Python 3.12 are already available.
- The app is served from the repository root — do not use a `src/` or `dist/` directory; there is no bundling step.

### Lint / test / build

- **Lint:** none configured.
- **Test:** no automated test suite. Verify changes manually in the browser (Learn view renders a verse; Listen view teleprompter scrolls with audio).
- **Build:** `npm run build` runs `node scripts/prepare-audio.mjs`. This is an optional Netlify helper, NOT a real bundling step — it only ensures `audio/recitation.mp3` exists, downloading it from the `RECITATION_URL` env var when set. It exits 0 cleanly when neither the file nor the URL is present. The site runs fine without it.

### Non-obvious caveats

- **Recitation audio is gitignored** (`audio/*.mp3`, copyright — M. S. Subbulakshmi). It is NOT committed, so fresh VMs will not have it unless `RECITATION_URL` is set (see `scripts/prepare-audio.mjs`) or a file is placed at `audio/recitation.mp3`. The app degrades gracefully without audio: the Learn view still shows verses/meanings and the "Mark as learned" progress flow works; only playback/teleprompter sync need the MP3. Do not treat a missing MP3 as a broken environment.
- **Regenerating data is optional and rarely needed.** `data/stotram.js` is committed and consumed directly by the app. `python3 scripts/build_data.py` rebuilds it from `scripts/source/*`. `scripts/make_timing.py` re-derives per-verse timestamps and requires `rapidfuzz` plus external inputs in `/tmp` (ffmpeg silencedetect + whisper output); it is only for re-deriving cues against a different recording and is not part of normal development.
- **Service worker (`sw.js`) caches aggressively.** When editing JS/CSS/HTML during development, hard-reload (or clear the SW/cache) so you see changes rather than the cached version.
