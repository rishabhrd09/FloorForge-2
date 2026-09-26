# Executed verification — 0.2.0-alpha

**This release is runnable but does not complete the original M0–M8 requirements.** See the 80-row requirement matrix.

## Executed here

112 tests passed, 0 failed (18.75 seconds) in the final run. Two clean default generations compared 23 published artifacts with no differences, on the same host/runtime.

Three fully generated examples are bundled: 40×60 ft G+1 with three bedrooms, 30×40 ft ground floor with two bedrooms, and 25×35 ft ground floor with one bedroom. The manual L-grid is an additional input fixture. Geometric acceptance is not a guarantee of construction or regulatory safety.

Each sample DXF was re-imported with ezdxf, and each GLB with Trimesh. IFC4 received only self-reference-integrity checks; no independent schema/BIM-viewer claim. All 41 pages across the three example PDFs were rasterised and inspected via contact sheets; A3 page bounds, banners and text bounds passed. No physical printing was tested.

The browser harness completed nine checks, including a real backend generation triggered from the studio, the resulting exports/model, source preflight, grid interaction, AI choices and a 390px mobile width. No page JavaScript errors were recorded. The controlled test used Chromium under Xvfb/SwiftShader and a loopback fetch binding because managed browser navigation was blocked. It is not native-GPU or unrestricted-browser installation acceptance.

Python compilation, JavaScript syntax and Bash syntax passed. START_HERE links resolve within the package. The exact runtime and dependency notices are in evidence/runtime.json and licenses/LEDGER.json.

## Repairs made during verification

Non-finite input became a structured rejection; duplicate/missing semantic references are rejected before route-graph access; furniture checks treat connected open public zones as a physical union rather than an invented wall. A long circulation hall was shortened, and the upper terrace was made genuinely roof-open across the shared geometry. DXF writer timestamps/GUID metadata were normalised for reproducibility. Report generation no longer mutates a previously validated DAG stage.

## Not accepted

No original legacy repository/tests, native macOS/Windows installers, clean network installation, real-GPU colour test, photoreal still/film, live local/cloud inference, independent IFC viewer, AutoCAD GUI, professional structural design or official NBC/byelaw certification was available or completed. Optional source adapters are marked unverified, not presented as working binaries. The requirement matrix records further functional gaps, including the complete questionnaire, drag-resize designer, unrestricted layouts, image recognition, eldercare accessibility and continuous stair walking.

The actual screenshots are included; no generated-image beautification was substituted for geometry. They document a raster preliminary model, not the requested final photoreal quality bar.
