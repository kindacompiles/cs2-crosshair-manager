# CS2 Crosshair Manager

A small desktop utility for saving Counter-Strike 2 crosshair presets and writing them into reusable CS2 cfg files.
It lets you quickly switch crosshairs in CS2 by using a bind or simple console command, filling the gap left by the lack of a built-in crosshair manager in the game.

## What it does

- Imports crosshair values from CS2 console output from `find cl_crosshair` or CS2 crosshair share codes
- Saves presets into letter slots
- Writes `crosshairs.cfg` plus per-preset files like `crossa.cfg` into your CS2 cfg folder
- Adds `exec crosshairs` to `autoexec.cfg` if it is missing
- Optionally creates a key bind that cycles through selected presets
- Uses `config.json` so generated cfg files can be recreated

## Run

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Use

1. Open CS2 and run `find cl_crosshair` in the developer console to capture your current crosshair, or copy a CS2 crosshair share code you want to import.
2. Paste it into the app.
3. Click `Import`, then `Save` or `Save All`.
4. Pick your CS2 `cfg` folder if it was not detected automatically.
5. After writing changes, reload them in CS2 with `exec crosshairs`.
6. Use aliases like `crossa`, `crossb`, or the configured cycle bind.

If your `autoexec.cfg` contains `exec crosshairs`, then `exec autoexec` also reloads the manager. Restarting the game also loads it.

## Backup

Back up `config.json` to preserve your saved crosshair library. The app regenerates `crosshairs.cfg` and preset files like `crossa.cfg` from that file.

## Safety

The app rewrites generated cfg files each time, including `crosshairs.cfg` and preset files like `crossa.cfg`.

The only change it may make to `autoexec.cfg` is appending `exec crosshairs` if that line is missing. This lets CS2 load the generated aliases automatically when your autoexec runs. If the app needs to edit an existing `autoexec.cfg`, it creates a timestamped backup first.

Labels, cvar names, cvar values, share codes, and binds are validated before being written.

## Note

This is a focused personal utility, not an official Valve tool. If CS2 cfg or crosshair behavior changes from an update, the app may no longer work. 
Alias and bind commands may be blocked in workshops.
This was built as a personal utility with AI-assisted development and manual testing against CS2 cfg behavior.