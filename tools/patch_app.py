"""Bring site/app.js up to the format of the large-catalog build. Safe to run twice."""
import pathlib
import runpy
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
target = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "app.js"
if "window.__sec" in target.read_text(encoding="utf-8"):
    print("app.js already up to date")
    sys.exit(0)
sys.argv = [str(ROOT / "tools" / "app_changes.py"), str(target)]
runpy.run_path(sys.argv[0], run_name="__main__")
