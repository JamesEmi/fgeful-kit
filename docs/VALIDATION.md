# Validation record

Validated on Linux with Python 3.11 on 9 October 2026. The machine-readable companion is `validation.json`.

The package was installed in a new isolated virtual environment with all extras. Native Cairo/Pango build files already available on the host were supplied through pkg-config; they were not installed into a global Python environment. The final environment uses the versions in `constraints-tested.txt`, including NumPy 2.0.2, Manim 0.18.1, Rerun 0.24.1, and Playwright 1.63.0. `pip check` reported no broken requirements.

Checks performed:

- Ten automated tests cover matrix storage conventions, known point transformations, rigid versus scale-changing distances, invalid geometry rejection, exact continuation endpoints, sampling ties, dataset relocation, clip normalization, quoted paths, and embedded chapter titles.
- The generated 12-second synthetic data story rendered at 1280×720/12 fps. A native Manim scene rendered at the same settings; assembly produced a 17.667-second film with two chapters. The movies passed FFmpeg full-decode checks.
- Browser previews for the synthetic story and imported 180-second ACFA story passed JavaScript/error and text-overflow checks. Representative synthetic and matched-control frames were visually inspected.
- Three data-dependent ACFA Manim scenes were rendered from the new project path: chunk ownership, measured findings, and direct reference factors. The findings and reference-factor frames were visually inspected; all three movies passed full-decode checks.
- Rerun export and dataframe readback succeeded on both synthetic and real ACFA geometry. The ACFA recording includes the comparison stages, reference images, and a continuous GPS-to-reference replay. This is a recording/schema validation; the native Rerun GUI was not visually inspected in this packaging run.
- A Python wheel was built, including browser templates and licensed font resources. A relocated source archive was exercised independently of the original source directory.

The existing Chromium installation was passed through the documented executable override. Headless captures used the explicit software-rendering and container-sandbox flags. The ordinary Playwright-managed browser installation path is documented but was not separately downloaded for this test.

The full 180-second ACFA data film and all ten ACFA scenes were not rerendered as a new production delivery. The original films remain unchanged; this validation exercises the extraction and the modified data-dependent paths. The Dockerfile, macOS instructions, Windows/WSL instructions, and Python 3.12 support have not been executed here.

These checks establish the tested packaging and rendering behavior, not the scientific validity of a new experiment. Agents must validate their own inputs, claims, and final visual presentation.
