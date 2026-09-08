# RetroLauncher

A self-hosted, browser-based ROM frontend/launcher in the spirit of LaunchBox,
Hyperspin, and RetroBat — but running as a local Python web server you open
in any browser on the same machine (or over your LAN), instead of a native
desktop app.

Features:

- **Library scanning** — point a platform at a ROM folder and file extensions;
  RetroLauncher walks it, cleans up filenames (strips `(USA)`, `[!]`, etc. tags),
  and builds a game library in SQLite.
- **Emulator launching** — configure one or more emulators per platform with a
  launch-argument template (`{rom}` is substituted with the ROM's path); the
  server launches the emulator process directly, so it must run on the same
  machine as your emulators.
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
    index.html, settings.html
    static/css/style.css   Dark, controller-friendly 10-foot UI theme
    static/js/app.js         Library grid, game detail modal, launch/scrape actions
    static/js/gamepad.js       Spatial focus navigation + Gamepad API poll loop
    static/js/settings.js        Platform/emulator/metadata-provider management UI
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
2. Add an **Emulator** for that platform — the absolute path to the emulator
   executable, and a launch-argument template using `{rom}` for the ROM path
   (e.g. `-fullscreen {rom}`). The first emulator you add for a platform is
   used as the default.
3. Click **Scan** on the platform to build its game list from the ROM folder.
4. (Optional) To pull box art and descriptions automatically, create a free
   Twitch developer application at
   [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps) to get an
   IGDB Client ID + Secret, and paste them into the Metadata & Box Art panel
   in Settings. Then use **Fetch Metadata** on any game's detail view.
5. Back in the library, use a gamepad's D-pad + A/B, or your keyboard's arrow
   keys + Enter/Escape, to browse and launch games.

## Notes & limitations

- Because launching a game runs a subprocess on the server, RetroLauncher is
  meant to be run on the same PC as your emulators — not as a remote game
  streaming service.
- The IGDB provider needs credentials; without them, "Fetch Metadata" returns
  a clear error rather than failing silently. Box art can also be dropped in
  manually later by writing to a game's `cover_path` (a manual-upload UI is a
  natural next addition).
- ROM scanning is name-based (no checksum/DAT matching yet) — good enough for
  a personal library, but a `scanner.py` extension point is where DAT-based
  matching would go if you want LaunchBox-style verified imports later.
