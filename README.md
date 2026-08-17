# Śrī Viṣṇu Sahasranāmam

A quiet progressive web app for sitting with the thousand names of Vishnu.

It has two paths:

1. **Learn** — one verse at a time, from *Śuklāmbaradharam* through dhyānam and the 108 name-ślokas. Sanskrit, simple English, the names in that verse, and the matching stretch of M. S. Subbulakshmi’s recitation, which starts and stops with that verse.
2. **Listen** — a teleprompter synced to her recording (opening, dhyānam, the thousand names, phalaśruti). The Mahābhārata *pūrva pīṭhikā* is not in her recitation, so it is not shown here.

The design is meant to feel like a small inner shrine: lamp-light, gold, unhurried type. No clutter.

## Recitation audio

M. S. Subbulakshmi’s recording is still under copyright, so it is **not stored in GitHub**. Use a copy you already have.

The app plays `audio/recitation.mp3` automatically when that file is present on the site. You can also load a file in **Settings**; it stays on that device only.

If the thousand names drift from her voice, open Settings and tap **Mark names start now** when you hear *Vishvam Vishnur…*, then **Mark names end now** at *Vanamālī…*.

## Deploy on Netlify

This is a static site. The fastest path:

1. In [Netlify](https://app.netlify.com), choose **Add new site → Import an existing project**.
2. Connect the GitHub repo `sudhamanc/VishnuSahasranamam`.
3. Use these settings (already in `netlify.toml`):
   - **Build command:** `node scripts/prepare-audio.mjs`
   - **Publish directory:** `.`
4. Deploy.

Then add the recitation in one of these ways (pick one):

**A. Environment variable (works with Git deploys)**  
Site settings → Environment variables → add `RECITATION_URL` with a direct link to your MP3. Trigger a new deploy. The build copies the file into `audio/recitation.mp3` on Netlify only.

**B. Netlify Drop / CLI (file never goes to GitHub)**  
Copy your MP3 to `audio/recitation.mp3` on your computer, then:

```bash
npx netlify-cli login
npx netlify-cli init
npx netlify-cli deploy --prod --dir .
```

Or drag the project folder onto [app.netlify.com/drop](https://app.netlify.com/drop).

Until the MP3 is on the site, visitors can still load it in Settings.

For a household shrine, consider Netlify **password protection** so the recording is not openly indexed.

## Run locally

```bash
python3 -m http.server 4173
```

Open [http://localhost:4173](http://localhost:4173). On a phone, add it to the home screen from the browser share sheet.

## Content

The stotram text follows the widely recited Mahābhārata recension (Anushāsana Parva). English explanations are written in plain language as a doorway for learners, not as a replacement for Śaṅkara, Parāśara Bhaṭṭar, or other traditional commentaries.

Rebuild the data file after editing `scripts/build_data.py`:

```bash
python3 scripts/build_data.py
```
