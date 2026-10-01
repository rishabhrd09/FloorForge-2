# Reported wall junction — 2026-09-29

The reported Ground guide is reconstructed from the screenshots, with the displayed plot/setback dimensions and blank First/Second boards matching the reported missing-bedroom diagnostics. This is a test fixture, not the user's complete saved project, and no browser autosave was replaced.

Previously, Bedroom 2's right wall from (4346, 5794) to (4346, 11513) mm was treated as one wall. Its midpoint fell at the boundary between the veranda and courtyard (y = 8654 mm), causing all three spaces to be counted as owners. The compiler now splits at that boundary and assigns each segment its own pair of neighbours. Room polygons are unchanged.

The Ground fixture now passes wall compilation. It still requires wider bedrooms, an entrance, windows and connected access. The three-floor fixture reports both empty upper floors. A stair landing does not supply a staircase. These checks remain enforced.

`valid-outdoor-junction.floorforge.json` is a small, separate compiler fixture that passes validation and generation. It demonstrates a living room with a veranda door and courtyard window; it is not a full residential programme. Its 3D screenshot is actual Chromium/SwiftShader output. The browser acceptance record also covers the fixed guide, conversion, mode preservation, exact metric inputs, and stale-design handling on failure.
