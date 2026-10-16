"""Build the separate electrical teaching edition of My Desired Home.

The original sample (examples/gallery/my-desired-home) is read only. Its files are
copied byte-for-byte into the electrical edition; this script then adds an
independent electrical model, packaged data for offline use and its own manifest.
It refuses to write a model that fails the geometry, path, netlist or rule checks.

    python3 scripts/build_electrical_sample.py
    node web/electrical-tour/build.mjs
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from electrical_design import Design                      # noqa: E402
import electrical_network as network                       # noqa: E402
from electrical_export import model_dict                   # noqa: E402
from electrical_validate import validate                   # noqa: E402

ROOT = HERE.parent
GALLERY = ROOT / "examples/gallery"
SOURCE = GALLERY / "my-desired-home"
DEST = GALLERY / "my-desired-home-electrical"
THUMBNAILS = GALLERY / "thumbnails"
CATALOG = GALLERY / "catalog.json"
# Files only the electrical edition has. Everything else in DEST must equal SOURCE byte-for-byte.
ELECTRICAL_FILES = ("electrical.html", "electrical-tour.js", "electrical-data.js", "electrical-model.json",
                    "electrical-manifest.json", "ELECTRICAL_GUIDE.md", "viewer.js")
# Copies an earlier version of this script edited; they are restored from the source.
RESTORABLE = ("preview.html", "manifest.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def architectural_files():
    return sorted(p.relative_to(SOURCE) for p in SOURCE.rglob("*") if p.is_file() and p.name != ".DS_Store")


def sync_copy() -> list[str]:
    """Make every architectural file in the edition byte-identical to the original."""
    if not DEST.exists():
        shutil.copytree(SOURCE, DEST)
        shutil.copy2(THUMBNAILS / "my-desired-home.png", THUMBNAILS / "my-desired-home-electrical.png")
    restored = []
    for rel in architectural_files():
        src, dst = SOURCE / rel, DEST / rel
        if dst.exists() and dst.read_bytes() == src.read_bytes():
            continue
        if not dst.exists() or str(rel) in RESTORABLE:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(str(rel))
            continue
        raise ValueError(f"Copied architectural file differs from the original: {rel}")
    extra = [p.relative_to(DEST) for p in DEST.rglob("*") if p.is_file() and p.name != ".DS_Store"
             and not (SOURCE / p.relative_to(DEST)).exists() and str(p.relative_to(DEST)) not in ELECTRICAL_FILES]
    if extra:
        raise ValueError(f"Unexpected files in the electrical edition: {extra}")
    return restored


def build_model():
    building = json.loads((SOURCE / "building.json").read_text(encoding="utf-8"))
    scene = json.loads((SOURCE / "scene.json").read_text(encoding="utf-8"))
    if building["planHash"] != scene["planHash"]:
        raise ValueError("Architectural source hashes disagree")
    d = Design(building, scene)
    d.collect_rooms()
    network.place_distribution(d)
    d.design_rooms()
    network.group_circuits(d)
    network.build_boards(d)
    network.wire_everything(d)
    model = model_dict(d, building["planHash"])
    report = validate(model, building, d.house)
    problems = [f"{k}: {p}" for k, v in report.items() for p in v]
    if problems:
        raise ValueError("Electrical model failed its checks:\n" + "\n".join(problems[:40]))
    return model, scene


def main() -> None:
    restored = sync_copy()
    model, scene = build_model()
    (DEST / "electrical-model.json").write_text(json.dumps(model, separators=(",", ":"), ensure_ascii=False) + "\n",
                                                encoding="utf-8")
    # Browsers block fetch(file://...) from a local page, so the same data is also packaged as a classic script.
    packed = "window.__ELECTRICAL_TOUR_DATA__=" + json.dumps({"scene": scene, "model": model}, separators=(",", ":"),
                                                             ensure_ascii=True) + ";\n"
    (DEST / "electrical-data.js").write_text(packed, encoding="utf-8")
    shutil.copy2(ROOT / "web/viewer.js", DEST / "viewer.js")
    update_guide(model)
    write_manifest()
    ensure_catalog()
    counts = {k: len(model[k]) for k in ("enclosures", "points", "circuits", "conduits", "conductors")}
    print(f"Electrical edition: {counts}; restored copies: {restored or 'none'}")


GUIDE_START, GUIDE_END = "<!-- circuit-schedule:start -->", "<!-- circuit-schedule:end -->"
POINT_NAMES = {"downlight": "light", "cove": "cove strip", "mirror-light": "mirror light", "undercabinet": "under-cabinet light",
               "fan": "ceiling fan", "exhaust": "exhaust fan", "socket6": "6 A socket", "socket16": "16 A socket",
               "geyser-outlet": "16 A water-heater socket"}


def circuit_schedule(model) -> str:
    points = {p["id"]: p for p in model["points"]}
    devices = {d["id"]: d for d in model["devices"]}
    boards = {e["id"]: e for e in model["enclosures"]}
    rooms = {r["id"]: r["name"] for r in model["rooms"]}
    short = {"mcb4p": "main switch", "rccb4p": "30 mA RCCB", "isolator2p": "sub-DB isolator"}
    lines = ["| Circuit | Board | Phase | Type | Serves | Points | Protection, supply side first |",
             "|---|---|---|---|---|---|---|"]
    for c in model["circuits"]:
        board = "Main DB" if c["db"] == model["distribution"]["mainDB"] else "Sub-DB"
        chain = " → ".join(short.get(devices[d]["kind"], devices[d]["label"]) for d in c["chain"])
        counts = {}
        for pid in c["points"]:
            counts[points[pid]["kind"]] = counts.get(points[pid]["kind"], 0) + 1
        loads = ", ".join(f"{POINT_NAMES.get(k, k)} ×{n}" for k, n in counts.items()) or "—"
        serves = ", ".join(rooms[r] for r in c["rooms"]) or "First-floor sub-DB (phase, neutral, PE)"
        size = f"{c['conductorSize']:g} mm² min." if c.get("conductorSize") else "by designer"
        lines.append(f"| {c['id']} | {board} | {c['phase']} | {c['kind'].capitalize()}, {size} | {serves} | {loads} | {chain} |")
    load = model["supply"]["phaseLoadW"]
    lines.append("")
    lines.append(f"Design load on CPWD ratings (LED lighting not added): R {load['R'] / 1000:g} kW, Y {load['Y'] / 1000:g} kW, "
                 f"B {load['B'] / 1000:g} kW; about {model['supply']['designLoadKW']:g} kW in total.")
    return "\n".join(lines)


def update_guide(model):
    guide = DEST / "ELECTRICAL_GUIDE.md"
    text = guide.read_text(encoding="utf-8")
    start, end = text.index(GUIDE_START) + len(GUIDE_START), text.index(GUIDE_END)
    guide.write_text(text[:start] + "\n" + circuit_schedule(model) + "\n" + text[end:], encoding="utf-8")


def write_manifest():
    manifest_path = DEST / "electrical-manifest.json"
    files = {name: sha(DEST / name) for name in ELECTRICAL_FILES
             if name != "electrical-manifest.json" and (DEST / name).exists()}
    manifest = {"schema": "floorforge.electrical-edition-manifest.v1",
                "sourceSample": "my-desired-home",
                "architecture": {str(rel): sha(SOURCE / rel) for rel in architectural_files()},
                "files": files}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def ensure_catalog():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if any(s["id"] == "my-desired-home-electrical" for s in catalog):
        return
    base = next(s for s in catalog if s["id"] == "my-desired-home")
    entry = {**base, "id": "my-desired-home-electrical", "title": "My Desired Home · Inside the Wires",
             "description": "A separate copy of the veranda house with an interactive, India-focused electrical tour. "
                            "Explore the meter, boards, protected circuits and concealed route traces.",
             "style": "Electrical simulation", "directory": "gallery/my-desired-home-electrical",
             "sourceSample": "my-desired-home", "featurePage": "electrical.html", "hasElectricalTour": True}
    catalog.insert(1, entry)
    CATALOG.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
