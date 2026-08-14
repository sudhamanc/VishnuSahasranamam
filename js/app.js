(() => {
  const $ = (id) => document.getElementById(id);
  const learnVerses = window.STOTRAM.learn;
  const SECTION_LABEL = {
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
    if (name === "home" || name === "settings") {
      Recitation.audio().pause();
      Recitation.clearRange();
    }
    if (name === "learn") renderLearn();
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
      $("progressCopy").textContent = "Begin with the first verse when you are ready.";
    } else if (done >= total) {
      $("progressCopy").textContent = "All 108 verses have been sat with. You may begin again.";
    } else {
      $("progressCopy").textContent = `${done} of ${total} verses marked as learned.`;
    }
  }

  function currentLearn() {
    return learnVerses[state.learnIndex] || learnVerses[0];
  }

  function renderLearn() {
    const verse = currentLearn();
    $("learnKicker").textContent = `Śloka ${verse.n} of ${learnVerses.length}`;
    $("learnSlider").max = String(learnVerses.length);
    $("learnSlider").value = String(verse.n);
    $("learnSa").textContent = verse.sa.replace(/\s*॥\s*/g, " ॥\n").trim();
    $("learnIast").textContent = verse.iast;
    $("learnIast").hidden = !state.showIast;
    $("learnEn").textContent = verse.en;
    const names = $("learnNames");
    names.innerHTML = verse.names
      .map(
        (n) =>
          `<li><span class="n">${n.n}</span><span class="nm">${n.name}</span><span class="en">${n.en}</span></li>`
      )
      .join("");
    $("learnNamesWrap").hidden = verse.names.length === 0;
    const learned = learnedSet().has(verse.id);
    $("markLearned").textContent = learned ? "Learned" : "Mark as learned";
    $("markLearned").classList.toggle("is-on", learned);
    $("prevVerse").disabled = verse.n === 1;
    $("nextVerse").disabled = verse.n === learnVerses.length;
    updateLearnAudioLabel();
    syncPlayButtons();
  }

  function updateLearnAudioLabel() {
    if (!Recitation.hasSource()) {
      $("learnAudioLabel").textContent =
        "Load Subbulakshmi’s recitation in Settings to hear this verse.";
      return;
    }
    $("learnAudioLabel").textContent =
      "Her voice on this verse — listen, then say it with her.";
  }

  function syncPlayButtons() {
    const on = Recitation.playing();
    document.querySelectorAll(".play-orb").forEach((btn) => {
      btn.querySelector(".icon-play").hidden = on;
      btn.querySelector(".icon-pause").hidden = !on;
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
    const esc = (s) =>
      String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
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
      $("listenNow").textContent = "Load the recitation in Settings to begin.";
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
    $("namesStart").value = String(Math.round(state.namesStart));
    $("namesEnd").value = String(Math.round(state.namesEnd));
    $("showIast").checked = state.showIast !== false;
    $("audioStatus").textContent = state.audioName
      ? `Saved: ${state.audioName}`
      : "No recitation loaded yet.";
  }

  $("goLearn").onclick = () => setView("learn");
  $("goListen").onclick = () => setView("listen");
  $("settingsBtn").onclick = () => setView("settings");
  $("backBtn").onclick = () => setView("home");
  $("homeProgress").onclick = () => setView("learn");

  $("learnSlider").oninput = (e) => {
    Recitation.audio().pause();
    Recitation.clearRange();
    state = Store.write({ learnIndex: Number(e.target.value) - 1 });
    renderLearn();
  };
  $("prevVerse").onclick = () => {
    Recitation.audio().pause();
    Recitation.clearRange();
    state = Store.write({ learnIndex: Math.max(0, state.learnIndex - 1) });
    renderLearn();
  };
  $("nextVerse").onclick = () => {
    Recitation.audio().pause();
    Recitation.clearRange();
    state = Store.write({
      learnIndex: Math.min(learnVerses.length - 1, state.learnIndex + 1),
    });
    renderLearn();
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
  };
  $("learnPlay").onclick = async () => {
    if (Recitation.playing() && Recitation.audio().dataset.loopStart) {
      Recitation.audio().pause();
      syncPlayButtons();
      return;
    }
    await playCurrentLearn();
  };

  $("listenPlay").onclick = async () => {
    if (!Recitation.hasSource()) {
      setView("settings");
      return;
    }
    Recitation.clearRange();
    await Recitation.toggle();
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
    Recitation.audio().removeAttribute("src");
    Recitation.audio().load();
    await Store.clearAudio();
    state = Store.read();
    renderSettings();
  };
  $("namesStart").onchange = (e) => {
    state = Store.write({ namesStart: Number(e.target.value) });
    Recitation.buildTimeline();
  };
  $("namesEnd").onchange = (e) => {
    state = Store.write({ namesEnd: Number(e.target.value) });
    Recitation.buildTimeline();
  };
  $("markStart").onclick = () => {
    state = Store.write({ namesStart: Recitation.current() });
    renderSettings();
    Recitation.buildTimeline();
  };
  $("markEnd").onclick = () => {
    state = Store.write({ namesEnd: Recitation.current() });
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
  Recitation.audio().addEventListener("pause", syncPlayButtons);
  Recitation.audio().addEventListener("ended", syncPlayButtons);

  async function restoreAudio() {
    const file = await Store.loadAudio();
    if (file) await Recitation.attachFile(file);
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
