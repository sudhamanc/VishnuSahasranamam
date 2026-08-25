(() => {
  const $ = (id) => document.getElementById(id);
  const learnVerses = window.STOTRAM.learn;
  const SECTION_LABEL = {
    opening: "Opening",
    purva: "Pūrva pīṭhikā",
    dhyana: "Dhyānam",
    stotram: "Sahasranāmam",
    phalashruti: "Phalaśruti",
  };

  let state = Store.read();
  let raf = 0;
  let learnLoop = true;

  function setView(name) {
    state = Store.write({ view: name });
    ["home", "learn", "listen", "settings"].forEach((view) => {
      $("view-" + view).hidden = view !== name;
    });
    $("backBtn").hidden = name === "home";
    $("settingsBtn").hidden = name === "settings";
    if (location.hash.replace("#", "") !== name) {
      history.replaceState(null, "", "#" + name);
    }
    if (name !== "listen") {
      Recitation.releaseWake();
      stopPrompter();
    }
    if (name === "home" || name === "settings" || name === "learn") {
      Recitation.audio().pause();
      Recitation.clearRange();
    }
    if (name === "listen") Recitation.clearRange();
    if (name === "learn") {
      renderLearn();
      watchPin();
      window.scrollTo({ top: 0, behavior: "auto" });
    }
    if (name === "listen") renderListen();
    if (name === "settings") renderSettings();
    if (name === "home") renderHome();
  }

  function learnedSet() {
    return new Set(state.learned || []);
  }

  function renderHome() {
    const done = learnedSet().size;
    const total = learnVerses.length;
    $("ringLabel").textContent = String(done);
    $("ringFg").style.strokeDashoffset = String(188.4 * (1 - done / total));
    if (done === 0) {
      $("progressCopy").textContent = "Begin with Śuklāmbaradharam when you are ready.";
    } else if (done >= total) {
      $("progressCopy").textContent = "Every verse has been sat with. You may begin again.";
    } else {
      $("progressCopy").textContent = `${done} of ${total} verses marked as learned.`;
    }
  }

  function currentLearn() {
    return learnVerses[state.learnIndex] || learnVerses[0];
  }

  function learnKicker(verse) {
    if (verse.section === "stotram" && verse.shloka) {
      return `Śloka ${verse.shloka} of ${window.STOTRAM.meta.stotramCount || 108}`;
    }
    const label = SECTION_LABEL[verse.section] || verse.section;
    const inSection = learnVerses.filter((v) => v.section === verse.section);
    const i = inSection.findIndex((v) => v.id === verse.id) + 1;
    return `${label} · ${i} of ${inSection.length}`;
  }

  // Break each half-line at its daṇḍa, and after a completed verse, so the
  // Sanskrit reads as it is written rather than as the box happens to wrap it.
  function verseLines(sa) {
    return sa
      .replace(/\s*।\s*/g, " ।\n")
      .replace(/(॥\s*[०-९\d]+\s*॥)\s*/g, "$1\n")
      .replace(/\n+$/, "")
      .trim();
  }

  const esc = (s) =>
    String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

  function renderLearn() {
    const verse = currentLearn();
    $("learnKicker").textContent = learnKicker(verse);
    $("learnSlider").max = String(learnVerses.length);
    $("learnSlider").value = String(verse.n);
    $("learnSa").textContent = verseLines(verse.sa);
    $("learnIast").textContent = verse.iast;
    $("learnIast").hidden = !state.showIast;
    $("learnEn").textContent = verse.en;
    $("pinBadge").textContent = verse.shloka ? String(verse.shloka) : "";
    $("pinBadge").hidden = !verse.shloka;
    const names = $("learnNames");
    names.innerHTML = verse.names
      .map(
        (n) =>
          `<li><span class="n">${n.n}</span><span class="nm">${esc(n.name)}</span><span class="en">${esc(n.en)}</span></li>`
      )
      .join("");
    $("learnNamesWrap").hidden = verse.names.length === 0;
    $("learnNamesWrap").open = state.namesOpen !== false;
    if (verse.names.length) {
      const first = verse.names[0].n;
      const last = verse.names[verse.names.length - 1].n;
      $("learnNamesCount").textContent =
        verse.names.length === 1 ? `${first}` : `${first}–${last}`;
    } else {
      $("learnNamesCount").textContent = "";
    }
    const learned = learnedSet().has(verse.id);
    $("markLearned").textContent = learned ? "Learned" : "Mark as learned";
    $("markLearned").classList.toggle("is-on", learned);
    $("markLearned").setAttribute("aria-pressed", learned ? "true" : "false");
    $("prevVerse").disabled = verse.n === 1;
    $("nextVerse").disabled = verse.n === learnVerses.length;
    updateLearnAudioLabel();
    syncPlayButtons();
  }

  // Show the śloka again whenever a new one is opened, however deep into the
  // names the last one was read.
  function goToVerse(index) {
    const next = Math.max(0, Math.min(learnVerses.length - 1, index));
    if (next === state.learnIndex) return;
    Recitation.audio().pause();
    Recitation.clearRange();
    state = Store.write({ learnIndex: next });
    renderLearn();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  let pinWatcher = null;

  function watchPin() {
    if (pinWatcher) pinWatcher.disconnect();
    if (!("IntersectionObserver" in window)) return;
    const scrim = document.querySelector(".status-scrim");
    const inset = scrim ? scrim.offsetHeight : 0;
    pinWatcher = new IntersectionObserver(
      ([entry]) => {
        $("versePin").classList.toggle("is-pinned", !entry.isIntersecting);
      },
      { rootMargin: `-${inset + 1}px 0px 0px 0px`, threshold: 0 }
    );
    pinWatcher.observe($("pinSentinel"));
  }

  function updateLearnAudioLabel() {
    if (!Recitation.hasSource()) {
      $("learnAudioLabel").textContent =
        "Add the recitation in Settings, or deploy audio/recitation.mp3 with the site.";
      return;
    }
    $("learnAudioLabel").textContent =
      "Her voice on this verse — listen, then say it with her.";
  }

  function syncPlayButtons() {
    const on = Recitation.playing();
    document.querySelectorAll(".play-orb").forEach((btn) => {
      btn.classList.toggle("is-playing", on);
      btn.setAttribute("aria-label", on ? "Pause" : btn.dataset.playLabel || "Play");
    });
  }

  async function playCurrentLearn() {
    if (!Recitation.hasSource()) {
      setView("settings");
      return;
    }
    Recitation.clearRange();
    const verse = currentLearn();
    Recitation.buildTimeline();
    const bounds = Recitation.boundsForLearn(verse.id);
    if (!bounds) return;
    await Recitation.playRange(bounds.start, bounds.end, learnLoop);
    syncPlayButtons();
  }

  function renderListen() {
    Recitation.buildTimeline();
    const track = $("prompterTrack");
    track.innerHTML = Recitation.timeline
      .map((v, i) => {
        const sec = i === 0 || Recitation.timeline[i - 1].section !== v.section
          ? `<p class="sec">${esc(SECTION_LABEL[v.section] || v.section)}</p>`
          : "";
        return `<article class="prompter-verse" data-i="${i}">${sec}<p class="sa">${esc(v.sa)}</p><p class="en">${esc(v.en)}</p></article>`;
      })
      .join("");
    document.documentElement.style.setProperty("--type-scale", String(state.fontScale || 1));
    $("fontScale").value = String(state.fontScale || 1);
    $("listenSeek").max = "1000";
    Recitation.requestWake();
    startPrompter();
    requestAnimationFrame(updatePrompter);
    syncPlayButtons();
    if (!Recitation.hasSource()) {
      $("listenNow").textContent = "Add the recitation in Settings to begin.";
    }
  }

  function updatePrompter() {
    const t = Recitation.current();
    const verses = Recitation.timeline;
    if (!verses.length) return;
    let i = verses.findIndex((v) => t < v.end);
    if (i < 0) i = verses.length - 1;
    const nodes = $("prompterTrack").children;
    [...nodes].forEach((el, idx) => {
      el.classList.toggle("is-current", idx === i);
      el.classList.toggle("is-past", idx < i);
    });
    const current = nodes[i];
    if (!current) return;
    const next = nodes[i + 1];
    const span = Math.max(0.05, verses[i].end - verses[i].start);
    const p = Math.min(1, Math.max(0, (t - verses[i].start) / span));
    const y0 = current.offsetTop + current.offsetHeight * 0.45;
    const y1 = next ? next.offsetTop + next.offsetHeight * 0.45 : y0;
    const y = y0 + (y1 - y0) * p;
    const center = $("prompter").clientHeight * 0.48;
    $("prompterTrack").style.transform = `translateY(${center - y}px)`;
    $("listenNow").textContent = SECTION_LABEL[verses[i].section] || verses[i].section;
    const dur = Recitation.duration();
    $("listenSeek").value = String(Math.round((t / dur) * 1000));
    $("listenTime").textContent = `${fmt(t)} / ${fmt(dur)}`;
    syncPlayButtons();
  }

  function startPrompter() {
    stopPrompter();
    const tick = () => {
      updatePrompter();
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
  }

  function stopPrompter() {
    cancelAnimationFrame(raf);
    raf = 0;
  }

  function fmt(sec) {
    const s = Math.max(0, Math.floor(sec || 0));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  }

  function renderSettings() {
    $("timeOffset").value = String(state.timeOffset || 0);
    $("showIast").checked = state.showIast !== false;
    if (state.audioName) {
      $("audioStatus").textContent = `Saved on this device: ${state.audioName}`;
    } else if (Recitation.hasSource()) {
      $("audioStatus").textContent =
        "Using the site recitation — M. S. Subbulakshmi.";
    } else {
      $("audioStatus").textContent = "No recitation loaded yet.";
    }
  }

  $("goLearn").onclick = () => setView("learn");
  $("goListen").onclick = () => setView("listen");
  $("settingsBtn").onclick = () => setView("settings");
  $("backBtn").onclick = () => setView("home");
  $("homeProgress").onclick = () => setView("learn");

  $("learnSlider").oninput = (e) => goToVerse(Number(e.target.value) - 1);
  $("prevVerse").onclick = () => goToVerse(state.learnIndex - 1);
  $("nextVerse").onclick = () => goToVerse(state.learnIndex + 1);
  $("learnNamesWrap").ontoggle = () => {
    state = Store.write({ namesOpen: $("learnNamesWrap").open });
  };
  $("markLearned").onclick = () => {
    const id = currentLearn().id;
    const set = learnedSet();
    if (set.has(id)) set.delete(id);
    else set.add(id);
    state = Store.write({ learned: [...set] });
    renderLearn();
  };
  $("learnLoop").onchange = (e) => {
    learnLoop = e.target.checked;
    Recitation.setLooping(learnLoop);
  };
  const toggleLearnAudio = async () => {
    if (Recitation.playing() && Recitation.audio().dataset.loopStart) {
      Recitation.audio().pause();
      syncPlayButtons();
      return;
    }
    $("learnPlay").classList.add("is-playing");
    await playCurrentLearn();
    syncPlayButtons();
  };
  $("learnPlay").onclick = toggleLearnAudio;
  $("pinPlay").onclick = toggleLearnAudio;

  // A flick sideways across the verse moves to the next or previous śloka.
  let swipeX = 0;
  let swipeY = 0;
  let swiping = false;
  $("learnCard").addEventListener(
    "touchstart",
    (e) => {
      swiping = e.touches.length === 1;
      if (!swiping) return;
      swipeX = e.touches[0].clientX;
      swipeY = e.touches[0].clientY;
    },
    { passive: true }
  );
  $("learnCard").addEventListener(
    "touchend",
    (e) => {
      if (!swiping) return;
      swiping = false;
      const touch = e.changedTouches[0];
      const dx = touch.clientX - swipeX;
      const dy = touch.clientY - swipeY;
      if (Math.abs(dx) < 70 || Math.abs(dx) < Math.abs(dy) * 1.8) return;
      goToVerse(state.learnIndex + (dx < 0 ? 1 : -1));
    },
    { passive: true }
  );

  $("listenPlay").onclick = async () => {
    if (!Recitation.hasSource()) {
      setView("settings");
      return;
    }
    Recitation.clearRange();
    if (Recitation.playing()) {
      Recitation.audio().pause();
    } else {
      $("listenPlay").classList.add("is-playing");
      await Recitation.toggle();
    }
    syncPlayButtons();
  };
  $("listenBack").onclick = () => Recitation.seek(-10);
  $("listenFwd").onclick = () => Recitation.seek(10);
  $("listenSeek").oninput = (e) => {
    Recitation.setTime((Number(e.target.value) / 1000) * Recitation.duration());
  };
  $("fontScale").oninput = (e) => {
    state = Store.write({ fontScale: Number(e.target.value) });
    document.documentElement.style.setProperty("--type-scale", e.target.value);
  };

  $("audioFile").onchange = async (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    await Store.saveAudio(file);
    await Recitation.attachFile(file);
    state = Store.read();
    renderSettings();
  };
  $("clearAudio").onclick = async () => {
    Recitation.audio().pause();
    await Store.clearAudio();
    const bundled = await Recitation.probeBundled();
    if (bundled) {
      await Recitation.attachUrl(bundled);
    } else {
      Recitation.audio().removeAttribute("src");
      Recitation.audio().load();
    }
    state = Store.read();
    renderSettings();
  };
  $("timeOffset").onchange = (e) => {
    state = Store.write({ timeOffset: Number(e.target.value) || 0 });
    Recitation.buildTimeline();
  };
  $("markShloka1").onclick = () => {
    // Her Viśvaṃ Viṣṇur… begins at 403.05s in the reference recording.
    const offset = Recitation.current() - 403.05;
    state = Store.write({ timeOffset: Math.round(offset * 10) / 10 });
    renderSettings();
    Recitation.buildTimeline();
  };
  $("resetOffset").onclick = () => {
    state = Store.write({ timeOffset: 0 });
    renderSettings();
    Recitation.buildTimeline();
  };
  $("showIast").onchange = (e) => {
    state = Store.write({ showIast: e.target.checked });
  };
  $("resetProgress").onclick = () => {
    if (confirm("Clear the verses you have marked as learned?")) {
      state = Store.write({ learned: [], learnIndex: 0 });
      renderSettings();
    }
  };

  document.addEventListener("keydown", (e) => {
    if (state.view !== "learn") return;
    if (e.key === "ArrowLeft") $("prevVerse").click();
    if (e.key === "ArrowRight") $("nextVerse").click();
    if (e.key === " ") {
      e.preventDefault();
      $("learnPlay").click();
    }
  });
  Recitation.audio().addEventListener("play", syncPlayButtons);
  Recitation.audio().addEventListener("playing", syncPlayButtons);
  Recitation.audio().addEventListener("pause", syncPlayButtons);
  Recitation.audio().addEventListener("ended", syncPlayButtons);

  async function restoreAudio() {
    const file = await Store.loadAudio();
    if (file) {
      await Recitation.attachFile(file);
      return;
    }
    const bundled = await Recitation.probeBundled();
    if (bundled) await Recitation.attachUrl(bundled);
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }

  restoreAudio().finally(() => {
    const hash = location.hash.replace("#", "");
    const start = ["home", "learn", "listen", "settings"].includes(hash) ? hash : "home";
    setView(start);
  });
  window.addEventListener("hashchange", () => {
    const hash = location.hash.replace("#", "") || "home";
    if (["home", "learn", "listen", "settings"].includes(hash)) setView(hash);
  });
})();
