"""One worker of the parallel build: builds every Nth API reference page and writes its own data files.

Started by build_site.py as: ref_shard.py <state file> <worker number>. Progress is saved after every
data file, so a stopped worker continues where it was.
"""
import collections
import json
import pathlib
import pickle
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
state = pickle.loads(pathlib.Path(sys.argv[1]).read_bytes())
k = int(sys.argv[2])
OUT = pathlib.Path(state["out"])
REFERENCE = pathlib.Path(state["reference"])

# Load only the definitions part of build_site.py: everything before the assembly step.
source = (ROOT / "tools" / "build_site.py").read_text(encoding="utf-8")
definitions = source.split("# ---------------- Assemble ----------------", 1)[0]
ns = {"__file__": str(ROOT / "tools" / "build_site.py"), "__name__": "lab_definitions"}
exec(compile(definitions, "build_site.py (definitions)", "exec"), ns)
ns["urls"] = state["urls"]
ns["records_ref"] = state["records_ref"]
ns["ref_stats"] = collections.Counter()

progress_path = OUT / f"shard_{k}.progress.json"
progress = {"fingerprint": state["fingerprint"], "done": 0, "chunks": 0, "rows": {}, "audit": {}, "steps": 0}
if progress_path.exists():
    saved = json.loads(progress_path.read_text(encoding="utf-8"))
    if saved.get("fingerprint") == state["fingerprint"]:
        progress = saved
for leftover in (OUT / "chunks").glob(f"{k}_*.js"):
    if int(leftover.stem.split("_")[1]) >= progress["chunks"]:
        leftover.unlink()

buffer, size, pending_rows, pending_audit, pending_steps = {}, 0, {}, {}, 0


def flush(done_count):
    global buffer, size, pending_rows, pending_audit, pending_steps
    if not buffer:
        return
    name = f"{k}_{progress['chunks']}"
    payload = json.dumps(buffer, ensure_ascii=False, separators=(",", ":"))
    (OUT / "chunks" / f"{name}.js").write_text(f'window.__chunk("{name}",{payload});\n', encoding="utf-8")
    progress["chunks"] += 1
    progress["rows"].update(pending_rows)
    progress["audit"].update(pending_audit)
    progress["steps"] += pending_steps
    progress["done"] = done_count
    temporary = progress_path.with_suffix(".tmp")
    temporary.write_text(json.dumps(progress), encoding="utf-8")
    temporary.replace(progress_path)
    buffer, size, pending_rows, pending_audit, pending_steps = {}, 0, {}, {}, 0


mine = state["work"][k::state["workers"]]
for position, (ref_path, file_path, identifier) in enumerate(mine):
    if position < progress["done"]:
        continue
    file_path = pathlib.Path(file_path)
    item = ns["ref_item"](ref_path, ns["read_record"](file_path), state["by_q"], state["by_name"], state["ast_map"])
    ns["resolve_item"](item)
    item.setdefault("kind", "Simulation")
    encoded = len(json.dumps(item, ensure_ascii=False))
    if size and size + encoded > 700_000:
        flush(position)
    buffer[identifier] = item
    size += encoded
    pending_rows[identifier] = f"{k}_{progress['chunks']}"
    pending_audit[identifier] = {"ref": str(file_path.relative_to(REFERENCE))}
    pending_steps += len(item["steps"])
    if position and position % 5000 == 0:
        print(f"worker {k}: {position:,} of {len(mine):,}", flush=True)
flush(len(mine))
(OUT / f"shard_{k}.json").write_text(json.dumps(progress), encoding="utf-8")
progress_path.unlink(missing_ok=True)
print(f"worker {k}: finished {len(mine):,} pages", flush=True)
