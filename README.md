# Śrī Viṣṇu Sahasranāmam

A quiet progressive web app for sitting with the thousand names of Vishnu.

It has two paths:

1. **Learn** — one śloka at a time. Sanskrit, simple English, the names in that verse, and the matching stretch of M. S. Subbulakshmi’s recitation.
2. **Listen** — a teleprompter. The verses rise as the full recitation plays, so the eye stays with the ear.

The design is meant to feel like a small inner shrine: lamp-light, gold, unhurried type. No clutter.

## Recitation audio

M. S. Subbulakshmi’s recording is still under copyright, so it is **not bundled** in this repository. Load your own copy in **Settings** (the familiar Saregama recitation of about thirty minutes). The file stays on your device in IndexedDB and can be used offline.

If the verses drift from her voice, open Settings and tap **Mark names start now** when you hear *Vishvam Vishnur…*, then **Mark names end now** at *Vanamālī…*.

## Run locally

The app is static. From this folder:

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
