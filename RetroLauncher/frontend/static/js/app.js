(function () {
  const state = {
    platforms: [],
    platformId: null,
    favoritesOnly: false,
    search: "",
    games: [],
    activeGame: null,
  };

  const el = (id) => document.getElementById(id);

  function toast(message) {
    const t = el("toast");
    t.textContent = message;
    t.hidden = false;
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => (t.hidden = true), 3000);
  }

  async function api(path, options) {
    const resp = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!resp.ok) {
      let detail = resp.statusText;
      try {
        const body = await resp.json();
        detail = body.detail || detail;
      } catch (_) {
        /* ignore */
      }
      throw new Error(detail);
    }
    if (resp.status === 204) return null;
    return resp.json();
  }

  // ---------------- Sidebar ----------------

  // Generic fallback glyph shown for platforms without a custom uploaded icon.
  const DEFAULT_PLATFORM_ICON = `<svg class="nav-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7 7h10a4 4 0 0 1 4 4v3a3 3 0 0 1-5.2 2.05L14 14.5h-4l-1.8 1.55A3 3 0 0 1 3 14v-3a4 4 0 0 1 4-4Z" stroke="currentColor" stroke-width="1.6"/>
    <path d="M8 10v3M6.5 11.5h3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>
    <circle cx="16.5" cy="10.5" r="0.9" fill="currentColor"/>
    <circle cx="18.5" cy="12.5" r="0.9" fill="currentColor"/>
  </svg>`;

  function platformIconHtml(p) {
    if (p.icon_path) {
      return `<img class="nav-icon" src="/media/platform_icons/${p.icon_path}" alt="" />`;
    }
    return DEFAULT_PLATFORM_ICON;
  }

  async function loadPlatforms() {
    state.platforms = await api("/api/platforms");
    const list = el("platform-list");
    list.innerHTML = "";
    for (const p of state.platforms) {
      const btn = document.createElement("button");
      btn.className = "nav-item";
      btn.dataset.nav = "";
      btn.dataset.platformId = p.id;
      btn.innerHTML = `<span class="nav-label">${platformIconHtml(p)}${escapeHtml(p.name)}</span><span class="count">${p.game_count}</span>`;
      btn.addEventListener("click", () => selectPlatform(p.id, p.name));
      list.appendChild(btn);
    }
  }

  function setActiveNav(target) {
    document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
    if (target) target.classList.add("active");
  }

  function selectPlatform(id, name) {
    state.platformId = id;
    state.favoritesOnly = false;
    el("content-title").textContent = name;
    setActiveNav(document.querySelector(`.nav-item[data-platform-id="${id}"]`));
    loadGames();
  }

  function selectAllGames() {
    state.platformId = null;
    state.favoritesOnly = false;
    el("content-title").textContent = "All Games";
    setActiveNav(document.querySelector('.nav-item[data-platform-id=""]'));
    loadGames();
  }

  function selectFavorites() {
    state.platformId = null;
    state.favoritesOnly = true;
    el("content-title").textContent = "★ Favorites";
    setActiveNav(document.querySelector(".nav-item[data-favorites]"));
    loadGames();
  }

  // ---------------- Games grid ----------------

  async function loadGames() {
    const params = new URLSearchParams();
    if (state.platformId) params.set("platform_id", state.platformId);
    if (state.favoritesOnly) params.set("favorite", "true");
    if (state.search) params.set("search", state.search);

    state.games = await api(`/api/games?${params.toString()}`);
    renderGrid();
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str == null ? "" : String(str);
    return d.innerHTML;
  }

  function renderGrid() {
    const grid = el("grid");
    const emptyState = el("empty-state");
    grid.innerHTML = "";

    if (state.games.length === 0) {
      emptyState.hidden = false;
      emptyState.textContent = state.platforms.length
        ? "No games found. Try scanning a platform's ROM folder from Settings."
        : "No platforms configured yet. Head to Settings to add one and scan your ROMs.";
      return;
    }
    emptyState.hidden = true;

    for (const game of state.games) {
      const card = document.createElement("div");
      card.className = "card";
      card.dataset.nav = "";
      card.tabIndex = 0;
      card.dataset.gameId = game.id;

      const cover = game.cover_path
        ? `<img src="/media/covers/${game.cover_path}" alt="${escapeHtml(game.title)}" loading="lazy" />`
        : `<div class="cover">${escapeHtml(game.title)}</div>`;

      card.innerHTML = `
        ${game.favorite ? '<div class="fav-badge">★</div>' : ""}
        ${game.cover_path ? `<div class="cover">${cover}</div>` : cover}
        <div class="title">${escapeHtml(game.title)}</div>
      `;
      card.addEventListener("click", () => openModal(game));
      grid.appendChild(card);
    }
  }

  // ---------------- Modal ----------------

  function openModal(game) {
    state.activeGame = game;
    el("modal-title").textContent = game.title;
    const meta = [game.platform_id ? platformName(game.platform_id) : null, game.release_date, game.genre]
      .filter(Boolean)
      .join(" • ");
    el("modal-meta").textContent = meta;
    el("modal-description").textContent = game.description || "No description yet — try Fetch Metadata.";
    el("modal-cover").innerHTML = game.cover_path
      ? `<img src="/media/covers/${game.cover_path}" alt="${escapeHtml(game.title)}" />`
      : "No Cover";
    el("modal-favorite").textContent = game.favorite ? "★ Favorited" : "☆ Favorite";
    el("scrape-results").innerHTML = "";
    el("modal-backdrop").hidden = false;
    setTimeout(() => window.RetroNav.setFocus(el("modal-play-browser")), 0);
  }

  function closeModal() {
    el("modal-backdrop").hidden = true;
    state.activeGame = null;
    window.RetroNav.ensureInitialFocus();
  }

  function platformName(id) {
    const p = state.platforms.find((p) => p.id === id);
    return p ? p.name : null;
  }

  function playInBrowser() {
    if (!state.activeGame) return;
    window.location.href = `/play.html?game=${state.activeGame.id}`;
  }

  async function launchActiveGame() {
    if (!state.activeGame) return;
    try {
      await api(`/api/games/${state.activeGame.id}/launch`, { method: "POST", body: "{}" });
      toast(`Launching ${state.activeGame.title} on the server's native emulator...`);
    } catch (e) {
      toast(`Launch failed: ${e.message}`);
    }
  }

  async function toggleFavorite() {
    if (!state.activeGame) return;
    const favorite = !state.activeGame.favorite;
    const updated = await api(`/api/games/${state.activeGame.id}`, {
      method: "PUT",
      body: JSON.stringify({ favorite }),
    });
    state.activeGame = updated;
    el("modal-favorite").textContent = updated.favorite ? "★ Favorited" : "☆ Favorite";
    loadGames();
  }

  async function scrapeActiveGame() {
    if (!state.activeGame) return;
    const results = el("scrape-results");
    results.innerHTML = '<p class="meta">Searching...</p>';
    try {
      const candidates = await api(`/api/games/${state.activeGame.id}/scrape/search`);
      if (candidates.length === 0) {
        results.innerHTML = '<p class="meta">No matches found.</p>';
        return;
      }
      results.innerHTML = "";
      const list = document.createElement("div");
      list.className = "panel";
      for (const c of candidates.slice(0, 8)) {
        const row = document.createElement("button");
        row.className = "btn";
        row.dataset.nav = "";
        row.style.display = "block";
        row.style.width = "100%";
        row.style.textAlign = "left";
        row.style.marginBottom = "6px";
        row.textContent = `${c.title}${c.release_date ? " (" + c.release_date + ")" : ""}`;
        row.addEventListener("click", () => applyScrape(c.provider_id));
        list.appendChild(row);
      }
      results.appendChild(list);
    } catch (e) {
      results.innerHTML = `<p class="meta">${escapeHtml(e.message)}</p>`;
    }
  }

  async function applyScrape(providerId) {
    if (!state.activeGame) return;
    try {
      const updated = await api(`/api/games/${state.activeGame.id}/scrape/apply`, {
        method: "POST",
        body: JSON.stringify({ provider_id: providerId }),
      });
      state.activeGame = updated;
      openModal(updated);
      loadGames();
      toast("Metadata updated");
    } catch (e) {
      toast(`Scrape failed: ${e.message}`);
    }
  }

  // ---------------- Wiring ----------------

  function init() {
    document.querySelector('.nav-item[data-platform-id=""]').addEventListener("click", selectAllGames);
    document.querySelector(".nav-item[data-favorites]").addEventListener("click", selectFavorites);

    el("modal-close").addEventListener("click", closeModal);
    el("modal-backdrop").addEventListener("click", (e) => {
      if (e.target === el("modal-backdrop")) closeModal();
    });
    el("modal-play-browser").addEventListener("click", playInBrowser);
    el("modal-launch").addEventListener("click", launchActiveGame);
    el("modal-favorite").addEventListener("click", toggleFavorite);
    el("modal-scrape").addEventListener("click", scrapeActiveGame);

    window.RetroNav.onBack = () => {
      if (!el("modal-backdrop").hidden) closeModal();
    };

    let searchTimer;
    el("search").addEventListener("input", (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.search = e.target.value.trim();
        loadGames();
      }, 250);
    });

    loadPlatforms()
      .then(loadGames)
      .then(() => window.RetroNav.ensureInitialFocus());
  }

  document.addEventListener("DOMContentLoaded", init);
})();
