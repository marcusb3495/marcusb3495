# RetroLauncher

A self-hosted, browser-based ROM frontend/launcher in the spirit of LaunchBox,
Hyperspin, and RetroBat — but running as a local Python web server you open
in any browser on the same machine (or over your LAN), instead of a native
desktop app.

Features:

- **Library scanning** — point a platform at a ROM folder and file extensions;
  RetroLauncher walks it, cleans up filenames (strips `(USA)`, `[!]`, etc. tags),
  and builds a game library in SQLite.
- **Play in browser** — click "Play in Browser" on any game and it runs
  entirely client-side via [EmulatorJS](https://emulatorjs.org) (WebAssembly
  emulator cores), streamed from whichever machine opened the page. No
  desktop app, remote-desktop, or streaming software needed — this is what
  makes RetroLauncher usable from a different machine than the server.
- **Native emulator launching** — alternatively, configure one or more real
  emulators per platform with a launch-argument template (`{rom}` is
  substituted with the ROM's path); the server launches the emulator process
  directly on itself, so its window only appears on the server machine's own
  screen (useful when you're physically at that machine, or want a more
  accurate/full-featured emulator than a browser core provides).
- **Metadata & box art scraping** — pluggable metadata provider interface
  (`backend/app/scraper/`), with an IGDB implementation included. Add your own
  provider (ScreenScraper, TheGamesDB, ...) by implementing `MetadataProvider`.
- **Gamepad navigation** — a 10-foot UI navigable entirely with a connected
  gamepad (via the browser Gamepad API) or keyboard arrow keys, with visible
  focus highlighting and A/B (confirm/back) mapped to launch and close.

## Project layout

```
RetroLauncher/
  backend/
    app/
      main.py           FastAPI app, routing, static file mounts
      models.py          SQLAlchemy models (Platform, Emulator, Game, Setting)
      schemas.py          Pydantic request/response schemas
      scanner.py           ROM folder scanning + filename cleanup
      launcher.py           Emulator process launching
      scraper/               Pluggable metadata/box-art providers (IGDB included)
      routers/                 REST API endpoints
    requirements.txt
    run.py                Entrypoint: `python run.py`
  frontend/
    index.html, settings.html, play.html
    static/css/style.css   Dark, controller-friendly 10-foot UI theme
    static/js/app.js         Library grid, game detail modal, launch/scrape actions
    static/js/gamepad.js       Spatial focus navigation + Gamepad API poll loop
    static/js/settings.js        Platform/emulator/metadata-provider management UI
    static/js/play.js              In-browser gameplay via EmulatorJS (CDN-loaded)
  data/                   SQLite DB + downloaded cover art (gitignored)
```

## Running it

```bash
cd RetroLauncher/backend
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python run.py
```

Then open **http://localhost:8080** in a browser on the same machine.

## First-time setup

1. Go to **Settings** and add a **Platform** (e.g. "Nintendo Entertainment
   System") pointing at the absolute folder path where your ROMs live, plus
   the file extensions to include (e.g. `.nes,.zip`).
2. Set a **Browser Core** for that platform (e.g. `nes`, `snes`, `gba`,
   `genesis`, `psx`) if you want to use **Play in Browser** — this is the
   [EmulatorJS core id](https://emulatorjs.org/docs/system) for that system.
   Leave it blank if you only want native emulator launching.
3. (Optional) Add an **Emulator** for that platform for native launching —
   the absolute path to the emulator executable, and a launch-argument
   template using `{rom}` for the ROM path (e.g. `-fullscreen {rom}`). The
   first emulator you add for a platform is used as the default. Its window
   opens on whichever machine is running the RetroLauncher server, not on
   whatever device you're browsing from — see the note below.
4. Click **Scan** on the platform to build its game list from the ROM folder.
5. (Optional) To pull box art and descriptions automatically, create a free
   Twitch developer application at
   [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps) to get an
   IGDB Client ID + Secret, and paste them into the Metadata & Box Art panel
   in Settings. Then use **Fetch Metadata** on any game's detail view.
6. Back in the library, use a gamepad's D-pad + A/B, or your keyboard's arrow
   keys + Enter/Escape, to browse and launch games.

## Notes & limitations

- **Play in Browser** vs. **Launch Native Emulator** are two independent
  ways to play, and either, both, or neither can be set up per platform:
  - *Play in Browser* runs in the viewer's own browser tab via EmulatorJS
    (WebAssembly), so it works from any device on your network that just
    opens the page — including a different machine than the server. Only
    the ROM bytes are fetched from the server; emulation and rendering all
    happen client-side. The browser needs internet access to load
    EmulatorJS's core files from its CDN (the server does not).
  - *Launch Native Emulator* runs the emulator as a real process on
    whichever machine is running the RetroLauncher server, so its window
    only appears on that machine's own screen — useful when you're
    physically there, or want an emulator with more accuracy/features than
    a browser core provides. It's not a remote game streaming service: if
    you're browsing from a different device, you won't see the window.
- The IGDB provider needs credentials; without them, "Fetch Metadata" returns
  a clear error rather than failing silently. Box art can also be dropped in
  manually later by writing to a game's `cover_path` (a manual-upload UI is a
  natural next addition).
- ROM scanning is name-based (no checksum/DAT matching yet) — good enough for
  a personal library, but a `scanner.py` extension point is where DAT-based
  matching would go if you want LaunchBox-style verified imports later.
