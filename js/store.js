const Store = (() => {
  const KEY = "vs-sahasranamam-v1";
  const DB_NAME = "vs-audio";
  const DB_STORE = "files";

  const defaults = () => ({
    view: "home",
    learnIndex: 0,
    learned: [],
    showIast: true,
    namesStart: window.STOTRAM.meta.timing.namesStart,
    namesEnd: window.STOTRAM.meta.timing.namesEnd,
    audioName: "",
    fontScale: 1,
  });

  function read() {
    try {
      return { ...defaults(), ...JSON.parse(localStorage.getItem(KEY) || "{}") };
    } catch {
      return defaults();
    }
  }

  function write(patch) {
    const next = { ...read(), ...patch };
    localStorage.setItem(KEY, JSON.stringify(next));
    return next;
  }

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, 1);
      req.onupgradeneeded = () => req.result.createObjectStore(DB_STORE);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  async function saveAudio(file) {
    const db = await openDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(DB_STORE, "readwrite");
      tx.objectStore(DB_STORE).put(file, "recitation");
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
    write({ audioName: file.name });
  }

  async function loadAudio() {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(DB_STORE, "readonly");
      const req = tx.objectStore(DB_STORE).get("recitation");
      req.onsuccess = () => resolve(req.result || null);
      req.onerror = () => reject(req.error);
    });
  }

  async function clearAudio() {
    const db = await openDb();
    await new Promise((resolve, reject) => {
      const tx = db.transaction(DB_STORE, "readwrite");
      tx.objectStore(DB_STORE).delete("recitation");
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
    write({ audioName: "" });
  }

  return { read, write, saveAudio, loadAudio, clearAudio, defaults };
})();
