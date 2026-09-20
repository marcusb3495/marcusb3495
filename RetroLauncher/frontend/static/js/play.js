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

  // Surfaces uncaught JS errors (including ones thrown inside EmulatorJS
  // itself, loaded from its CDN) directly on the page, since most people
  // hitting this - especially on a phone - have no way to open DevTools.
  // Returns the logError function so callers can log their own entries.
  function initErrorLog() {
    const box = document.createElement("div");
    box.id = "play-error-log";
    box.hidden = true;
    box.style.cssText =
      "position:fixed;left:0;right:0;bottom:0;max-height:40vh;overflow:auto;" +
      "background:#3a0d0d;color:#ffd7d7;font:12px/1.5 monospace;padding:10px 12px;" +
      "border-top:2px solid #ff4d4d;white-space:pre-wrap;z-index:9999;";
    document.body.appendChild(box);

    function logError(text) {
      box.hidden = false;
      const line = document.createElement("div");
      line.textContent = text;
      box.appendChild(line);
    }

    window.addEventListener("error", (e) => {
      logError(
        `Error: ${e.message}` + (e.filename ? ` (${e.filename}:${e.lineno}:${e.colno})` : "")
      );
    });
    window.addEventListener("unhandledrejection", (e) => {
      const reason = e.reason;
      logError(`Unhandled promise rejection: ${reason && reason.message ? reason.message : reason}`);
    });

    return logError;
  }

  // EmulatorJS catches its own network failures internally and shows a
  // generic "Network Error" status instead of throwing, so window.onerror
  // never sees it. Patch fetch() and XMLHttpRequest (EmulatorJS uses both,
  // e.g. XHR for the ROM download progress bar) to log every request's
  // outcome, so the specific URL that actually failed shows up on screen.
  function instrumentNetwork(logError) {
    if (window.fetch) {
      const origFetch = window.fetch.bind(window);
      window.fetch = function (input, init) {
        const url = typeof input === "string" ? input : input && input.url;
        return origFetch(input, init).then(
          (resp) => {
            if (!resp.ok) {
              resp
                .clone()
                .text()
                .then((body) => logError(`fetch ${url} -> HTTP ${resp.status}: ${body.slice(0, 200)}`))
                .catch(() => logError(`fetch ${url} -> HTTP ${resp.status}`));
            }
            return resp;
          },
          (err) => {
            logError(`fetch ${url} -> failed: ${err.message}`);
            throw err;
          }
        );
      };
    }

    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
      this.__logUrl = url;
      this.addEventListener("error", () => logError(`XHR ${this.__logUrl} -> network error`));
      this.addEventListener("load", function () {
        if (this.status === 0 || this.status >= 400) {
          let body = "";
          try {
            if (this.response instanceof ArrayBuffer) {
              body = new TextDecoder().decode(this.response);
            } else {
              body = this.responseText || "";
            }
          } catch (_) {
            /* responseType isn't text/arraybuffer - body unavailable, that's fine */
          }
          logError(`XHR ${this.__logUrl} -> HTTP ${this.status}${body ? `: ${body.slice(0, 200)}` : ""}`);
        }
      });
      return origOpen.call(this, method, url, ...rest);
    };
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
    const logError = initErrorLog();
    instrumentNetwork(logError);

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

    // EmulatorJS reads the file extension out of this URL itself (not any
    // response header) to decide how to handle the ROM, so the real
    // filename - not just the game id - has to be part of the path.
    const romFilename = game.rom_path.split(/[\\/]/).pop();

    window.EJS_player = "#game";
    window.EJS_gameUrl = `/api/games/${gameId}/rom/${encodeURIComponent(romFilename)}`;
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
