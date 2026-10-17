"""Focused checks for the separate electrical teaching edition of My Desired Home.

Preservation (the copied architecture stays byte-identical to the original), geometry
(flush mounts on clear walls, conduits embedded in walls and slabs, reveal strips on
finished surfaces), connectivity (every conductor's physical path and the terminal
netlist), circuit rules taken from the cited sources, walk-through and plan data,
packaging, and the switching logic (run through Node when it is installed).
"""
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from electrical_geometry import House, inside, SOFFIT, FLOOR_HEIGHT  # noqa: E402
from electrical_validate import (validate, check_conduits, check_conductor_paths, check_netlist,  # noqa: E402
                                 check_rules, check_mounts, classify_point, _bends, _slab, _in_slab)

GALLERY = ROOT / "examples/gallery"
SOURCE = GALLERY / "my-desired-home"
EDITION = GALLERY / "my-desired-home-electrical"
ELECTRICAL_FILES = {"electrical.html", "electrical-tour.js", "electrical-data.js", "electrical-model.json",
                    "electrical-manifest.json", "ELECTRICAL_GUIDE.md", "viewer.js"}
SWITCHED = ("downlight", "cove", "mirror-light", "undercabinet", "fan", "exhaust")


@pytest.fixture(scope="module")
def building():
    return json.loads((SOURCE / "building.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scene():
    return json.loads((SOURCE / "scene.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def model():
    return json.loads((EDITION / "electrical-model.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def house(building, scene):
    return House(building, scene)


def index(model):
    out = {}
    for key in ("enclosures", "devices", "terminals", "switches", "regulators", "points", "boxes", "circuits",
                "conduits", "conductors"):
        for item in model[key]:
            out[item["id"]] = item
    return out


def seg_dist(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0., min(1., ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L))
    return math.dist(p, (a[0] + dx * t, a[1] + dy * t))


# ------------------------------------------------------------------ preservation and packaging
def test_copied_architecture_is_byte_identical_to_the_original():
    files = sorted(p.relative_to(SOURCE) for p in SOURCE.rglob("*") if p.is_file() and p.name != ".DS_Store")
    assert files, "original sample is missing"
    for rel in files:
        assert (EDITION / rel).read_bytes() == (SOURCE / rel).read_bytes(), rel
    extra = {str(p.relative_to(EDITION)) for p in EDITION.rglob("*") if p.is_file() and p.name != ".DS_Store"
             and not (SOURCE / p.relative_to(EDITION)).exists()}
    assert extra == ELECTRICAL_FILES


def test_electrical_manifest_records_the_edition_files():
    manifest = json.loads((EDITION / "electrical-manifest.json").read_text(encoding="utf-8"))
    assert manifest["sourceSample"] == "my-desired-home"
    assert set(manifest["files"]) == ELECTRICAL_FILES - {"electrical-manifest.json"}
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((EDITION / name).read_bytes()).hexdigest() == digest, name
    for rel, digest in manifest["architecture"].items():
        assert hashlib.sha256((SOURCE / rel).read_bytes()).hexdigest() == digest, rel


def test_tour_page_loads_its_data_offline():
    page = (EDITION / "electrical.html").read_text(encoding="utf-8")
    for src in ("viewer.js", "electrical-data.js", "electrical-tour.js"):
        assert f'src="{src}"' in page
    assert "Educational simulation" in page and "qualified" in page
    assert (EDITION / "viewer.js").read_bytes() == (ROOT / "web/viewer.js").read_bytes()
    prefix = "window.__ELECTRICAL_TOUR_DATA__="
    packed = (EDITION / "electrical-data.js").read_text(encoding="utf-8")
    assert packed.startswith(prefix) and packed.endswith(";\n")
    data = json.loads(packed[len(prefix):-2])
    assert data["scene"] == json.loads((EDITION / "scene.json").read_text(encoding="utf-8"))
    assert data["model"] == json.loads((EDITION / "electrical-model.json").read_text(encoding="utf-8"))


def test_model_belongs_to_this_house(model, building):
    assert model["schema"] == "floorforge.electrical-tour.v3"
    assert model["architecturalPlanHash"] == building["planHash"]
    assert "simulation" in model["status"].lower()


def test_stored_model_is_reproducible_from_the_builder(model):
    from build_electrical_sample import build_model
    rebuilt, _ = build_model()
    assert json.loads(json.dumps(rebuilt)) == model


def test_guide_schedule_matches_the_model_and_states_the_boundary(model):
    from build_electrical_sample import circuit_schedule
    guide = (EDITION / "ELECTRICAL_GUIDE.md").read_text(encoding="utf-8")
    assert circuit_schedule(model) in guide
    for phrase in ("Educational simulation", "not a verified fact", "qualified, licensed professionals", "AFDD"):
        assert phrase in guide


# ------------------------------------------------------------------ geometry
def test_full_validation_reports_no_problems(model, building, house):
    report = validate(model, building, house)
    assert {k: v for k, v in report.items() if v} == {}


def test_enclosures_are_flush_on_clear_wall_spans(model, building, house):
    assert check_mounts(model, building, house) == []
    for e in model["enclosures"]:
        m = e["mount"]
        wall = house.walls[m["wallId"]]
        assert wall.floor == e["floor"], e["id"]
        assert wall.sides[m["side"]] == ("outside" if e.get("exterior") else e["roomId"]), e["id"]
        span = house.face_span(wall, m["side"], e["roomId"]) if not e.get("exterior") else (0, wall.length)
        assert span[0] - 1e-6 <= m["along"] - e["size"]["w"] / 2 and m["along"] + e["size"]["w"] / 2 <= span[1] + 1e-6, e["id"]
        if not e.get("exterior"):
            assert not house.behind_door(wall, m["side"], m["along"], e["size"]["w"], e["roomId"]), e["id"]
        # recessed boxes leave masonry behind them
        assert e["size"]["depth"] <= wall.thickness - .04, e["id"]


def test_mounting_heights_follow_the_cited_rules(model):
    for e in model["enclosures"]:
        centre = e["mount"]["face"][2] - e["floor"] * FLOOR_HEIGHT
        bottom, top = centre - e["size"]["boxH"] / 2, centre + e["size"]["h"] / 2
        if e["kind"] in ("switchboard", "geyser-mcb"):
            assert bottom == pytest.approx(1.10, abs=.005), e["id"]           # CPWD 3.15.1(c), 3.11.6(c)
        if e["kind"] == "geyser-outlet":
            assert bottom >= 2.0, e["id"]                                      # CPWD 3.11.6(c)
        if e["kind"] == "socket-plate":
            expected = {"bedside": .70, "counter": .865 + .23}.get(e["purpose"], 1.10)
            assert bottom == pytest.approx(expected, abs=.006), e["id"]       # CPWD 3.11.6
        if e["kind"] in ("main-db", "sub-db", "loose-wire-box"):
            assert top <= 2.0 + 1e-6, e["id"]                                  # WM pp. 269-270
    meter = next(e for e in model["enclosures"] if e["kind"] == "meter")
    assert meter["mount"]["face"][2] - model["distribution"]["ground"] == pytest.approx(1.30, abs=.01)


def test_distribution_boards_sit_where_the_sources_put_them(model, house):
    encs = {e["id"]: e for e in model["enclosures"]}
    dist = model["distribution"]
    db, meter, sub = encs[dist["mainDB"]], encs[dist["meter"]], encs[dist["subDB"]]
    entry_rooms = {r for w in house.walls.values() for o in w.openings if o.kind == "entry" for r in o.connects}
    assert db["roomId"] in entry_rooms                                         # CPWD 3.20.9
    assert meter["exterior"] and meter["mount"]["wallId"] == db["mount"]["wallId"]
    assert meter["mount"]["side"] == -db["mount"]["side"]
    assert sub["floor"] == 1 and house.rooms[sub["roomId"]]["kind"] not in ("bathroom", "kitchen")   # CPWD 3.19
    for board in (db, sub):                                                    # 1 m clear in front (CEA Reg. 39)
        m = board["mount"]
        wall = house.walls[m["wallId"]]
        level = board["floor"] * FLOOR_HEIGHT
        assert house.blockers(wall, m["side"], m["along"], board["size"]["w"] + .1, level + .2, level + 2.0, 1.0,
                              ignore=("wall-tile", "curtain", "detail", "fixture", "downlight", "cove")) == [], board["id"]
    lwb = encs[db["lwb"]]
    assert lwb["mount"]["wallId"] == db["mount"]["wallId"] and lwb["mount"]["face"][2] > db["mount"]["face"][2]


def test_every_conduit_is_embedded_never_in_open_air(model, building):
    assert check_conduits(model, building) == []
    # bends between the end boxes (the ends themselves sit inside a box or enclosure)
    kinds = {classify_point(building, *p) for c in model["conduits"] for p in c["points"][1:-1]}
    assert None not in kinds and {"wall", "slab"} <= kinds


def test_slab_runs_stay_inside_the_slab_and_avoid_its_openings(model, building):
    slabs = {f: _slab(building, f) for f in (0, 1)}
    checked = 0
    for c in model["conduits"]:
        for a, b in zip(c["points"], c["points"][1:]):
            if abs(a[2] - b[2]) > 1e-6 or a[2] < 0:
                continue
            floor = int(a[2] // FLOOR_HEIGHT)
            if not (floor * FLOOR_HEIGHT + SOFFIT - 1e-6 <= a[2] <= (floor + 1) * FLOOR_HEIGHT):
                continue                      # horizontal pieces inside walls are covered by the wall check
            for k in range(21):
                t = k / 20
                assert _in_slab(slabs[floor], a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), (c["id"], a, b)
            checked += 1
    assert checked > 50


def test_conduit_bends_and_sizes_follow_cpwd(model):
    for c in model["conduits"]:
        if c["function"] in ("lighting", "power", "submain"):
            assert _bends(c["points"]) <= 4.01, c["id"]                       # CPWD 5.4.1(ii)
        if c["function"] in ("lighting", "power"):
            assert c["diameter"] in (20, 25), c["id"]                         # CPWD 4.3.1: at least 20 mm
    assert any(b["kind"] == "draw-box" for b in model["boxes"])


def test_reveal_strips_lie_on_finished_room_surfaces(model, house):
    rooms = {r["id"]: r for r in model["rooms"]}
    on_tiles = 0
    for c in model["conduits"]:
        for p in c["reveal"]:
            assert p["roomId"] in rooms or p["roomId"] == "outside", (c["id"], p)
            if p["surface"] == "ceiling":
                z = house.soffit(p["floor"]) - .002
                assert p["a"][2] == pytest.approx(z, abs=.001) and p["b"][2] == pytest.approx(z, abs=.001)
                mid = ((p["a"][0] + p["b"][0]) / 2, (p["a"][1] + p["b"][1]) / 2)
                assert inside(*mid, rooms[p["roomId"]]["polygon"]), (c["id"], p)
                assert house.overhead_bottom(*mid, p["floor"]) >= house.soffit(p["floor"]) - .005
            else:
                wall = house.walls[p["wallId"]]
                proud = abs(wall.offset(p["a"][:2])) - wall.half
                assert .001 <= proud <= .036, (c["id"], p)
                on_tiles += proud > .01
                assert wall.sides[1 if wall.offset(p["a"][:2]) > 0 else -1] == p["roomId"]
    assert on_tiles, "strips on tiled walls should sit on the tile face"


def test_fans_hang_from_the_solid_slab_clear_of_walls(model, house):
    fans = [p for p in model["points"] if p["kind"] == "fan"]
    assert len(fans) >= 10
    boxes = {b["id"]: b for b in model["boxes"]}
    rooms = {r["id"]: r for r in model["rooms"]}
    for p in fans:
        box = boxes[p["boxId"]]
        assert box["kind"] == "fan-box"
        soffit = house.soffit(p["floor"])
        assert box["position"][2] == pytest.approx(soffit)
        assert soffit - (p["floor"] * FLOOR_HEIGHT + 2.69) >= .3 - 1e-6         # IS 732:1989 C-8.1
        assert house.overhead_bottom(p["position"][0], p["position"][1], p["floor"]) == pytest.approx(soffit)
        poly = rooms[p["roomId"]]["polygon"]
        clearance = min(seg_dist(p["position"][:2], poly[k], poly[(k + 1) % len(poly)]) for k in range(len(poly)))
        assert clearance >= p["sweep"] / 2000 + .3 - 1e-6, p["id"]
        assert p["sweep"] in (900, 1050, 1200, 1400) and "CPWD Table 3.1" in p["basis"]


# ------------------------------------------------------------------ connectivity and topology
def test_every_conductor_follows_a_continuous_physical_path(model):
    assert check_conductor_paths(model) == []
    terms = {t["id"]: t for t in model["terminals"]}
    for k in model["conductors"]:
        if k["conduits"]:
            continue
        a, b = terms[k["from"]], terms[k["to"]]
        assert (a.get("boxId") or a["enclosureId"]) == (b.get("boxId") or b["enclosureId"]), k["id"]


def test_every_point_is_fed_from_the_meter_with_neutral_and_earth(model):
    assert check_netlist(model) == []


def test_protective_relationships_are_explicit(model):
    ids = index(model)
    incomer = next(d for d in model["devices"] if d["kind"] == "mcb4p")
    rccb = next(d for d in model["devices"] if d["kind"] == "rccb4p")
    assert rccb["residual"] and rccb["rating"]["sensitivity"].startswith("30 mA")      # CEA Reg. 44
    sub = next(c for c in model["circuits"] if c["id"] == "SUB")
    for c in model["circuits"]:
        mcb = ids[c["mcb"]]
        assert mcb["kind"] == "mcb" and mcb["poles"] == 1 and mcb["phase"] == c["phase"] and mcb["circuitId"] == c["id"]
        assert c["chain"][:2] == [incomer["id"], rccb["id"]] and c["chain"][-1] == mcb["id"]
        if c["floor"] == 1:
            assert sub["mcb"] in c["chain"] and any(ids[d]["kind"] == "isolator2p" for d in c["chain"]), c["id"]
    mcbs = [d for d in model["devices"] if d["kind"] == "mcb"]
    assert len(mcbs) == len(model["circuits"]) == len({d["circuitId"] for d in mcbs})
    main = [d for d in mcbs if d["enclosureId"] == model["distribution"]["mainDB"]]
    assert len({d["slot"] for d in main}) == len(main)
    assert all(("R", "Y", "B")[d["slot"] % 3] == d["phase"] for d in main)   # comb busbar order


def test_phase_and_neutral_stay_together_and_earth_is_never_a_return(model):
    conductors = {k["id"]: k for k in model["conductors"]}
    for c in model["conduits"]:
        roles = {}
        for kid in c["carries"]:
            k = conductors[kid]
            roles.setdefault(k["circuitId"], set()).add(k["role"])
        for cid, rs in roles.items():
            if cid and rs & {"L", "SW", "REG"}:
                assert {"N", "PE"} <= rs, (c["id"], cid, rs)                  # CPWD 3.5.3, 5.4.4(a)
    for k in model["conductors"]:
        if k["role"] == "PE":
            assert k["serves"] == [], k["id"]
    single_pole = {d["id"] for d in model["devices"] if d["kind"] in ("switch", "switch16", "local-mcb", "mcb", "regulator")}
    terms = {t["id"]: t for t in model["terminals"]}
    for k in model["conductors"]:
        if k["role"] == "N":
            for tid in (k["from"], k["to"]):
                assert terms.get(tid, {}).get("deviceId") not in single_pole, k["id"]   # no break in the neutral


def test_circuits_follow_cpwd_grouping_and_rooms_stay_on_one_phase(model):
    assert check_rules(model) == []
    points = {p["id"]: p for p in model["points"]}
    assert {"lighting", "power", "geyser", "submain"} <= {c["kind"] for c in model["circuits"]}
    for c in model["circuits"]:
        pts = [points[p] for p in c["points"]]
        if c["kind"] == "lighting":
            assert 0 < len(pts) <= 20 and all(p["kind"] in SWITCHED for p in pts), c["id"]   # CPWD 3.5.4, 3.10.1
        if c["kind"] == "geyser":
            assert [p["kind"] for p in pts] == ["geyser-outlet"], c["id"]                      # CPWD 3.10.3
        if c["kind"] == "power":
            n16 = sum(p["kind"] == "socket16" for p in pts)
            n6 = sum(p["kind"] == "socket6" for p in pts)
            assert (n16, n6) in {(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2), (2, 0)}, c["id"]
    loads = model["supply"]["phaseLoadW"]
    assert max(loads.values()) - min(loads.values()) <= 1200                                  # CPWD 3.2.10
    assert model["supply"]["designLoadKW"] > 5


def test_switchboards_reflect_their_own_rooms(model):
    boards = [e for e in model["enclosures"] if e["kind"] == "switchboard"]
    layouts = set()
    for room in {b["roomId"] for b in boards}:
        mine = [b for b in boards if b["roomId"] == room]
        switched = {p for s in model["switches"] if s["enclosureId"] in {b["id"] for b in mine} for p in s["points"]}
        expected = {p["id"] for p in model["points"] if p["roomId"] == room and p["kind"] in SWITCHED}
        assert switched == expected, room
        fans = sum(1 for p in model["points"] if p["roomId"] == room and p["kind"] == "fan")
        assert sum(m["kind"] == "regulator" for b in mine for m in b["modules"]) == fans, room
    for b in boards:
        layouts.add(tuple(sorted(m["kind"] for m in b["modules"] if m["kind"] != "blank")))
        assert {"P", "N", "E"} <= set(b["connectors"])                                         # CPWD 3.5.6
    assert len(layouts) >= 5


def test_fan_wiring_runs_switch_then_regulator_then_fan(model):
    ids = index(model)
    for p in [p for p in model["points"] if p["kind"] == "fan"]:
        reg = ids[ids[p["regulator"]]["deviceId"]]
        feeds = [k for k in model["conductors"] if k["to"] == p["terminals"]["L"]]
        assert len(feeds) == 1 and feeds[0]["role"] == "REG", p["id"]
        lead = feeds[0]
        while lead["from"] != reg["terminals"]["out"]:          # through the ceiling box, if looped
            lead = next(k for k in model["conductors"] if k["to"] == lead["from"] and k["role"] == "REG")
        series = [k for k in model["conductors"] if k["to"] == reg["terminals"]["in"]]
        assert len(series) == 1 and series[0]["role"] == "SW", p["id"]                    # IS 732:1989 C-8.1
        assert ids[ids[series[0]["from"]]["deviceId"]]["kind"] == "switch"
        assert any(k["to"] == p["terminals"]["N"] and k["role"] == "N" for k in model["conductors"])
        assert any(k["to"] == p["terminals"]["E"] and k["role"] == "PE" for k in model["conductors"])
        assert any(k["to"] == reg["terminals"]["earth"] and k["role"] == "PE" for k in model["conductors"])   # CPWD 3.16.3


# ------------------------------------------------------------------ walk-through and plan data
def test_traces_run_from_the_meter_to_a_point_with_standing_views(model):
    rooms = {r["id"]: r for r in model["rooms"]}
    meter = model["distribution"]["meter"]
    assert set(model["traces"]) == {c["id"] for c in model["circuits"]}
    for cid, steps in model["traces"].items():
        assert steps[0]["refs"][0] == meter, cid
        assert [s["n"] for s in steps] == list(range(1, len(steps) + 1))
        circuit = next(c for c in model["circuits"] if c["id"] == cid)
        if cid != "SUB":
            assert any(r in circuit["points"] for r in steps[-1]["refs"]), cid
        assert sum(1 for s in steps if s["view"]["foot"] is None) <= 1, cid
        for s in steps:
            view = s["view"]
            if view["foot"] is not None and view["roomId"] is not None:
                assert inside(view["foot"][0], view["foot"][1], rooms[view["roomId"]]["polygon"]), (cid, s["n"])


def test_plan_data_covers_both_floors(model):
    floors = {f["floor"]: f for f in model["plan"]["floors"]}
    assert set(floors) == {0, 1}
    for f in floors.values():
        assert f["walls"] and f["rooms"] and f["openings"]
    assert any(f["voids"] for f in floors.values())
    assert {c["planFloor"] for c in model["conduits"]} == {0, 1}


def test_sources_assumptions_and_exclusions_are_explicit(model):
    sources = {s["id"]: s for s in model["sources"]}
    for f in model["facts"]:
        assert f["source"] in sources and f["ref"], f["id"]
        assert f["kind"] in {"requirement", "recommendation", "manufacturer", "training", "regulation"}
    assert all(s["url"].startswith("https://") for s in sources.values())
    urls = " ".join(s["url"] for s in sources.values())
    for needle in ("CPWD_General_Specification_for_Electrical_Works_Part-I_Internal_2023", "BQT58820",
                   "legrand.co.in/download", "Wireman%20-%201st%20Year", "cea.nic.in", "youtu.be/Do5m06ewhS8"):
        assert needle in urls
    assert all(a["confirm"] for a in model["assumptions"])
    supply = next(a for a in model["assumptions"] if a["id"] == "A-SUPPLY")
    assert "not a verified fact" in supply["text"] and f"{model['supply']['designLoadKW']} kW" in supply["text"]
    assert any("AFDD" in n["title"] for n in model["notModelled"])


# ------------------------------------------------------------------ interaction logic
def test_switching_logic_passes_its_node_tests():
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    result = subprocess.run([node, "--test", "web/electrical-tour/src/sim.test.js"], cwd=ROOT,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-2000:]
