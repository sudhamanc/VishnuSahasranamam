const Recitation = (() => {
  const audio = () => document.getElementById("recitation");
  let objectUrl = null;
  let timeline = [];
  let wakeLock = null;
  let rangeRaf = 0;
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
    return Number.isFinite(d) && d > 0 ? d : window.STOTRAM.meta.timing.expectedDuration;
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
    const dur = duration();
    let namesStart = Number(state.namesStart);
    let namesEnd = Number(state.namesEnd);
    namesStart = Math.max(0, Math.min(namesStart, dur - 30));
    namesEnd = Math.max(namesStart + 30, Math.min(namesEnd, dur - 2));

    const before = verses.filter((v) => v.section !== "stotram" && v.section !== "phalashruti");
    const names = verses.filter((v) => v.section === "stotram");
    const after = verses.filter((v) => v.section === "phalashruti");

    const stamp = (list, from, to) => {
      const total = list.reduce((sum, v) => sum + (v.weight || 1), 0) || 1;
      let t = from;
      const span = Math.max(1, to - from);
      return list.map((v) => {
        const len = ((v.weight || 1) / total) * span;
        const item = { ...v, start: t, end: t + len };
        t += len;
        return item;
      });
    };

    timeline = [
      ...stamp(before, 0, namesStart),
      ...stamp(names, namesStart, namesEnd),
      ...stamp(after, namesEnd, dur),
    ];
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
    return v ? { start: v.start, end: v.end } : null;
  }

  function stopRangeWatch() {
    if (rangeRaf) {
      cancelAnimationFrame(rangeRaf);
      rangeRaf = 0;
    }
  }

  function waitSeeked(el) {
    return new Promise((resolve) => {
      let settled = false;
      const done = () => {
        if (settled) return;
        settled = true;
        el.removeEventListener("seeked", done);
        resolve();
      };
      el.addEventListener("seeked", done);
      window.setTimeout(done, 400);
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

  function watchRange(el) {
    stopRangeWatch();
    const tick = () => {
      if (el.dataset.loopOn == null) {
        rangeRaf = 0;
        return;
      }
      hitRangeEnd(el);
      if (el.dataset.loopOn == null) {
        rangeRaf = 0;
        return;
      }
      rangeRaf = requestAnimationFrame(tick);
    };
    rangeRaf = requestAnimationFrame(tick);
  }

  async function playRange(start, end, loop) {
    const el = audio();
    const clipEnd = Math.max(start + 0.3, end - 0.18);
    el.dataset.loopStart = String(start);
    el.dataset.loopEnd = String(end);
    el.dataset.clipEnd = String(clipEnd);
    el.dataset.loopOn = loop ? "1" : "0";
    el.pause();
    if (Math.abs(el.currentTime - start) > 0.04) {
      el.currentTime = start;
      await waitSeeked(el);
    } else {
      el.currentTime = start;
    }
    rangeSeeking = false;
    watchRange(el);
    try {
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
