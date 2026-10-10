# From experiment to explainer

The production loop is: freeze evidence, write a beat sheet, export data, preview, render, assemble, validate. Keep the narrative independent of the optimizer implementation; a new experiment should need a new adapter and story, not a replacement rendering stack.

## A useful first cut

1. Establish the object being corrected and the coordinate frames.
2. Show the observation and its connection to the state.
3. Explain what the state can change. Use a visibly labeled schematic if that makes the mechanism clearer.
4. Show the recorded experiment with stable camera framing and point identities.
5. Present the controlled comparison and its exact metric definition.
6. Add the next source of evidence, maintaining state continuity if this is a continuation.
7. End with the supported result and the material limitation or tradeoff.

The ACFA example follows this structure: chunk ownership, rigid-state limitation, scale sensitivity, matched GPS comparison, direct reference factors, and shared correction of cameras and surfaces. Its specific conclusion must not become a default conclusion for other datasets.

## Visual language

The default theme uses a dark background, Lato headings, mint correction/state emphasis, gold navigation observations, blue references, and purple diagnostic links. Use consistent semantics throughout the film and explain the colors. Avoid showing every point, edge, or number at once. A fixed point subset is preferable to flickering random resampling.

Keep equations native in Manim and measured geometry in the data renderer. The same measured video can appear by itself and inside the conceptual film. Use a short title, one explanatory sentence, and one takeaway. A silent captioned film must be understandable without narration.

## Preview and troubleshooting

- Missing `pangocairo` or `cairo` during pip installation: install the native development packages in README.md before installing the Manim extra. This is a system dependency, not a Python import-name problem.
- Missing `latex` or `dvisvgm`: install TeX and ensure its executable directory is on PATH. Conda's PATH can hide system tools.
- Missing Chromium executable: run `python -m playwright install chromium` in the same environment as the browser extra, or provide `--browser-executable`.
- WebGL unavailable or black geometry on a headless host: use `--software-gl`, inspect the preview and browser errors, and test a short segment. Preserve the fallback in the reproduction command.
- Browser sandbox unavailable in a controlled container: explicitly supply `--no-sandbox`. Normal desktop use should retain the sandbox.
- RRD unreadable in an older viewer: use Rerun 0.24.1 to match the writer. Version migration needs an explicit read/write test.
- Wrong scale/placement: check a known point through the exported matrix, matrix ordering, units, and the library's translation convention. Do not compensate by silently rescaling the displayed cloud.
- Misleading motion: inspect `*.render.json` and `*.rrd.json` for the exact selected stage indices. Normalized replay time is not optimizer performance.

## Output expectations

Keep MP4, RRD, chapter JSON, input hashes, and verification reports together in an output folder. A source archive should contain code, instructions, fixtures that can be regenerated, and third-party notices. It should not carry flight recordings, maps, browser installations, virtual environments, or old render caches.

The script `scripts/package_release.py` implements an explicit source-file allowlist. Large experiment data can be handed off separately as a copied project folder after checking its intended audience and normal project permissions.
