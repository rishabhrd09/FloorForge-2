# Inside the Wires: electrical edition of My Desired Home

> **Educational simulation.** The electrical positions, circuits and routes here are proposals drawn on a copy of the house. They are not an installation design, an approved drawing or an as-built record. Real installation design and live electrical work need qualified, licensed professionals. Never open a real energised board or meter.

This folder is a separate edition of **My Desired Home**. Its architectural files (`building.json`, `scene.json`, `project.floorforge.json`, `model.glb`, `preview.html`, `manifest.json` and the rest) are byte-for-byte copies of `examples/gallery/my-desired-home/`. The builder refuses to run if a copy differs, and `tests/test_electrical_tour.py` checks the same thing. The original sample and every other sample are untouched.

Open `electrical.html` straight from this folder (no server needed), open it from the sample gallery, or serve the project and visit `/samples/my-desired-home-electrical/electrical.html`.

## Using the tour

- **Circuits.** Pick a circuit in the side panel. Its concealed route appears as a thin cyan strip on the finished ceiling and wall surfaces in front of the conduit. Walls stay opaque, so you cannot see wiring in other rooms through them.
- **Follow route from meter.** This steps through the selected circuit: sealed meter → main DB (main switch, RCCB, the circuit's MCB) → outgoing terminal blocks → each concealed run → the first switchboard → the switch (and regulator, for a fan) → the point. Use ◀ ▶, `[` `]` or Page Up/Down. In walk mode each step stands you in the room. A conduit step opens a short chase so you can see the conduit cut lengthwise with its conductors inside.
- **Open a board.** In **Walk inside**, click a switchboard, socket plate or DB. The cover plate or DB door swings open on the flush back box. Click any switch, regulator, terminal, connector block, busbar or wire. An amber label appears beside that exact part, showing its circuit, where it comes from and goes to, its role (phase, switched live, regulated live, neutral or protective earth), its phase and whether it is live now. The inspector panel has the longer explanation and source references.
- **Operate it.** Click a switch module to toggle it. Click a regulator to step it. Click a DB device to switch it, or use the controls panel. Only the points on that switch, and only the conductors that feed them, change state. The neutral is never switched. The protective earth never carries load current. The fault buttons show which device would disconnect: earth leakage trips the RCCB, and an overload or short trips the circuit MCB. No currents or trip times are calculated.
- **Fans.** Click a fan canopy to open its ceiling box. You see the hook, and the regulated live, neutral and protective conductors reaching the fan's connector block. The fan's internal motor wiring is not modelled.
- **Wiring plan.** **3D + plan** or **Wiring plan** shows each floor in 2D: walls, door swings, symbols, every conduit, and the selected circuit in cyan. Selection is shared with the 3D view. Scroll to zoom, drag to pan, double-click to refit.

## The house, end to end (as simulated)

1. **Supply (assumed).** A 230/400 V, 50 Hz three-phase four-wire low-voltage service from a local 11 kV / 433 V distribution transformer. The 11 kV feeder ends at that transformer and never enters the house. The project has no sanctioned load or DISCOM record. On CPWD design ratings the modelled points come to about 9 kW before LED lighting. That is above the single-phase limit of most state supply codes. So **three-phase is a reasonable assumption, not a verified fact**: the DISCOM's connection approval decides it.
2. **Meter.** One sealed DISCOM three-phase meter in a meter box outside the entry room. The underground service cable rises inside the external wall into the back of the box. Everything up to and including the meter belongs to the licensee and is live even when the house main switch is off.
3. **Main distribution board.** A double-door TPN MCB board flush in the drawing-room wall, back-to-back with the meter. It is scaled on Schneider Easy9 EZ9ETND08 (422 × 471 × 90 mm). Four meter tails (R, Y, B, N) enter the 4-pole incoming MCB, which is the main switch. Then comes a 4-pole 30 mA Type A RCCB. The RCCB feeds a three-phase comb busbar (R-Y-B repeating) and the neutral bar. The main earthing terminal is the earth bar, linked to two earth-electrode pits outside. Each outgoing circuit has a single-pole MCB on its phase tooth. The P/N/E terminal blocks for every circuit sit in a loose-wire box above the DB (CPWD 3.18.2, Fig. 8). No RCBOs are drawn: CPWD 3.20.9 describes an incoming MCB plus an RCD, and per-circuit RCBOs would be a designer's choice.
4. **First-floor sub-DB.** A sub-main from one main-DB MCB on the blue phase runs in the slab and rises into an SPN double-door board in the upper arrival lobby (scaled on EZ9ESND08). It has a 2-pole isolator, a single-phase comb busbar, neutral and earth bars, and one MCB per circuit. The main 30 mA RCCB covers it.
5. **Final circuits.** Each circuit is single-phase: one phase conductor with its own neutral and protective-earth conductor, drawn together in the same conduit. Lighting circuits carry lights, fans and exhaust fans. Power circuits carry 6 A / 16 A sockets within CPWD 3.10.3's limits. Each water heater has its own circuit. All circuits serving one room are on the same phase, and the phases are balanced on CPWD design ratings.
6. **Concealed routes.** Conduits run in the RCC slab above each storey, laid before concreting. They avoid stair wells and voids, and drop vertically in wall chases to boxes. No run has more than four quarter-bends between boxes; two draw boxes break the longest ones (CPWD 5.4.1(ii)). The strips you see are projections of these routes onto the room surfaces, not visible wiring.
7. **Room switchboards and points.** Flush GI boxes with modular plates (Legrand dimensions) have their box bottom at 1.10 m. Each board terminates its circuit on phase, neutral and earth connector blocks (CPWD 3.5.6). Switches open only the live. A fan switch feeds a 2-module step regulator in series, and the regulated live goes to the fan. Bedside sockets are at 0.70 m and kitchen sockets 23 cm above the counter. Each geyser has a 16 A MCB at 1.10 m beside the bathroom board, with its socket at least 2.05 m above the floor.

Conductor colours follow CPWD 3.5.5: red / yellow / blue phases in the three-phase service, red live in single-phase circuits, black neutral, and green-yellow protective earth. The amber (selection) and cyan (route) markings are overlays, never installed objects.

### Circuit schedule

Generated by the builder from `electrical-model.json`. It shows each circuit's phase, board, protective device and loads; the neutral and protective earth always travel with the phase.

<!-- circuit-schedule:start -->
| Circuit | Board | Phase | Type | Serves | Points | Protection, supply side first |
|---|---|---|---|---|---|---|
| G1 | Main DB | R | Lighting, 1.5 mm² min. | Modular kitchen, Open staircase, Kitchen pantry | light ×7, under-cabinet light ×1 | main switch → 30 mA RCCB → G1 MCB |
| G2 | Main DB | R | Lighting, 1.5 mm² min. | Master bedroom | light ×7, cove strip ×1, ceiling fan ×2 | main switch → 30 mA RCCB → G2 MCB |
| G3 | Main DB | R | Lighting, 1.5 mm² min. | Master attached bathroom | light ×2, mirror light ×1, exhaust fan ×1 | main switch → 30 mA RCCB → G3 MCB |
| G4 | Main DB | Y | Lighting, 1.5 mm² min. | Entry hall, Open puja alcove, Living and dining hall | light ×8, ceiling fan ×2 | main switch → 30 mA RCCB → G4 MCB |
| G5 | Main DB | Y | Lighting, 1.5 mm² min. | Caregiver attached toilet, Caregiver bedroom | light ×3, cove strip ×1, ceiling fan ×1, mirror light ×1, exhaust fan ×1 | main switch → 30 mA RCCB → G5 MCB |
| G6 | Main DB | Y | Lighting, 1.5 mm² min. | Care room | light ×8, ceiling fan ×2 | main switch → 30 mA RCCB → G6 MCB |
| G7 | Main DB | B | Lighting, 1.5 mm² min. | Drawing room & foyer | light ×8, ceiling fan ×1 | main switch → 30 mA RCCB → G7 MCB |
| G8 | Main DB | R | Power, 4 mm² min. | Modular kitchen | 16 A socket ×1 | main switch → 30 mA RCCB → G8 MCB |
| G9 | Main DB | R | Power, 4 mm² min. | Modular kitchen, Master bedroom | 6 A socket ×2, 16 A socket ×1 | main switch → 30 mA RCCB → G9 MCB |
| G10 | Main DB | R | Power, 4 mm² min. | Master attached bathroom, Master bedroom | 6 A socket ×3 | main switch → 30 mA RCCB → G10 MCB |
| G11 | Main DB | Y | Power, 4 mm² min. | Entry hall, Open puja alcove, Living and dining hall | 6 A socket ×3 | main switch → 30 mA RCCB → G11 MCB |
| G12 | Main DB | Y | Power, 4 mm² min. | Caregiver bedroom, Caregiver attached toilet, Care room | 6 A socket ×3 | main switch → 30 mA RCCB → G12 MCB |
| G13 | Main DB | Y | Power, 4 mm² min. | Care room | 16 A socket ×1, 6 A socket ×1 | main switch → 30 mA RCCB → G13 MCB |
| G14 | Main DB | B | Power, 4 mm² min. | Drawing room & foyer | 6 A socket ×1 | main switch → 30 mA RCCB → G14 MCB |
| G15 | Main DB | R | Geyser, 4 mm² min. | Master attached bathroom | 16 A water-heater socket ×1 | main switch → 30 mA RCCB → G15 MCB |
| G16 | Main DB | Y | Geyser, 4 mm² min. | Caregiver attached toilet | 16 A water-heater socket ×1 | main switch → 30 mA RCCB → G16 MCB |
| F1 | Sub-DB | B | Lighting, 1.5 mm² min. | Studio and office, Overlooking living lobby, Upper arrival lobby, Open staircase | light ×10, ceiling fan ×2 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F1 MCB |
| F2 | Sub-DB | B | Lighting, 1.5 mm² min. | Bedroom 2 | light ×4, cove strip ×1, ceiling fan ×1 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F2 MCB |
| F3 | Sub-DB | B | Lighting, 1.5 mm² min. | Master suite | light ×8, cove strip ×1, ceiling fan ×2 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F3 MCB |
| F4 | Sub-DB | B | Lighting, 1.5 mm² min. | Shared upper bathroom | light ×1, mirror light ×1, exhaust fan ×1 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F4 MCB |
| F5 | Sub-DB | B | Power, 4 mm² min. | Overlooking living lobby, Studio and office | 6 A socket ×2 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F5 MCB |
| F6 | Sub-DB | B | Power, 4 mm² min. | Studio and office, Upper arrival lobby | 6 A socket ×3 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F6 MCB |
| F7 | Sub-DB | B | Power, 4 mm² min. | Master suite, Shared upper bathroom | 6 A socket ×3 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F7 MCB |
| F8 | Sub-DB | B | Power, 4 mm² min. | Master suite, Bedroom 2 | 6 A socket ×3 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F8 MCB |
| F9 | Sub-DB | B | Power, 4 mm² min. | Bedroom 2 | 6 A socket ×1 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F9 MCB |
| F10 | Sub-DB | B | Geyser, 4 mm² min. | Shared upper bathroom | 16 A water-heater socket ×1 | main switch → 30 mA RCCB → SUB MCB → sub-DB isolator → F10 MCB |
| SUB | Main DB | B | Submain, by designer | First-floor sub-DB (phase, neutral, PE) | — | main switch → 30 mA RCCB → SUB MCB |

Design load on CPWD ratings (LED lighting not added): R 3.62 kW, Y 3 kW, B 2.66 kW; about 9.3 kW in total.
<!-- circuit-schedule:end -->

## Sourced, assumed, and left to a licensed designer

**Taken from sources** (each item in the tour links its reference):
- CPWD General Specifications Part I (Internal) 2023: mounting heights, circuit limits, conductor minima, conduit size, fill and bends, box and chase practice, colour code, the main-board arrangement, fan mounting and regulator earthing, earth electrodes and the pre-energising tests.
- CEA Measures relating to Safety and Electric Supply Regulations 2023: 30 mA RCD, consumer earthing, no break in the neutral, 1 m clear space in front of switchboards, main switch after the point of supply. Also the CEA metering regulations.
- IS 732:1989 App. C-8.1: fan clearances, and switch-plus-regulator in series.
- Bharat Skills Wireman trade theory: DB height and clearance, meter-then-main-switch order, slab conduit practice.
- Manufacturer data used only for sizes and layout: Schneider Easy9 (BQT58820 and datasheets), Legrand plates and boxes, Polycab wire diameters. IS 1293 pin geometry and IS 9537-3 conduit sizes are also used.

**Assumed for this teaching model** (listed under *What is assumed* in the tour):
- The three-phase supply.
- The meter and DB locations.
- The single-phase sub-DB.
- Circuit grouping and phase allocation.
- Routes.
- Conventional fans with step regulators.
- Water-heater positions.
- Fan, socket and board positions, which are proposals; light positions come from the architectural scene.

**Not designed here; needs a licensed electrical designer, the DISCOM, the electrical inspector and a site survey:**
- Sanctioned load and supply type.
- The earthing system (TN-C-S or TT), the supplier's earthed terminal and the interlink.
- Device ratings and breaking capacities, discrimination, and cable sizes beyond the CPWD minima.
- Voltage drop and fault levels.
- The AFDDs that CPWD 11.2.9.2 asks for in households.
- Surge protection.
- Bonding of metal services.
- Exterior and terrace lighting, and two-way staircase switching.
- AC, washing-machine and oven circuits.
- Real routes around beams, reinforcement and sunken slabs.
- Earth-resistance values, and the CPWD 16.2.4 test results.

## Sources

- [CPWD General Specifications for Electrical Works, Part I (Internal), 2023](https://www.cpwd.gov.in/Publication/CPWD_General_Specification_for_Electrical_Works_Part-I_Internal_2023.pdf)
- [CEA (Measures relating to Safety and Electric Supply) Regulations, 2023](https://cea.nic.in/wp-content/uploads/regulations_cpt/2023/06/pdf_100_183_English-1.pdf) and [CEA metering regulations](https://cea.nic.in/regulations-category/metering-regulations/?lang=en)
- [Bharat Skills: Wireman, 1st Year, Trade Theory (NSQF 2022)](https://bharatskills.gov.in/pdf/E_Books/CTS/119/English/TT/Wireman%20-%201st%20Year%20-%20TT%20%28NSQF%202022%29.pdf)
- [Schneider Electric Easy9 distribution boards (BQT58820)](https://www.se.com/in/en/download/document/BQT58820/) and the [EZ9ETND08 datasheet](https://www.se.com/in/en/product/download-pdf/EZ9ETND08)
- [Legrand India downloads (Mylinc / Lyncus catalogues)](https://www.legrand.co.in/download)
- [IS 732:2019 listing](https://services.bis.gov.in/php/BIS_2.0/bisconnect/ISL/is_details?IDS=MTUyMDM%3D), [IS 732:1989](https://law.resource.org/pub/in/bis/S05/is.732.1989.pdf), [IS 1293:2005](https://law.resource.org/pub/in/bis/S05/is.1293.2005.pdf), [IS 9537-3:1983](https://law.resource.org/pub/in/bis/S05/is.9537.3.1983.pdf)
- Visual inspiration only, not a technical source: [video](https://youtu.be/Do5m06ewhS8)

The full list, with the clause behind each rule, is in `electrical-model.json` (`sources`, `facts`, `assumptions`, `notModelled`) and in the tour's *Sources & assumptions* panel. Positions that could not be placed are listed under *Placement notes*.

## Rebuilding

From the repository root:

```bash
python3 scripts/build_electrical_sample.py
```

```bash
node web/electrical-tour/build.mjs
```

The first command verifies the copied architecture. It then regenerates `electrical-model.json` and `electrical-data.js`, this guide's circuit schedule and `electrical-manifest.json`, and refuses to write a model that fails its geometric or topological checks (`scripts/electrical_validate.py`). The second command bundles `web/electrical-tour/src/` into `electrical-tour.js`. Tests: `tests/test_electrical_tour.py`, and `node --test web/electrical-tour/src/sim.test.js` for the switching logic.
