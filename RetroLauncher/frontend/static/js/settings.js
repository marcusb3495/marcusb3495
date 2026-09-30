(function () {
  const el = (id) => document.getElementById(id);
  let platforms = [];

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

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str == null ? "" : String(str);
    return d.innerHTML;
  }

  // ---------------- Platforms ----------------

  async function loadPlatforms() {
    platforms = await api("/api/platforms");
    renderPlatforms();
    renderPlatformSelect();
    await loadEmulators();
  }

  function renderPlatforms() {
    const container = el("platform-rows");
    container.innerHTML = "";
    if (platforms.length === 0) {
      container.innerHTML = '<p class="meta">No platforms yet.</p>';
      return;
    }
    for (const p of platforms) {
      const row = document.createElement("div");
      row.className = "list-row";
      const iconSrc = p.icon_path ? `/media/platform_icons/${p.icon_path}` : "";
      row.innerHTML = `
        <div class="platform-icon-row">
          ${
            iconSrc
              ? `<img class="platform-icon-preview" src="${iconSrc}" alt="" />`
              : '<div class="platform-icon-preview"></div>'
          }
          <div class="info">
            <input class="search-box" data-role="name-input" value="${escapeHtml(p.name)}"
                   placeholder="Platform name" style="max-width: 220px; padding: 6px 10px; margin-bottom: 4px" />
            <div class="sub">${p.game_count} games</div>
          </div>
        </div>
        <div class="platform-icon-row">
          <input class="search-box" data-role="folder-input" value="${escapeHtml(p.folder_path)}"
                 placeholder="ROM folder path" style="max-width: 280px; padding: 6px 10px" />
          <input class="search-box" data-role="ext-input" value="${escapeHtml(p.extensions)}"
                 placeholder="Extensions (.nes,.zip)" style="max-width: 160px; padding: 6px 10px" />
        </div>
        <div class="platform-icon-row">
          <input class="search-box" data-role="core-input" value="${escapeHtml(p.browser_core || "")}"
                 placeholder="Browser core (e.g. nes)" style="max-width: 160px; padding: 6px 10px" />
          <input class="search-box" data-role="ss-system-input" value="${escapeHtml(p.screenscraper_system_id || "")}"
                 placeholder="ScreenScraper system ID" style="max-width: 160px; padding: 6px 10px" />
          <button class="btn" data-nav data-action="save-platform">Save Platform</button>
        </div>
        <div class="platform-icon-row">
          <input class="search-box" data-role="gamelist-input"
                 value="${escapeHtml(p.folder_path)}/gamelist.xml"
                 placeholder="Path to gamelist.xml" style="max-width: 320px; padding: 6px 10px" />
          <button class="btn" data-nav data-action="import-gamelist">Import Gamelist (RetroBat/Batocera)</button>
        </div>
        <div>
          <button class="btn" data-nav data-action="icon">Set Icon</button>
          <button class="btn" data-nav data-action="scan">Scan</button>
          <button class="btn danger" data-nav data-action="delete">Delete</button>
          <input type="file" accept="image/*,.svg" data-role="icon-input" hidden />
        </div>
      `;
      const iconInput = row.querySelector('[data-role="icon-input"]');
      row.querySelector('[data-action="icon"]').addEventListener("click", () => iconInput.click());
      iconInput.addEventListener("change", () => {
        if (iconInput.files[0]) uploadPlatformIcon(p.id, iconInput.files[0]);
      });
      row.querySelector('[data-action="scan"]').addEventListener("click", () => scanPlatform(p.id));
      row.querySelector('[data-action="delete"]').addEventListener("click", () => deletePlatform(p.id));
      const nameInput = row.querySelector('[data-role="name-input"]');
      const folderInput = row.querySelector('[data-role="folder-input"]');
      const extInput = row.querySelector('[data-role="ext-input"]');
      const coreInput = row.querySelector('[data-role="core-input"]');
      const ssSystemInput = row.querySelector('[data-role="ss-system-input"]');
      row.querySelector('[data-action="save-platform"]').addEventListener("click", () =>
        savePlatform(p.id, {
          name: nameInput.value.trim(),
          folder_path: folderInput.value.trim(),
          extensions: extInput.value.trim(),
          browser_core: coreInput.value.trim() || null,
          screenscraper_system_id: ssSystemInput.value.trim() || null,
        })
      );
      const gamelistInput = row.querySelector('[data-role="gamelist-input"]');
      row.querySelector('[data-action="import-gamelist"]').addEventListener("click", () =>
        importGamelist(p.id, gamelistInput.value.trim())
      );
      container.appendChild(row);
    }
  }

  async function importGamelist(platformId, gamelistPath) {
    if (!gamelistPath) {
      toast("Enter a gamelist.xml path first");
      return;
    }
    try {
      const result = await api(`/api/platforms/${platformId}/import-gamelist`, {
        method: "POST",
        body: JSON.stringify({ gamelist_path: gamelistPath }),
      });
      toast(
        `Imported ${result.matched}/${result.total_entries} entries ` +
          `(${result.covers_imported} cover art) - ${result.not_found} not matched to a scanned game`
      );
      await loadPlatforms();
    } catch (err) {
      toast(`Gamelist import failed: ${err.message}`);
    }
  }

  async function savePlatform(platformId, fields) {
    if (!fields.name || !fields.folder_path) {
      toast("Name and ROM folder path can't be empty");
      return;
    }
    try {
      await api(`/api/platforms/${platformId}`, {
        method: "PUT",
        body: JSON.stringify(fields),
      });
      toast("Platform settings saved");
      await loadPlatforms();
    } catch (err) {
      toast(`Failed to save platform settings: ${err.message}`);
    }
  }

  async function uploadPlatformIcon(platformId, file) {
    const formData = new FormData();
    formData.append("file", file);
    try {
      const resp = await fetch(`/api/platforms/${platformId}/icon`, {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.detail || resp.statusText);
      }
      toast("Icon updated");
      await loadPlatforms();
    } catch (err) {
      toast(`Failed to upload icon: ${err.message}`);
    }
  }

  function renderPlatformSelect() {
    const select = el("e-platform");
    const previous = select.value;
    select.innerHTML = platforms
      .map((p) => `<option value="${p.id}">${escapeHtml(p.name)}</option>`)
      .join("");
    if (previous && platforms.some((p) => String(p.id) === previous)) {
      select.value = previous;
    }
  }

  async function scanPlatform(id) {
    try {
      const result = await api(`/api/platforms/${id}/scan`, { method: "POST" });
      toast(`Scan complete: ${result.added} new game(s) added (${result.total_roms_found} ROM files found).`);
      await loadPlatforms();
    } catch (e) {
      toast(`Scan failed: ${e.message}`);
    }
  }

  async function deletePlatform(id) {
    if (!confirm("Delete this platform and all its games? This does not delete ROM files.")) return;
    await api(`/api/platforms/${id}`, { method: "DELETE" });
    await loadPlatforms();
  }

  el("platform-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api("/api/platforms", {
        method: "POST",
        body: JSON.stringify({
          name: el("p-name").value.trim(),
          folder_path: el("p-folder").value.trim(),
          extensions: el("p-ext").value.trim(),
          browser_core: el("p-core").value.trim() || null,
          screenscraper_system_id: el("p-ss-system").value.trim() || null,
        }),
      });
      el("platform-form").reset();
      toast("Platform added");
      await loadPlatforms();
    } catch (err) {
      toast(`Failed to add platform: ${err.message}`);
    }
  });

  // ---------------- Emulators ----------------

  async function loadEmulators() {
    const platformId = el("e-platform").value;
    const container = el("emulator-rows");
    if (!platformId) {
      container.innerHTML = '<p class="meta">Add a platform first.</p>';
      return;
    }
    const emulators = await api(`/api/emulators?platform_id=${platformId}`);
    container.innerHTML = "";
    if (emulators.length === 0) {
      container.innerHTML = '<p class="meta">No emulators configured for this platform yet.</p>';
      return;
    }
    for (const em of emulators) {
      const row = document.createElement("div");
      row.className = "list-row";
      row.innerHTML = `
        <div class="info">
          <div>${escapeHtml(em.name)} ${em.is_default ? "<span class=\"sub\">(default)</span>" : ""}</div>
          <div class="sub">${escapeHtml(em.executable_path)} ${escapeHtml(em.args_template)}</div>
        </div>
        <div>
          <button class="btn danger" data-nav data-action="delete">Delete</button>
        </div>
      `;
      row.querySelector('[data-action="delete"]').addEventListener("click", () => deleteEmulator(em.id));
      container.appendChild(row);
    }
  }

  async function deleteEmulator(id) {
    await api(`/api/emulators/${id}`, { method: "DELETE" });
    await loadEmulators();
  }

  el("e-platform").addEventListener("change", loadEmulators);

  el("emulator-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const platformId = el("e-platform").value;
    if (!platformId) {
      toast("Add a platform first");
      return;
    }
    try {
      await api("/api/emulators", {
        method: "POST",
        body: JSON.stringify({
          platform_id: Number(platformId),
          name: el("e-name").value.trim(),
          executable_path: el("e-exec").value.trim(),
          args_template: el("e-args").value.trim() || "{rom}",
          is_default: true,
        }),
      });
      el("emulator-form").reset();
      el("e-args").value = "{rom}";
      toast("Emulator added");
      await loadEmulators();
    } catch (err) {
      toast(`Failed to add emulator: ${err.message}`);
    }
  });

  // ---------------- Metadata settings ----------------

  async function loadSettings() {
    const settings = await api("/api/settings");
    const byKey = Object.fromEntries(settings.map((s) => [s.key, s.value]));

    if (byKey.metadata_provider) el("s-provider").value = byKey.metadata_provider;

    if (byKey.igdb_client_id) el("s-client-id").value = byKey.igdb_client_id;
    // Secret fields are masked by the API; leave them blank so the user isn't
    // shown a fake value, but note that a saved secret exists via placeholder.
    if (byKey.igdb_client_secret) el("s-client-secret").placeholder = "•••••••• (saved)";

    if (byKey.screenscraper_devid) el("s-ss-devid").value = byKey.screenscraper_devid;
    if (byKey.screenscraper_devpassword) el("s-ss-devpassword").placeholder = "•••••••• (saved)";
    if (byKey.screenscraper_softname) el("s-ss-softname").value = byKey.screenscraper_softname;
    if (byKey.screenscraper_ssid) el("s-ss-ssid").value = byKey.screenscraper_ssid;
    if (byKey.screenscraper_sspassword) el("s-ss-sspassword").placeholder = "•••••••• (saved)";
  }

  async function saveSetting(key, value) {
    if (value === "" || value == null) return;
    await api("/api/settings", { method: "PUT", body: JSON.stringify({ key, value }) });
  }

  el("save-settings").addEventListener("click", async () => {
    try {
      await saveSetting("metadata_provider", el("s-provider").value);

      await saveSetting("igdb_client_id", el("s-client-id").value.trim());
      await saveSetting("igdb_client_secret", el("s-client-secret").value.trim());

      await saveSetting("screenscraper_devid", el("s-ss-devid").value.trim());
      await saveSetting("screenscraper_devpassword", el("s-ss-devpassword").value.trim());
      await saveSetting("screenscraper_softname", el("s-ss-softname").value.trim());
      await saveSetting("screenscraper_ssid", el("s-ss-ssid").value.trim());
      await saveSetting("screenscraper_sspassword", el("s-ss-sspassword").value.trim());

      toast("Settings saved");
    } catch (err) {
      toast(`Failed to save settings: ${err.message}`);
    }
  });

  function init() {
    window.RetroNav.onBack = () => (window.location.href = "/");
    loadPlatforms();
    loadSettings();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
