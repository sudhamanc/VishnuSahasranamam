const Recitation = (() => {
  const audio = () => document.getElementById("recitation");
  let objectUrl = null;
  let timeline = [];
  let wakeLock = null;
  let rangeTimer = 0;
  let rangeSeeking = false;

  const BUNDLED_CANDIDATES = [
    "./audio/recitation.mp3",
    "./audio/recitation.m4a",
    "./audio/ms-subbulakshmi.mp3",
  ];

  function hasSource() {
    return Boolean(audio().getAttribute("src"));
  }

  function duration() {
    const d = audio().duration;
    return Number.isFinite(d) && d > 0 ? d : window.STOTRAM.meta.timing.duration;
  }

  function current() {
    return audio().currentTime || 0;
  }

  function playing() {
    return !audio().paused && !audio().ended;
  }

  function waitForAudio() {
    const el = audio();
    return new Promise((resolve) => {
      const done = () => {
        el.removeEventListener("loadedmetadata", done);
        el.removeEventListener("error", done);
        resolve();
      };
      el.addEventListener("loadedmetadata", done, { once: true });
      el.addEventListener("error", done, { once: true });
    });
  }

  async function attachFile(file) {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = URL.createObjectURL(file);
    audio().src = objectUrl;
    await audio().play().then(() => audio().pause()).catch(() => {});
    buildTimeline();
  }

  async function attachUrl(url) {
    if (objectUrl) {
      URL.revokeObjectURL(objectUrl);
      objectUrl = null;
    }
    const ready = waitForAudio();
    audio().src = url;
    audio().load();
    await ready;
    if (audio().duration && Number.isFinite(audio().duration)) buildTimeline();
  }

  async function probeBundled() {
    for (const path of BUNDLED_CANDIDATES) {
      try {
        const head = await fetch(path, { method: "HEAD" });
        if (head.ok) return path;
      } catch {
        /* some hosts reject HEAD */
      }
      try {
        const range = await fetch(path, { headers: { Range: "bytes=0-1" } });
        if (range.ok || range.status === 206) return path;
      } catch {
        /* try next */
      }
    }
    return null;
  }

  function buildTimeline() {
    const state = Store.read();
    const verses = window.STOTRAM.listen;
    const baseDur = window.STOTRAM.meta.timing.duration;
    const offset = Number(state.timeOffset) || 0;
    // The cues were measured against the 29:41 recording. If a different rip
    // of the same recitation runs slightly long or short, scale linearly.
    const actual = audio().duration;
    const scale =
      Number.isFinite(actual) && actual > 60 && Math.abs(actual - baseDur) < 90
        ? actual / baseDur
        : 1;
    timeline = verses.map((v) => ({
      ...v,
      start: v.start * scale + offset,
      end: v.end * scale + offset,
    }));
    return timeline;
  }

  function verseAt(time) {
    if (!timeline.length) buildTimeline();
    const t = time ?? current();
    for (const v of timeline) {
      if (t < v.end) return v;
    }
    return timeline[timeline.length - 1];
  }

  function boundsForLearn(id) {
    if (!timeline.length) buildTimeline();
    const v = timeline.find((item) => item.learnId === id);
    if (!v) return null;
    // start is where her voice begins after the breath; end is where it stops.
    // A small tail keeps the last syllable's decay without touching the next verse.
    return { start: Math.max(0, v.start - 0.1), end: v.end + 0.15 };
  }

  function stopRangeWatch() {
    if (rangeTimer) {
      clearInterval(rangeTimer);
      rangeTimer = 0;
    }
  }

  function waitSeeked(el, timeoutMs) {
    return new Promise((resolve) => {
      let settled = false;
      const done = () => {
        if (settled) return;
        settled = true;
        el.removeEventListener("seeked", done);
        resolve();
      };
      el.addEventListener("seeked", done);
      window.setTimeout(done, timeoutMs || 2000);
    });
  }

  function confirmSeek(el, t) {
    // If the seek did not land (rare, e.g. slow range requests), retry once.
    waitSeeked(el)
      .then(() => {
        if (Math.abs(el.currentTime - t) > 1.5) {
          el.currentTime = t;
          return waitSeeked(el);
        }
        return null;
      })
      .then(() => {
        rangeSeeking = false;
      });
  }

  function hitRangeEnd(el) {
    if (el.dataset.loopOn == null || rangeSeeking) return false;
    const start = Number(el.dataset.loopStart);
    const clipEnd = Number(el.dataset.clipEnd || el.dataset.loopEnd);
    if (!Number.isFinite(clipEnd) || el.currentTime < clipEnd - 0.02) return false;
    if (el.dataset.loopOn === "1") {
      rangeSeeking = true;
      el.currentTime = start;
      waitSeeked(el).then(() => {
        rangeSeeking = false;
      });
      return true;
    }
    el.pause();
    el.currentTime = start;
    stopRangeWatch();
    return true;
  }

  // An interval timer keeps watching even when the tab is unfocused,
  // where requestAnimationFrame would throttle and let the clip overrun.
  function watchRange(el) {
    stopRangeWatch();
    rangeTimer = window.setInterval(() => {
      if (el.dataset.loopOn == null) {
        stopRangeWatch();
        return;
      }
      hitRangeEnd(el);
    }, 60);
  }

  async function playRange(start, end, loop) {
    const el = audio();
    const clipEnd = Math.max(start + 0.3, end);
    el.dataset.loopStart = String(start);
    el.dataset.loopEnd = String(end);
    el.dataset.clipEnd = String(clipEnd);
    el.dataset.loopOn = loop ? "1" : "0";
    if (!el.paused) el.pause();
    rangeSeeking = true;
    el.currentTime = start;
    confirmSeek(el, start);
    watchRange(el);
    try {
      // play() is called in the same task as the tap, so the browser's
      // user-gesture requirement is met even while the seek is pending.
      await el.play();
    } catch (err) {
      console.warn(err);
    }
  }

  function clearRange() {
    const el = audio();
    stopRangeWatch();
    delete el.dataset.loopStart;
    delete el.dataset.loopEnd;
    delete el.dataset.clipEnd;
    delete el.dataset.loopOn;
  }

  function setLooping(loop) {
    const el = audio();
    if (el.dataset.loopOn == null) return;
    el.dataset.loopOn = loop ? "1" : "0";
  }

  function seek(delta) {
    audio().currentTime = Math.max(0, Math.min(duration(), current() + delta));
  }

  function setTime(t) {
    audio().currentTime = Math.max(0, Math.min(duration(), t));
  }

  async function toggle() {
    if (playing()) {
      audio().pause();
      return;
    }
    try {
      await audio().play();
    } catch (err) {
      console.warn(err);
    }
  }

  audio().addEventListener("timeupdate", () => hitRangeEnd(audio()));
  audio().addEventListener("ended", () => hitRangeEnd(audio()));

  audio().addEventListener("loadedmetadata", buildTimeline);

  async function requestWake() {
    try {
      if (navigator.wakeLock) wakeLock = await navigator.wakeLock.request("screen");
    } catch {
      wakeLock = null;
    }
  }

  async function releaseWake() {
    try {
      await wakeLock?.release();
    } catch {
      /* ignore */
    }
    wakeLock = null;
  }

  return {
    audio,
    hasSource,
    duration,
    current,
    playing,
    attachFile,
    attachUrl,
    probeBundled,
    buildTimeline,
    verseAt,
    boundsForLearn,
    playRange,
    clearRange,
    setLooping,
    seek,
    setTime,
    toggle,
    requestWake,
    releaseWake,
    get timeline() {
      return timeline;
    },
  };
})();
