#!/usr/bin/env node
/**
 * Optional Netlify build step: download the recitation if RECITATION_URL is set.
 * The MP3 is not stored in git (copyright). Drop audio/recitation.mp3 locally,
 * or set RECITATION_URL in the Netlify UI to a direct link you control.
 */
import { mkdir, writeFile, access } from "node:fs/promises";
import { constants } from "node:fs";

const dest = new URL("../audio/recitation.mp3", import.meta.url);
await mkdir(new URL("../audio/", import.meta.url), { recursive: true });

const url = process.env.RECITATION_URL;
if (!url) {
  try {
    await access(dest, constants.R_OK);
    console.log("Using existing audio/recitation.mp3");
  } catch {
    console.log(
      "No recitation bundled. Add audio/recitation.mp3 or set RECITATION_URL."
    );
  }
  process.exit(0);
}

const res = await fetch(url);
if (!res.ok) {
  throw new Error(`Could not download recitation (${res.status})`);
}
const buf = Buffer.from(await res.arrayBuffer());
await writeFile(dest, buf);
console.log(`Wrote audio/recitation.mp3 (${buf.length} bytes)`);
