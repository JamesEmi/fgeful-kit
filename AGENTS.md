# Creating Manim and Rerun-based explainer videos

This repository is a reusable production kit. Preserve its general CLI and data format; place a new experiment's adapter, scenes, and timeline in a new example/project. Run commands from the repository root after installing the appropriate extras. Read README.md and docs/DATA_FORMAT.md first.

## 1. Establish the story and evidence

- Identify the audience, the technical question, the intended conclusion, and the source records. Reuse task context; ask only for information that materially blocks the work.
- Write a brief beat sheet: problem → mechanism → controlled comparison → observed result → boundary or tradeoff. One main idea per scene. A complete film usually mixes schematic explanation and measured clips.
- Inventory input hashes, units, coordinate frames, point ownership, transform conventions, state timelines, and fitted versus evaluation measurements. For every numerical claim, identify a result field or reproducible calculation.
- Label synthetic examples, schematic perturbations, and proposed mechanisms visibly. The supplied demo is scripted teaching geometry, not an optimizer experiment.
- Preserve the actual matched control: same starting geometry, observation identities, losses, camera views and point sampling when making a causal comparison. Report a changed factor set at the transition where it changes.
- Do not equate geometric agreement with surveyed accuracy, training/development fits with held-out evidence, or a custom class name with an unavailable library capability. For the ACFA case, GTSAM can express scale-aware position residuals through stock expressions.

## 2. Export one portable data project

- Use the schema in docs/DATA_FORMAT.md. Keep local points and cameras fixed; record the accepted local-to-world matrices from the actual run. Retain exact source-state indices.
- Use physical transforms `world = linear @ local + translation`; for Sim3, `linear = sR`. Some libraries store an internal translation scaled by `s`; normalize before exporting. Test a known transformed point.
- Both cameras and surfaces owned by a chunk must inherit its same transform in the browser and Rerun trees.
- Write little-endian float32 binaries and JSON, not pickle. Matrices are column-major on disk. Use the NumPy transpose shown in the schema.
- Put dataset assets and generated media in an ignored `output/`, `data/`, or external directory. Use real copied files when handing off a project; no absolute source-path dependencies or symlinks escaping the project.
- Run `fgeful-kit validate PROJECT`. A successful validation does not establish the scientific correctness of the experiment.

## 3. Author and preview the data film

- Start from `fgeful-kit demo output/new-story` or write the schema directly. The default browser renderer takes scene configuration from JSON. An advanced project can supply its own `story.html` and `story.js` implementing `window.storyReady`, `window.storyError`, and async `window.render(seconds)`.
- Keep camera framing stable across comparisons. Use wide views for context, close views for the mechanism, and direct correspondence lines when they explain the observation. Keep sparse overlays legible over dense geometry.
- Render deterministically by time. Map progress to a recorded state with nearest-index sampling. Do not interpolate measured transforms to invent intermediate solver states. Camera motion and schematic animation may be smooth.
- The browser video renders the same underlying geometry as the RRD; it is not a capture of Rerun's application chrome. Describe it accurately in the handoff.
- Run `fgeful-kit preview PROJECT --output output/previews` and inspect the screenshots, especially transition boundaries and comparison layouts. Fix clipped text, tiny plots, empty views, confusing colors, and labels that overlap geometry.
- Render a short segment first: `fgeful-kit render PROJECT --start 0 --duration 2 --width 1280 --height 720 --fps 12 --output output/probe.mp4`. Use `--software-gl` only if needed for headless rendering.

## 4. Create the Manim explanation

