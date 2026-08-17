const Recitation = (() => {
  const audio = () => document.getElementById("recitation");
  let objectUrl = null;
  let timeline = [];
  let wakeLock = null;

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

  async function playRange(start, end, loop) {
    const el = audio();
    el.dataset.loopStart = String(start);
    el.dataset.loopEnd = String(end);
    el.dataset.loopOn = loop ? "1" : "0";
    el.currentTime = start;
    try {
      await el.play();
    } catch (err) {
      console.warn(err);
    }
  }

  function clearRange() {
    const el = audio();
    delete el.dataset.loopStart;
    delete el.dataset.loopEnd;
    delete el.dataset.loopOn;
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

  audio().addEventListener("timeupdate", () => {
    const el = audio();
    if (el.dataset.loopOn !== "1") return;
    const end = Number(el.dataset.loopEnd);
    const start = Number(el.dataset.loopStart);
    if (el.currentTime >= end - 0.05) {
      el.currentTime = start;
    }
  });

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
