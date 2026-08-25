# Śrī Viṣṇu Sahasranāmam

A quiet progressive web app for sitting with the thousand names of Vishnu.

It has two paths:

1. **Learn** — one verse at a time, from *Śuklāmbaradharam* through the whole recitation. Sanskrit, simple English, the names in that verse, and the matching stretch of M. S. Subbulakshmi’s recording, which starts and stops with that verse.
2. **Listen** — a teleprompter synced to her recording. The script follows exactly what she sings, in her order: opening verses, the Bhīṣma–Yudhiṣṭhira dialogue, the nyāsa, dhyānam, the 108 name-ślokas, and the phalaśruti.

Every verse carries a measured timestamp from her 29:41 recording (derived by breath-gap analysis and speech alignment), so both views stay on her voice without any manual timing.

The design is meant to feel like a small inner shrine: lamp-light, gold, unhurried type. No clutter.

## Recitation audio

M. S. Subbulakshmi’s recording is still under copyright, so it is **not stored in GitHub**. Use a copy you already have.

The app plays `audio/recitation.mp3` automatically when that file is present on the site. You can also load a file in **Settings**; it stays on that device only.

If your copy of the recording has extra leading silence, open Settings and tap **She is starting Viśvam now** at the first name-śloka, or type a timing nudge in seconds.

To re-derive the per-verse timestamps (only needed for a different recording), see `scripts/make_timing.py`, then run `scripts/build_data.py`.

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

## How did Fable 5, Opus 5 and Grok 4.6 make this happen (I used a combination of all this) - The model speaks here

The MP3 was already in the repo from your upload. I treated it as a tape: find every pause, guess what she is saying in a few places, then count pauses between those landmarks.

1. Get a waveform you can measure

The file is ~29:41. I decoded it to a plain WAV so the tools could look at amplitude over time, not MP3 frames.

2. Find the breaths (this did most of the work)

She chants against tanpura. Between phrases there is a short dip of about 0.3–0.6 seconds — not true silence, but quieter than singing.

ffmpeg’s silencedetect looks for stretches below a loudness threshold. I ran it twice:

A coarser pass (−27 dB) for the opening, dialogue, dhyānam, and phalaśruti, where verses are longer and less regular.
A finer pass (−24 dB, at least 0.28 s) for the 108 name-ślokas. That pass found 211 breaths between the start of Viśvaṃ Viṣṇur… (~6:43) and the start of śloka 107.
Those breaths fall on half-lines: first pāda, breath, second pāda, breath, next śloka. A normal name-śloka is two breaths. That is the clock.

3. Speech recognition as a landmark, not as the clock

I ran faster-whisper, an open-source speech-to-text model (same family as OpenAI Whisper). The first time it is used, it downloads weights from Hugging Face — that is the “downloaded a model” part. After that it lives on the machine.

I used small for the whole track, then medium / large-v3 on a few stubborn windows.

It is a poor Sanskrit + tanpura transcriber. Output was often gibberish (Akshara Akshara, English hallucinations). What it did give, when it worked, was word timestamps: “something that sounds like sarvagaḥ starts around 525.4 s.”

I compared those fragments to the IAST of each śloka with fuzzy string matching (so typos still hit the right verse). That produced anchors: “I am fairly sure śloka 10 starts at this breath, 23 at this one, 71 at this one.”

4. First attempt: interpolate between anchors (this is what drifted)

Between two solid anchors I used dynamic programming: pick a chain of breaths such that the time from one śloka-start to the next is about 8–9 seconds (her usual pace).

That fails when she changes speed. Śloka 1 is slow (~12 s, three breaths). Śloka 14 is almost double-time in one breath (~3.2 s). The interpolator assumed “every verse ≈ two equal breaths,” so from about śloka 14 it sat a half-line early: clip starts on the previous verse’s last words and cuts the current one short. Toward the end, later anchors pulled it back into line — which matches what you heard.

5. What I actually shipped for the names

Once the breath list was clean, I stopped interpolating and counted:

Śloka 1: 3 segments (extra pause in the first verse).
Ślokas 14 and 53: 1 breath each (sung compressed).
Every other name-śloka: 2 breaths.
Śloka 107 includes the sung oṃ nama iti tail, then a pause, then Vanamālī three times as śloka 108.
That uses 211 breaths exactly. I then checked ~16 landmarks from the transcript (ślokas 2, 10, 15, 23, 47, 55, 71, 89, 102, …) so a missed extra pause would have thrown every later number off. They lined up.

6. Opening, dialogue, dhyānam, phalaśruti

Those are not in a 2-breath grid. For those I used the coarser pauses plus the (better) Whisper read of the preamble: Śuklāmbaradharam at ~2 s, kimekaṃ daivataṃ around 1:10, nyāsa ~3:33, dhyānam ~4:27, long silence, then names at 6:43. Each of those verses got a start = end of previous breath, end = start of next breath.

7. What the app does with that table

mss_timing.json is just a list of (start, end) in seconds for all 171 sung verses. Learn mode seeks to start − 0.1 s and stops at end + 0.15 s (a little decay, not into the next line). The teleprompter highlights whichever verse contains currentTime.

So: breaths = the ruler, Whisper = occasional street signs, counting between signs = the map. The “magic” that broke in the middle was the interpolator pretending every śloka is the same length. The fix was to stop guessing length and follow the breaths she actually took.

## Content

The stotram text follows the widely recited Mahābhārata recension (Anushāsana Parva). English explanations are written in plain language as a doorway for learners, not as a replacement for Śaṅkara, Parāśara Bhaṭṭar, or other traditional commentaries.

Each śloka carries only its own names. `NAME_RANGES` in `scripts/build_data.py`
records where every verse sits in the list of a thousand names; it was derived by
aligning each name in `scripts/source/names_1000.json` against the verse it is
drawn from, rather than by counting words by eye.

Rebuild the data file after editing `scripts/build_data.py`, then check the
grouping still holds:

```bash
python3 scripts/build_data.py
python3 scripts/check_name_ranges.py
```

`check_name_ranges.py` strips each verse and its names down to a consonant
skeleton and reads the names back against the verse, so a name that has drifted
into a neighbouring śloka fails loudly instead of sitting there unnoticed.