- Adapt `examples/minimal/scenes.py`; import `ExplainScene`, `text`, `formula`, and the palette from `fgeful_kit.manim_theme`. The ACFA scenes are fuller examples of graph nodes, factor glyphs, camera ownership, equations, and real-image matches.
- Build the causal mechanism in steps: introduce variables, connect observations to their owners, write the residual, show which state changes, then show the data result. An attractive equation without an explanation of its variables is insufficient.
- Use short headings, one equation or diagram at a time, purposeful highlighting, and enough holding time to read. Keep a consistent 16:9 frame and the shared color semantics. Text and math must fit without shrinking into illegibility.
- Keep all empirical values in the project metadata/result adapter. A scene must not silently inherit another example's metrics, dataset name, sample counts, or contribution claims.
- `MathTex` requires LaTeX and dvisvgm. Check `fgeful-kit doctor`; follow README.md for native prerequisites. Do not replace math with screenshots just to hide a broken installation.
- Render with `fgeful-kit manim SCENE_FILE SCENE_CLASS --project PROJECT --output output/scene.mp4`. The `--project` argument is needed only by scenes that consume data. For a dedicated environment use `--python /path/to/python`.

## 5. Export the interactive Rerun recording

- Run `fgeful-kit rerun PROJECT --output output/experiment.rrd`. Use a fixed `--point-stride` if needed; it must be the same for every state being compared.
- Log local point/camera children under each chunk's `Transform3D`; log world observations in world coordinates. Keep evaluation links distinct from fitted constraints.
- Stage comparisons use normalized replay progress, not solver wall-clock speed. The report records the selected state indices. Declared continuation pipelines must have equal previous-end and next-start geometry.
- Read back the saved RRD. The command does this through Rerun's dataframe reader. Use the matching viewer version when inspecting it; a dataframe load is not a substitute for visual inspection of a new view design.
- If starting from another RRD, inspect that recording's actual schemas and coordinate conventions and write an explicit adapter. There is no universal arbitrary-RRD-to-video command in this package.

## 6. Assemble, verify, and review

- Prefer 1080p, 24 fps, H.264, yuv420p, and fast-start MP4 for the final handoff. Use the same dimensions and fps for all clips. The assembly command normalizes heterogeneous clips when necessary.
- Write a sequence JSON with clip paths, chapter titles, and optional start/end times; run `fgeful-kit assemble SEQUENCE.json --output output/explainer.mp4`. Interleave measured clips where they answer the preceding conceptual scene.
- Assembly intentionally produces a silent captioned film. If narration is requested, implement and validate an explicit audio-mixing stage rather than assuming this tool preserves input audio.
- Run `fgeful-kit verify` on the data film and final film. Check full decode, resolution, frame rate, duration and chapter markers. Inspect representative frames and the transition joins. Review the beginning, middle and end of each unique scene type.
- Confirm that every result sentence agrees with its source, that fixed controls really hold the stated quantities fixed, and that a continuation begins at the previous result. Show material tradeoffs.
- Run `python -m pytest -q` after changes to the reusable code. Add tests for new failure modes or contracts; do not add tests that only repeat implementation details.

## 7. Deliver a usable artifact

- Provide the final MP4s, interactive RRD, chapter map, concise provenance/validation report, and the commands required to reproduce them. Keep the source code and large data deliverables separate.
- When serving a preview remotely, provide a live tested localhost URL and port-forward instructions. Do not claim a server is available without checking it.
- Never embed this machine's home directory, browser cache location, Python environment path, or an assumed port in the reusable code. Browser/interpreter overrides belong in CLI arguments.
- Use `scripts/package_release.py` for a source ZIP. It excludes outputs, private datasets, caches, installed packages and Git history. Inspect the inventory before a requested upload.
- Treat GitHub publication as a separate action unless already authorized. Do not invent a remote URL, choose a code license for the owner, or include research data merely because the code was requested.

## Suggested task prompt for another agent

“Use this repository's AGENTS.md workflow to make a captioned explanation of [question] from [data project]. Produce a data MP4, a Manim-led MP4 with chapters, and an RRD. Establish the evidence and coordinate conventions first, preview a short segment, then render and verify. Label synthetic or illustrative material and report the limitations of the supplied measurements.”
