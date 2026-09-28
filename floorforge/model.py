from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any
import hashlib, json, math
from pathlib import Path

class DesignError(ValueError):
    def __init__(self, code: str, message: str, details: Any = None):
        super().__init__(message)
        self.code, self.details = code, details
    def record(self):
        return {'code': self.code, 'message': str(self), 'details': self.details}

def canonical(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf8')

def sha(data: Any) -> str:
    return hashlib.sha256(canonical(data)).hexdigest()

def atomic(path: Path, data: bytes) -> None:
    import tempfile, os
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp=f.name; f.write(data); f.flush(); os.fsync(f.fileno())
    try: os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def read_json(path: Path):
    def bad(v): raise DesignError('NONFINITE_JSON', 'NaN and infinity are not permitted.')
    return json.loads(path.read_text('utf8'), parse_constant=bad)

DEFAULTS = {
    'title': 'The Verandah House', 'width_mm': 12192, 'depth_mm': 18288,
    'road_bearing_deg': 180., 'bedrooms': 3, 'storeys': 2, 'budget_lakh': 65., 'attached_baths': 'all',
    'style': 'warm', 'finish': 'standard', 'open_kitchen': True, 'parking': False,
    'pooja': True, 'eldercare': False, 'vastu': 'moderate', 'front_mm': 3300,
    'rear_mm': 1200, 'left_mm': 1100, 'right_mm': 1100,
    'latitude': 22.72, 'longitude': 75.86, 'timezone_hours': 5.5,
    'solar_date': '2026-03-21', 'solar_hour': 15.,
    'soil': 'unknown', 'plinth_mm': 450, 'floor_height_mm': 3150,
    'rate_low_inr_ft2': 2000., 'rate_high_inr_ft2': 2800.,
    'cost_contingency_pct': 10., 'variant': 0,
    'exterior_theme': 'modern_tropical', 'interior_theme': 'bright_natural',
    'change_policy': 'exterior_refinement', 'interior_layout_locked': True,
    'seed': 0, 'theme_version': '1',
}
SOURCE_PRIORITY = {'defaults':0, 'survey':10, 'text':20, 'sketch':30, 'grid':40, 'plan':40, 'edit':50}
STYLES = {
    'warm': {'label':'Warm stone & timber','wall':'#e5ddc9','accent':'#827762','wood':'#785035','frame':'#293732','roof':'#3a413b','signature':'Deep framed portal, stone blade and timber soffit'},
    'minimal': {'label':'Quiet modern','wall':'#e9e8df','accent':'#777d79','wood':'#907356','frame':'#252e2e','roof':'#424c4a','signature':'Thin horizontal canopies and a recessed steel entry'},
    'tropical': {'label':'Tropical verandah','wall':'#ece8d9','accent':'#ac956d','wood':'#795d3e','frame':'#38483d','roof':'#6d5c47','signature':'Deep shaded verandah with a timber pergola'},
    'terracotta': {'label':'Earth & terracotta','wall':'#eee0cc','accent':'#a45d42','wood':'#6d4933','frame':'#41453c','roof':'#9e634c','signature':'Round portico columns and terracotta screening'},
    'graphite': {'label':'Graphite & bronze','wall':'#656a63','accent':'#ac8e60','wood':'#6d4d38','frame':'#202927','roof':'#303a34','signature':'Recessed dark volumes, bronze fins and warm recessed light'},
    'concrete': {'label':'Concrete & glass','wall':'#b6b5ab','accent':'#7c8077','wood':'#997555','frame':'#303833','roof':'#878b83','signature':'Expressed concrete slab edges and broad glazed bays'},
}

@dataclass
class Space:
    id: str
    name: str
    kind: str
    floor: int
    polygon: list[list[float]]
    clear: list[list[float]] = field(default_factory=list)
    area_m2: float = 0.

@dataclass
class Wall:
    id: str
    floor: int
    a: list[float]
    b: list[float]
    thickness: float
    height: float
    rooms: list[str]
    external: bool
    polygon: list[list[float]] = field(default_factory=list)

@dataclass
class Opening:
    id: str
    wall_id: str
    floor: int
    kind: str
    offset: float
    width: float
    sill: float
    height: float
    connects: list[str]
    swing: str | None = None   # the room a hinged leaf opens into
    hinge: str = 'start'       # which jamb carries the hinges: 'start' (at offset) or 'end' (offset + width)


def local_to_enu(x: float, y: float, bearing: float):
    a=math.radians(bearing)
    return (-math.cos(a)*x-math.sin(a)*y, math.sin(a)*x-math.cos(a)*y)

def enu_to_local(e: float,n: float,bearing: float):
    a=math.radians(bearing)
    return (-math.cos(a)*e+math.sin(a)*n,-math.sin(a)*e-math.cos(a)*n)
