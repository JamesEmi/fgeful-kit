# fgeful-kit

Turn recorded geometry into a captioned data film, an interactive Rerun recording, and a Manim explanation. This extracts the workflow used for the ACFA chunk-scale and cross-robot mapping videos into a small Python package.

The three outputs share the same data contract:

| Output | Purpose | Engine |
|---|---|---|
| `data.mp4` | Designed, repeatable views of recorded states | WebGL + Playwright + FFmpeg |
| `experiment.rrd` | Inspect points, cameras, constraints, and state histories | Rerun SDK |
| `explainer.mp4` | Explain the mechanism and interleave actual data clips | Manim + FFmpeg chapters |

The data MP4 is a custom presentation of the geometry also logged to Rerun. It does not record the Rerun application's interface. Both paths consume the same points and transforms. The package also works with independent Manim scenes or authored browser stories.

**Agents: start with [AGENTS.md](AGENTS.md).** It contains the complete production procedure, evidence rules, and acceptance checks.

## Quick start

Use Python **3.11** (the tested interpreter). Python 3.12 is allowed by the package but has not been exercised here. Install the native prerequisites below first if using Manim.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[all,test]' -c constraints-tested.txt
python -m playwright install chromium
fgeful-kit doctor
```

On Ubuntu/Debian, the Manim/FFmpeg prerequisites are:

```bash
sudo apt-get update
sudo apt-get install -y build-essential pkg-config python3-dev ffmpeg \
  libcairo2-dev libpango1.0-dev texlive-latex-base texlive-latex-extra \
  texlive-fonts-recommended dvisvgm
python -m playwright install --with-deps chromium
```

On macOS, use Homebrew's `ffmpeg`, `cairo`, `pango`, `pkg-config`, and `mactex-no-gui`; ensure `latex` and `dvisvgm` are on PATH after installing TeX. macOS and Windows have not been validated here; WSL2 or the included Docker image is the recommended Windows route. Native installation details: [Manim](https://docs.manim.community/en/stable/installation/uv.html), [Playwright browsers](https://playwright.dev/python/docs/browsers), [Rerun viewer](https://rerun.io/docs/getting-started/install-rerun/viewer).

Create the bundled synthetic example and produce all three outputs:

```bash
fgeful-kit demo output/demo
fgeful-kit validate output/demo
fgeful-kit preview output/demo --output output/previews
fgeful-kit render output/demo --output output/data.mp4
fgeful-kit rerun output/demo --output output/experiment.rrd
fgeful-kit manim examples/minimal/scenes.py SharedTransform --output output/explanation.mp4
fgeful-kit assemble examples/minimal/sequence.json --output output/explainer.mp4
```

The default is 1920×1080 at 24 fps. For a quick pass, use `--width 1280 --height 720 --fps 12` on `render`, `manim`, and `assemble`. `preview` creates chapter screenshots and checks text overflow. `render` records sampled state indices and input hashes; `verify` fully decodes an MP4. Manim and assembly call that verification automatically. Commands refuse to overwrite completed movies or an existing demo directory; use a new output name for each revision.

```bash
fgeful-kit verify output/data.mp4
fgeful-kit serve output/demo --port 8771
rerun output/experiment.rrd
```

Open the URL printed by `serve`. On a remote server, forward that port using your editor or `ssh -L 8771:127.0.0.1:8771 user@host`; then open `http://localhost:8771/story.html` locally. The built-in server binds only to loopback. Pick another port if one is already in use.

## Choose only the tools you need

| Install extra | Use |
|---|---|
| `pip install -e .` | Data preparation and schema validation; NumPy only |
| `pip install -e '.[browser]'` | Browser preview/capture; install Chromium separately |
| `pip install -e '.[rerun]'` | RRD export and its reader check |
| `pip install -e '.[manim]'` | Manim scenes; native libraries and TeX required |
| `pip install -e '.[test]'` | Unit and media integration tests |

Renderer versions retain the original pipeline: Manim 0.18.1, Rerun SDK 0.24.1, and Playwright 1.63.0. The portable environment uses NumPy 2.0.x to satisfy Rerun's declared dependency; it does not copy the original workspace's manually mixed NumPy installation. Newer versions should be an explicit compatibility change. Use a Rerun viewer matching the SDK version for these recordings.

