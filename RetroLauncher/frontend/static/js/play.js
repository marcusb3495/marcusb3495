(function () {
  // Loaded from EmulatorJS's CDN - it exposes a loader that reads the
  // EJS_* globals set below and mounts a WebAssembly emulator core into
  // the #game element. See https://emulatorjs.org for docs.
  const EMULATORJS_DATA_URL = "https://cdn.emulatorjs.org/stable/data/";

  const params = new URLSearchParams(window.location.search);
  const gameId = params.get("game");

  function showMessage(html) {
    document.getElementById("game").hidden = true;
    const box = document.getElementById("play-message");
    box.innerHTML = html;
    box.hidden = false;
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str == null ? "" : String(str);
    return d.innerHTML;
  }

  async function fetchJson(url) {
    const resp = await fetch(url);
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      throw new Error(body.detail || resp.statusText);
    }
    return resp.json();
  }

  async function init() {
    if (!gameId) {
      showMessage("No game specified.");
      return;
    }

    let game, platform;
    try {
      game = await fetchJson(`/api/games/${gameId}`);
      platform = await fetchJson(`/api/platforms/${game.platform_id}`);
    } catch (e) {
      showMessage(`Failed to load game: ${escapeHtml(e.message)}`);
      return;
    }

    document.getElementById("play-title").textContent = game.title;
    document.title = `${game.title} · RetroLauncher`;

    if (!platform.browser_core) {
      showMessage(
        `No browser emulator core is set for <strong>${escapeHtml(platform.name)}</strong>.<br><br>` +
          `Go to Settings → Platforms and set a "Browser Core" for this platform ` +
          `(e.g. <code>nes</code>, <code>snes</code>, <code>gba</code>, <code>genesis</code>, <code>psx</code>) ` +
          `then come back and try again.`
      );
      return;
    }

    window.EJS_player = "#game";
    window.EJS_gameUrl = `/api/games/${gameId}/rom`;
    window.EJS_core = platform.browser_core;
    window.EJS_gameName = game.title;
    window.EJS_pathtodata = EMULATORJS_DATA_URL;
    window.EJS_startOnLoaded = true;

    const script = document.createElement("script");
    script.src = EMULATORJS_DATA_URL + "loader.js";
    script.onerror = () => {
      showMessage(
        "Failed to load the in-browser emulator from cdn.emulatorjs.org. " +
          "Check that this device has internet access (only the browser needs it - not the server)."
      );
    };
    document.body.appendChild(script);
  }

  init();
})();
