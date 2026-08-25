const Store = (() => {
  const KEY = "vs-sahasranamam-v3";
  const LEGACY_KEYS = ["vs-sahasranamam-v2", "vs-sahasranamam-v1"];
  const DB_NAME = "vs-audio";
  const DB_STORE = "files";

  const defaults = () => ({
    view: "home",
    learnIndex: 0,
    learned: [],
    showIast: true,
    timeOffset: 0,
    audioName: "",
    fontScale: 1,
    namesOpen: true,
  });

  function read() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) return { ...defaults(), ...JSON.parse(raw) };
      for (const legacy of LEGACY_KEYS) {
        const legacyRaw = localStorage.getItem(legacy);
        if (!legacyRaw) continue;
        const old = JSON.parse(legacyRaw);
        const migrated = {
          ...defaults(),
          showIast: old.showIast !== false,
          audioName: old.audioName || "",
          fontScale: old.fontScale || 1,
        };
        localStorage.setItem(KEY, JSON.stringify(migrated));
        return migrated;
      }
      return defaults();
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
