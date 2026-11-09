#!/usr/bin/env python3
"""Compose side-by-side reference-photo vs. Existing-Site 3D vs. Proposed-Home 3D comparison boards
for all six Tirumala site photographs (N-01, N-02, N-03, N-04, NE-01, E-01)."""
from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence" / "tirumala"


def compose_comparison_boards() -> list[str]:
    manifest_path = EVIDENCE_DIR / "photo-reference-manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    written: list[str] = []
    panel_w, panel_h = 640, 440
    pad = 24
    header_h = 92
    board_w = panel_w * 3 + pad * 4
    board_h = header_h + panel_h + pad * 2 + 54

    for item in manifest["photos"]:
        code = item["id"]
        orig_path = ROOT / item["evidence_asset_path"]
        exist_path = EVIDENCE_DIR / f"ref-{code}-existing-site.png"
        prop_path = EVIDENCE_DIR / f"ref-{code}-proposed-home.png"
        if not (orig_path.exists() and exist_path.exists() and prop_path.exists()):
            continue

        board = Image.new("RGB", (board_w, board_h), (246, 244, 238))
        draw = ImageDraw.Draw(board)

        # Header banner
        draw.rectangle([0, 0, board_w, header_h], fill=(34, 41, 47))
        clean_label = item["label"].replace("\u2014", "-").replace("\u2013", "-")
        title = f"{code} - {clean_label} (Original suffix {item['original_number_suffix']})"
        pos_geo = item["camera_position_geo_m"]
        meta = (
            f"Geographic Camera: ({pos_geo[0]:.2f}, {pos_geo[1]:.2f}, {pos_geo[2]:.2f}) m | "
            f"Bearing: {item['bearing_deg']:.0f} deg | Pitch: {item['pitch_deg']:.1f} deg | "
            f"FOV: {item['fov_deg']:.0f} deg | Confidence: {item['confidence']}"
        )
        draw.text((pad, 18), title, fill=(248, 246, 240))
        draw.text((pad, 50), meta, fill=(202, 210, 216))

        panels = [
            (orig_path, f"1. Reference Photograph ({code})"),
            (exist_path, f"2. 3D Existing-Site Mode ({code} Camera)"),
            (prop_path, f"3. 3D Proposed-Home Mode ({code} Camera)"),
        ]
        for idx, (img_path, caption) in enumerate(panels):
            x0 = pad + idx * (panel_w + pad)
            y0 = header_h + pad
            with Image.open(img_path) as im:
                fitted = ImageOps.contain(im.convert("RGB"), (panel_w, panel_h))
                cell = Image.new("RGB", (panel_w, panel_h), (228, 225, 216))
                ox = (panel_w - fitted.width) // 2
                oy = (panel_h - fitted.height) // 2
                cell.paste(fitted, (ox, oy))
                board.paste(cell, (x0, y0))
            draw.rectangle([x0, y0, x0 + panel_w, y0 + panel_h], outline=(160, 156, 146), width=2)
            draw.text((x0 + 8, y0 + panel_h + 12), caption, fill=(40, 44, 48))

        out_file = EVIDENCE_DIR / f"ref-{code}-comparison.png"
        board.save(out_file)
        written.append(str(out_file.relative_to(ROOT)))

    return written


if __name__ == "__main__":
    files = compose_comparison_boards()
    print(json.dumps({"comparison_boards": files}))
