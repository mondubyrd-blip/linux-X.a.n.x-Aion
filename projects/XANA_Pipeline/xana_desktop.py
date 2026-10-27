#!/usr/bin/env python3
"""X.A.N.A local desktop GUI. Standard-library-only; no network calls."""
from __future__ import annotations
import hashlib, json, os, subprocess, sys, tkinter as tk
from datetime import datetime, timezone
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

APP_DIR = Path(__file__).resolve().parent
WORKSPACE = APP_DIR / "xana_workspace"
ASSETS = WORKSPACE / "assets"
MANIFEST = ASSETS / "avatar_manifest.json"
LOG = WORKSPACE / "desktop_audit.jsonl"
ASSET_EXTS = {".glb", ".gltf", ".fbx", ".obj", ".stl", ".png", ".jpg", ".jpeg", ".webp", ".blend", ".json"}

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def audit(event: str, **details):
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    row = {"time_utc": datetime.now(timezone.utc).isoformat(), "event": event, **details}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

class XanaDesktop(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("X.A.N.A Pipeline — Local Desktop")
        self.geometry("1000x680")
        self.minsize(760, 520)
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        ASSETS.mkdir(parents=True, exist_ok=True)
        self._build()
        self.refresh()

    def _build(self):
        header = ttk.Frame(self, padding=14); header.pack(fill="x")
        ttk.Label(header, text="X.A.N.A Pipeline", font=("TkDefaultFont", 18, "bold")).pack(anchor="w")
        ttk.Label(header, text="Local desktop asset control · no cloud calls · no automatic installs").pack(anchor="w", pady=(4, 0))
        actions = ttk.Frame(self, padding=(12, 0, 12, 8)); actions.pack(fill="x")
        for title, command in [
            ("Refresh", self.refresh), ("Import assets", self.import_assets),
            ("Build manifest", self.build_manifest), ("Open workspace", self.open_workspace),
            ("View audit log", self.view_log), ("Component paths", self.configure_components),
        ]:
            ttk.Button(actions, text=title, command=command).pack(side="left", padx=(0, 6))
        split = ttk.Panedwindow(self, orient="horizontal"); split.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        left = ttk.Frame(split, padding=8); right = ttk.Frame(split, padding=8)
        split.add(left, weight=3); split.add(right, weight=4)
        ttk.Label(left, text="Local assets", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.assets = ttk.Treeview(left, columns=("size", "sha"), show="tree headings")
        self.assets.heading("#0", text="Asset"); self.assets.heading("size", text="Bytes"); self.assets.heading("sha", text="SHA-256")
        self.assets.column("size", width=90, stretch=False); self.assets.column("sha", width=250, stretch=True)
        self.assets.pack(fill="both", expand=True, pady=(6, 0))
        ttk.Label(right, text="Status and audit", font=("TkDefaultFont", 11, "bold")).pack(anchor="w")
        self.out = tk.Text(right, wrap="word", state="disabled", font=("TkFixedFont", 9))
        scroll = ttk.Scrollbar(right, orient="vertical", command=self.out.yview); self.out.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y"); self.out.pack(fill="both", expand=True, pady=(6, 0))
        ttk.Label(self, text="Application-level local operation does not replace OS-level network isolation.", padding=(12, 0, 12, 8)).pack(anchor="w")

    def log(self, value):
        text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False, default=str)
        self.out.configure(state="normal"); self.out.insert("end", text + "\n\n"); self.out.see("end"); self.out.configure(state="disabled")

    def refresh(self):
        for item in self.assets.get_children(): self.assets.delete(item)
        files = sorted(p for p in ASSETS.rglob("*") if p.is_file() and p != MANIFEST)
        rows = []
        for p in files:
            try:
                digest = sha256_file(p); size = p.stat().st_size
                self.assets.insert("", "end", text=str(p.relative_to(ASSETS)), values=(size, digest[:16] + "…"))
                rows.append({"path": str(p.relative_to(WORKSPACE)), "bytes": size, "sha256": digest})
            except OSError as exc:
                self.log({"asset_error": str(p), "error": str(exc)})
        self.log({"workspace": str(WORKSPACE), "asset_count": len(rows), "manifest_exists": MANIFEST.exists(), "network": "no network calls implemented"})
        audit("refresh", asset_count=len(rows))

    def import_assets(self):
        chosen = filedialog.askopenfilenames(title="Select local assets")
        if not chosen: return
        imported = []
        for raw in chosen:
            src = Path(raw)
            if src.suffix.lower() not in ASSET_EXTS:
                if not messagebox.askyesno("Unusual file type", f"{src.name} is not a recognized 3D/image asset. Import anyway?"): continue
            dest = ASSETS / src.name
            if dest.exists():
                dest = ASSETS / f"{src.stem}_{sha256_file(src)[:8]}{src.suffix}"
            try:
                import shutil
                shutil.copy2(src, dest)
                imported.append({"name": dest.name, "bytes": dest.stat().st_size, "sha256": sha256_file(dest)})
            except OSError as exc:
                messagebox.showerror("Import failed", f"{src}: {exc}")
        audit("assets_imported", assets=imported)
        self.log({"imported": imported}); self.refresh()

    def build_manifest(self):
        rows = []
        for p in sorted(ASSETS.rglob("*")):
            if p.is_file() and p != MANIFEST:
                rows.append({"path": str(p.relative_to(WORKSPACE)), "bytes": p.stat().st_size, "sha256": sha256_file(p)})
        payload = {"schema_version": 1, "generated_utc": datetime.now(timezone.utc).isoformat(), "storage": "local", "assets": rows}
        MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        audit("manifest_written", path=str(MANIFEST), asset_count=len(rows))
        self.log({"manifest": str(MANIFEST), "asset_count": len(rows), "status": "written locally"})
        messagebox.showinfo("Manifest built", f"Recorded {len(rows)} assets in:\n{MANIFEST}")
        self.refresh()

    def open_workspace(self):
        try:
            if sys.platform.startswith("win"): os.startfile(str(WORKSPACE))
            elif sys.platform == "darwin": subprocess.Popen(["open", str(WORKSPACE)])
            else: subprocess.Popen(["xdg-open", str(WORKSPACE)])
        except Exception as exc: messagebox.showerror("Open workspace failed", str(exc))

    def view_log(self):
        if LOG.exists():
            self.log(LOG.read_text(encoding="utf-8")[-20000:])
        else: self.log("No audit events recorded yet.")

    def configure_components(self):
        win = tk.Toplevel(self); win.title("Local component paths"); win.geometry("680x260")
        ttk.Label(win, text="Enter paths to existing local component directories. This screen records paths only; it does not install or execute them.", wraplength=620).pack(anchor="w", padx=12, pady=12)
        config_path = WORKSPACE / "components.json"
        try: config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
        except (OSError, json.JSONDecodeError): config = {}
        entries = {}
        for key in ("bodylab", "layer_forge", "avatar_factory", "humanhead"):
            row = ttk.Frame(win, padding=(12, 4)); row.pack(fill="x")
            ttk.Label(row, text=key, width=16).pack(side="left")
            var = tk.StringVar(value=config.get(key, ""))
            ttk.Entry(row, textvariable=var).pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="Browse", command=lambda v=var: v.set(filedialog.askdirectory() or v.get())).pack(side="left", padx=6)
            entries[key] = var
        def save():
            data = {k: v.get().strip() for k, v in entries.items()}
            result = {}
            for k, value in data.items():
                p = Path(value).expanduser() if value else None
                result[k] = {"path": str(p) if p else "", "exists": bool(p and p.exists() and p.is_dir())}
            config_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            audit("component_paths_saved", components=result)
            self.log({"component_paths": result})
            win.destroy()
        ttk.Button(win, text="Save paths locally", command=save).pack(anchor="e", padx=12, pady=12)

if __name__ == "__main__":
    XanaDesktop().mainloop()
