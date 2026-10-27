# X.A.N.A Pipeline — Local Desktop GUI

A local-first Tkinter desktop control panel for the X.A.N.A avatar asset pipeline.

## Run

Requires Python 3.10+ and Tkinter (usually packaged as `python3-tk` on Debian/Ubuntu).

```bash
python3 xana_desktop.py
```

The application uses only the Python standard library. It does not automatically download dependencies or make cloud API calls. It defaults to local files and writes imported assets and a SHA-256 manifest under `./xana_workspace/`.

## Features

- Local asset import and SHA-256 inventory
- JSON manifest generation
- Workspace file browser
- Explicit component-path configuration
- Local audit log
- No automatic network activity

## Scope and safety

This is the standalone desktop GUI entry point. It does not bundle the full 100+ MB integrated workspace archive or proprietary/source archives. Component execution must be configured with local paths; the GUI does not pretend a component is installed just because a path was entered. “Local-only” here means this app makes no network requests; it does not replace OS firewall or network isolation.

## License

No license is declared here. All rights and licensing remain with the original project owner unless a separate license is added.