The renderer finds Playwright's installed Chromium automatically. `--browser-executable /path/to/chromium` supports an existing installation. For headless machines without a usable GPU, add `--software-gl`. `--no-sandbox` is an explicit option for controlled containers where Chromium's sandbox cannot run; it is not the default. Separate Python environments are supported through the CLI's `manim --python` option or by installing each extra in its own environment.

`constraints-tested.txt` records the transitive Python versions used in the validated Linux/Python 3.11 environment. It is optional for other platforms; re-run the checks if changing those versions. It does not install native libraries or browser binaries.

An optional container recipe is included (not built in this validation run):

```bash
docker build -t fgeful-kit .
docker run --rm -v "$PWD:/work" fgeful-kit demo output/container-demo
docker run --rm -v "$PWD:/work" fgeful-kit render output/container-demo \
  --output output/container-data.mp4 --software-gl --no-sandbox
```

## Bring your own experiment

1. Export fixed local geometry and actual recorded transforms into the [data format](docs/DATA_FORMAT.md).
2. Write the timeline in `assets/story.json`. A scene has a title, subtitle, takeaway, one or two panels, and a camera view.
3. Adapt [the minimal Manim scene](examples/minimal/scenes.py), keeping data and schematic claims clearly identified.
4. Run preview and short renders, then export the final MP4/RRD and assemble chapters.

The kit does not run your optimizer, parse arbitrary RRDs into a film, or infer experimental truth. For an existing RRD, write an adapter for that recording's entities and timelines; use its source arrays when available. [WORKFLOW.md](docs/WORKFLOW.md) describes narrative and validation choices.

## Reuse the original ACFA example

[examples/acfa](examples/acfa/README.md) contains the authored browser presentation, ten adapted Manim scenes, and a full chapter assembly script. Import an existing October 3 ACFA delivery:

```bash
fgeful-kit import-acfa /path/to/acfa_scale_ablation_20261003 output/acfa \
  --template-dir examples/acfa --local-preview /path/to/local_chunk.png
fgeful-kit preview output/acfa --output output/acfa-previews
fgeful-kit render output/acfa --output output/acfa-data.mp4
fgeful-kit rerun output/acfa --output output/acfa.rrd --point-stride 5
python examples/acfa/build_film.py --project output/acfa \
  --data-video output/acfa-data.mp4 --output-dir output/acfa-film
```

`--local-preview` is optional. Importing dereferences the original symlinks, copies assets, removes runtime dependence on archived absolute paths, and records input hashes. Flight data, images, optimizer archives, generated videos, and RRDs are **not included in this repository**. The numerical optimizer and research-specific preprocessing remain separate from this presentation kit. The original case study's metrics are example-specific and must not be reused as claims for a different dataset.

## Repository contents

```text
AGENTS.md                  Agent production instructions
src/fgeful_kit/        CLI, data contract, capture, Rerun, assembly, theme
examples/minimal/          Synthetic demo scene and assembly manifest
examples/acfa/             Original case-study presentation and adapted scenes
docs/                     Data contract, workflow, portability and validation notes
tests/                    Geometry, state selection, relocation, and FFmpeg checks
Dockerfile                Optional Linux render environment
scripts/package_release.py  Build a source ZIP with an explicit file allowlist
```

Run `python -m pytest -q` for the automated checks. [Validation notes](docs/VALIDATION.md) distinguish tested paths from platform guidance. `python scripts/package_release.py --output dist/fgeful-kit.zip` creates a source-only archive and a SHA-256 inventory.

For GitHub, use the source folder/ZIP so the agent guide and examples are included. The wheel installs the CLI and library resources. After reviewing the source, publish it to your chosen repository:

```bash
git init -b main
git add .
git commit -m "Add reusable explainer video workflow"
git remote add origin <your-repository-url>
git push -u origin main
```

No external service, account, telemetry service, or CDN is required at render time. Dependencies are downloaded during installation. The source package includes unmodified Lato fonts with their OFL notice in `src/fgeful_kit/fonts/LICENSE.txt`; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). A license for the repository's own code has not been selected by its owner.
