"""Local serving and deterministic browser-frame capture."""
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
import json
import math
import shutil
import subprocess
import tempfile
import threading

from .data import Project, write_json


def prepare_web(root):
    project = Project(root)
    for name in ["story.html", "story.js"]:
        # Preserve an explicitly imported ACFA presentation or a user's own renderer.
        destination = project.root / name
        if not destination.exists():
            destination.write_bytes(files("fgeful_kit").joinpath("web", name).read_bytes())
    for name in ["Lato-Regular.ttf", "Lato-Bold.ttf"]:
        destination = project.assets / name
        if not destination.exists():
            destination.write_bytes(files("fgeful_kit").joinpath("fonts", name).read_bytes())
    (project.assets / "Lato-LICENSE.txt").write_bytes(files("fgeful_kit").joinpath("fonts", "LICENSE.txt").read_bytes())
    return project


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@contextmanager
def serve(root, port=0):
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(QuietHandler, directory=str(Path(root).resolve())))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/story.html"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def capture(root, output, *, start=0., duration=None, fps=24, width=1920, height=1080,
            browser_executable=None, software_gl=False, no_sandbox=False, previews=False):
    from playwright.sync_api import sync_playwright

    project = prepare_web(root)
    duration = project.meta["duration"] - start if duration is None else duration
    if not all(math.isfinite(v) for v in [start, duration, fps]) or start < 0 or duration <= 0 or start + duration > project.meta["duration"] + 1e-6:
        raise ValueError("Capture interval must lie within the story")
    if fps <= 0 or width < 2 or height < 2 or width % 2 or height % 2:
        raise ValueError("Use positive fps and even video dimensions")
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    errors, states, overflows = [], [], []
    args = ["--disable-dev-shm-usage"]
    if software_gl:
        args += ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
    if no_sandbox:
        args.append("--no-sandbox")
    options = {"headless": True, "args": args}
    if browser_executable:
        options["executable_path"] = str(browser_executable)
    with serve(project.root) as url, sync_playwright() as pw:
        browser = pw.chromium.launch(**options)
        try:
            page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(url + "?capture=1", wait_until="networkidle", timeout=90000)
            page.wait_for_function("window.storyReady || window.storyError", timeout=90000)
            if not page.evaluate("window.storyReady"):
                raise RuntimeError(page.evaluate("window.storyError"))
            if previews:
                output.mkdir(parents=True, exist_ok=True)
                times = sorted(set([start, start + duration] + [max(start, min(start + duration, s["start"] + .5)) for s in project.meta["scenes"]]))
                for t in times:
                    states.append(page.evaluate("t => window.render(t)", t))
                    page.screenshot(path=str(output / f"frame_{t:08.3f}.png"), animations="disabled")
                    bad = page.evaluate("""() => [...document.querySelectorAll('h1,#sub,#insight,#provenance')].filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.id)""")
                    overflows.extend({"time": t, "element": e} for e in bad)
                report_path = output / "preview.json"
            else:
                if output.exists():
                    raise FileExistsError(f"Use a new output filename: {output}")
                frame_count = max(1, round(duration * fps))
                temporary = output.with_name(output.stem + ".partial.mp4")
                try:
                    with tempfile.TemporaryFile() as error_log:
                        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "image2pipe", "-vcodec", "mjpeg", "-framerate", str(fps), "-i", "pipe:0", "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(temporary)]
                        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=error_log)
                        try:
                            for i in range(frame_count):
                                t = start + i / fps
                                state = page.evaluate("t => window.render(t)", t)
                                process.stdin.write(page.screenshot(type="jpeg", quality=93, animations="disabled"))
                                if i % max(1, round(fps)) == 0 or i == frame_count - 1:
                                    states.append(state)
                                if i % max(1, round(fps * 5)) == 0:
                                    print(f"Rendered {i}/{frame_count} frames", flush=True)
                            process.stdin.close()
                            if process.wait() != 0:
                                error_log.seek(0)
                                raise RuntimeError(error_log.read().decode(errors="replace"))
                        except BaseException:
                            process.kill()
                            process.wait()
                            raise
                    if errors:
                        raise RuntimeError("Browser errors: " + "; ".join(errors))
                    temporary.replace(output)
                finally:
                    temporary.unlink(missing_ok=True)
                report_path = output.with_suffix(".render.json")
            report = {"project": project.root.name, "start": start, "duration_requested": duration,
                      "fps": fps, "dimensions": [width, height], "states": states,
                      "browser_errors": errors, "overflow": overflows, "geometry_interpolated": False,
                      "inputs": project.report()["sha256"]}
            write_json(report_path, report)
            if errors or overflows:
                raise RuntimeError(f"Review capture validation: {report_path}")
            return report
        finally:
            browser.close()
