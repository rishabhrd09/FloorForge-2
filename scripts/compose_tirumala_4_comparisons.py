#!/usr/bin/env python3
"""Compose side-by-side visual comparison sheets for Tirumala 4:
1. Reference Photographs & Video Frames vs Tirumala 4 Calibrated 3D Views
   - R07 (East frontage looking NW) vs ref-r07-east-northwest.png & ref-r07-existing-plot.png
   - R11 (NE plot corner, wall, pier & verge) vs ref-r11-ne-corner.png
   - R08 (North colony garden & opposite white/navy house) vs ref-r08-north-garden.png
   - V01 (East basketball court, hoop, drain slabs & road) vs ref-v01-east-court-road.png
   - R13 / R09 (Colony junction, concrete road, drain slabs & homes) vs ref-r09-colony-junction.png
   - R14 / V03 (Mauve-taupe wall, grooved pier, hedge, pavers & streetlight) vs ref-r14-wall-pole-paving.png
2. Tirumala 3 (Before) vs Tirumala 4 (After) Same-Camera Architectural Comparison
   - Northeast Exterior (car on vs default car off + calibrated colony)
   - East Frontage Exterior
   - Home ICU -> Veranda & North Garden
   - Connected Kitchen, Living & Dining Hall
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PROMPT_PACK = ROOT / "output" / "tirumala-4-prompt-pack"
T3_RENDERS = ROOT / "examples" / "gallery" / "tirumala-3" / "renders"
T4_RENDERS = ROOT / "examples" / "gallery" / "tirumala-4" / "renders"
DELIVERY_DIR = ROOT / "output" / "tirumala-4-delivery"


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        if bold
        else [
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    )
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _fit_tile(img_path: Path, w: int, h: int) -> Image.Image:
    im = Image.open(img_path).convert("RGB")
    return ImageOps.fit(im, (w, h), method=Image.Resampling.LANCZOS)


def build_reference_comparison_sheet() -> Path:
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    rows = [
        (
            "R07 — East Frontage Looking NW (Owner-Confirmed)",
            "Shows NE corner plot, mauve-taupe wall, road & white/navy house across North garden; pre-construction trees separated into 'Existing plot' mode",
            PROMPT_PACK / "site-photos" / "R07-east-side-northwest.png",
            T4_RENDERS / "ref-r07-east-northwest.png",
            T4_RENDERS / "ref-r07-existing-plot.png",
            "Site Photo R07 (1000145296.jpg)",
            "Tirumala 4 — Proposed Home (ref_r07_east_northwest)",
            "Tirumala 4 — Existing Plot Mode (Site: Existing plot)",
        ),
        (
            "R11 / V02 — Northeast Plot Corner, Pier & Paver Verge (Owner-Confirmed; Duplicate Photo Note Recorded)",
            "12 m North road × 9 m East road; photographed colony wall retained, proposed house boundary refined in ivory/limestone with low leaf planting",
            PROMPT_PACK / "site-photos" / "R11-NE-corner-owner-labelled.png",
            T4_RENDERS / "ref-r11-ne-corner.png",
            T4_RENDERS / "exterior-northeast.png",
            "Site Photo R11 (1000145311.jpg · Primary NE Label)",
            "Tirumala 4 — Calibrated NE Corner (ref_r11_ne_corner)",
            "Tirumala 4 — NE Hero Exterior (Empty Porch Default)",
        ),
        (
            "R08 / N-01 — North Colony Garden & Opposite White/Navy House (Approximate Matched View)",
            "Looking North across 12 m concrete road into fenced colony garden, palms/shade trees, pergola & opposite G+1 white/navy residence",
            PROMPT_PACK / "site-photos" / "R08-north-garden-outlook.png",
            T4_RENDERS / "ref-r08-north-garden.png",
            T4_RENDERS / "veranda-north-garden-outlook.png",
            "Site Photo R08 (1000145302.jpg)",
            "Tirumala 4 — North Road & Garden (ref_r08_north_garden)",
            "Tirumala 4 — Veranda Eye-Level North Garden Outlook",
        ),
        (
            "V01 / E-01 — East 9 m Road, Storm-Drain Slabs & Basketball Court (Owner-Confirmed Video Frame 00:00.5)",
            "Precast drain slabs with paired circular holes, paver verge, chain-link court enclosure, hoop/backboard, palms & post-top park lamp",
            PROMPT_PACK / "video-frames" / "V01-court-and-road.jpg",
            T4_RENDERS / "ref-v01-east-court-road.png",
            T4_RENDERS / "exterior-east.png",
            "Video Frame V01 (00:00.500 · East Court & Road)",
            "Tirumala 4 — East Court & Drain Slabs (ref_v01_east_court_road)",
            "Tirumala 4 — East Elevation Across 9 m Road",
        ),
        (
            "R13 / R09 / V04 — Colony Road Junction, Streetlight & Neighbouring Homes (Estimated Camera Offset, Transient Cars Excluded)",
            "Grooved concrete carriageways, precast drain cover slabs, paver verges, angled LED streetlight & 2–3 storey colony houses (parked cars excluded)",
            PROMPT_PACK / "site-photos" / "R13-colony-junction-wide.png",
            T4_RENDERS / "ref-r09-colony-junction.png",
            PROMPT_PACK / "video-frames" / "V04-colony-street.jpg",
            "Site Photo R13 (1000145305.jpg · Transient Cars Excluded)",
            "Tirumala 4 — Colony Junction (ref_r09_colony_junction)",
            "Video Frame V04 (00:08.500 · 12 m North Street)",
        ),
        (
            "R14 / V03 / V05 — Boundary Wall, Mixed Hedge, Pavers & Streetlight (Material Reference; Exact Bearing Unconfirmed)",
            "Colony character: muted mauve-grey walls, pale coping, mixed leaf planting, interlocking pavers and slim streetlights; new house wall uses ivory/limestone",
            PROMPT_PACK / "site-photos" / "R14-wall-pole-and-paving.png",
            T4_RENDERS / "ref-r14-wall-pole-paving.png",
            PROMPT_PACK / "video-frames" / "V03-boundary-and-planting.jpg",
            "Site Photo R14 (1000145307.jpg · Wall, Pole & Pavers)",
            "Tirumala 4 — Close Material Study (ref_r14_wall_pole_paving)",
            "Video Frame V03 (00:06.000 · Boundary & Hedge)",
        ),
    ]

    tile_w, tile_h = 560, 364
    pad = 24
    row_h = tile_h + 84
    header_h = 104
    W = pad * 4 + tile_w * 3
    H = header_h + len(rows) * row_h + pad

    canvas = Image.new("RGB", (W, H), "#f6f2ea")
    draw = ImageDraw.Draw(canvas)
    f_title = _load_font(26, bold=True)
    f_sub = _load_font(15, bold=False)
    f_row = _load_font(17, bold=True)
    f_note = _load_font(13, bold=False)
    f_cap = _load_font(13, bold=True)

    draw.rectangle([0, 0, W, header_h - 10], fill="#24201c")
    draw.text(
        (pad, 20),
        "TIRUMALA 4 — PHOTO & VIDEO REFERENCES vs UPDATED REAL-TIME 3D VIEWS",
        fill="#f7f3eb",
        font=f_title,
    )
    draw.text(
        (pad, 58),
        "Locked P13 Geometry (geometryHash: b6484526b300...) · Empty Car Porch Default · Transient Road Vehicles Excluded · Pre-Construction Trees in 'Existing Plot' Mode",
        fill="#d5cbb8",
        font=f_sub,
    )

    for idx, (r_title, r_sub, p1, p2, p3, c1, c2, c3) in enumerate(rows):
        y0 = header_h + idx * row_h
        draw.text((pad, y0), r_title, fill="#221e1a", font=f_row)
        draw.text((pad, y0 + 23), r_sub, fill="#5c5349", font=f_note)
        ty = y0 + 46
        for c_idx, (img_p, cap) in enumerate([(p1, c1), (p2, c2), (p3, c3)]):
            tx = pad + c_idx * (tile_w + pad)
            tile = _fit_tile(img_p, tile_w, tile_h)
            canvas.paste(tile, (tx, ty))
            draw.rectangle([tx, ty + tile_h - 28, tx + tile_w, ty + tile_h], fill="#1f1b18")
            draw.text((tx + 10, ty + tile_h - 22), cap, fill="#f4efe6", font=f_cap)
            draw.rectangle([tx, ty, tx + tile_w, ty + tile_h], outline="#bfb4a2", width=2)

    out1 = T4_RENDERS / "reference-comparison-sheet.png"
    out2 = DELIVERY_DIR / "reference-comparison-sheet.png"
    canvas.save(out1, optimize=True)
    canvas.save(out2, optimize=True)
    return out1


def build_before_after_sheet() -> Path:
    DELIVERY_DIR.mkdir(parents=True, exist_ok=True)
    pairs = [
        (
            "Northeast Corner Exterior (`exterior_northeast`)",
            "Tirumala 3: Parked car in porch by default, generic grey boundary wall",
            "Tirumala 4: My Desired Home facade, ivory/limestone boundary, low planting and owner-confirmed vacant adjoining grass lots",
            T3_RENDERS / "exterior-northeast.png",
            T4_RENDERS / "exterior-northeast.png",
        ),
        (
            "East Arrival Frontage (`exterior_east`)",
            "Tirumala 3: Car obstructing lower Kota porch view",
            "Tirumala 4: Lower Kota porch, retained forecourt, charcoal window frames, stone feature and adjoining grass land",
            T3_RENDERS / "exterior-east.png",
            T4_RENDERS / "exterior-east.png",
        ),
        (
            "Home ICU → Veranda & North Garden (`interior_icu_veranda_garden` — Identical Camera & 150.8 sq ft Room)",
            "Tirumala 3: Cooler interior shadow cast",
            "Tirumala 4: Warm 2-bounce light probe, ivory marble floor response, folded linen throw, monitor & teak window pelmets",
            T3_RENDERS / "interior-icu-veranda-garden.png",
            T4_RENDERS / "interior-icu-veranda-garden.png",
        ),
        (
            "Connected Kitchen, Living & Dining Hall (`interior_kitchen_living_dining` — Identical Camera & Layout)",
            "Tirumala 3: Baseline P13 open hall",
            "Tirumala 4: Warm task lighting, tableware on serving divider, framed botanical diptych & balanced daylight",
            T3_RENDERS / "interior-kitchen-living-dining.png",
            T4_RENDERS / "interior-kitchen-living-dining.png",
        ),
    ]

    tile_w, tile_h = 760, 494
    pad = 28
    row_h = tile_h + 78
    header_h = 98
    W = pad * 3 + tile_w * 2
    H = header_h + len(pairs) * row_h + pad

    canvas = Image.new("RGB", (W, H), "#f6f2ea")
    draw = ImageDraw.Draw(canvas)
    f_title = _load_font(26, bold=True)
    f_sub = _load_font(15, bold=False)
    f_row = _load_font(18, bold=True)
    f_cap = _load_font(14, bold=True)

    draw.rectangle([0, 0, W, header_h - 10], fill="#24201c")
    draw.text(
        (pad, 18),
        "TIRUMALA 3 (BEFORE) vs TIRUMALA 4 (AFTER) — SAME PHYSICAL CAMERA & LOCKED P13 GEOMETRY",
        fill="#f7f3eb",
        font=f_title,
    )
    draw.text(
        (pad, 56),
        "Identical room polygons, wall thicknesses, openings, furniture footprint & FOV — comparing colony context, empty porch default & material/lighting realism",
        fill="#d5cbb8",
        font=f_sub,
    )

    for idx, (title, cap_before, cap_after, p_before, p_after) in enumerate(pairs):
        y0 = header_h + idx * row_h
        draw.text((pad, y0), title, fill="#221e1a", font=f_row)
        ty = y0 + 32
        for c_idx, (img_p, cap) in enumerate([(p_before, cap_before), (p_after, cap_after)]):
            tx = pad + c_idx * (tile_w + pad)
            tile = _fit_tile(img_p, tile_w, tile_h)
            canvas.paste(tile, (tx, ty))
            draw.rectangle([tx, ty + tile_h - 30, tx + tile_w, ty + tile_h], fill="#1f1b18")
            draw.text((tx + 12, ty + tile_h - 23), cap, fill="#f4efe6", font=f_cap)
            draw.rectangle([tx, ty, tx + tile_w, ty + tile_h], outline="#bfb4a2", width=2)

    out1 = T4_RENDERS / "tirumala-3-vs-4-comparison.png"
    out2 = DELIVERY_DIR / "tirumala-3-vs-4-comparison.png"
    canvas.save(out1, optimize=True)
    canvas.save(out2, optimize=True)
    return out1


if __name__ == "__main__":
    p1 = build_reference_comparison_sheet()
    p2 = build_before_after_sheet()
    print(f"Wrote {p1} and {p2}")
