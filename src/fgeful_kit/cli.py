"""Small commands usable by humans and automation; optional stacks import lazily."""
import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .data import Project, write_json


def video_options(parser):
    parser.add_argument("--width", type=int, default=1920)
    parser.add_argument("--height", type=int, default=1080)
    parser.add_argument("--fps", type=int, default=24)


def doctor():
    packages = {}
    for name in ["numpy", "manim", "rerun-sdk", "playwright"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"python": sys.version.split()[0], "packages": packages,
            "commands": {name: shutil.which(name) for name in ["ffmpeg", "ffprobe", "latex", "dvisvgm"]},
            "note": "Browser executables are installed separately: python -m playwright install chromium"}


def render_manim(args):
    scene_file = Path(args.scene_file).resolve()
    output = Path(args.output).resolve()
    if output.exists():
        raise FileExistsError(output)
    if args.width % 2 or args.height % 2 or args.width < 2 or args.height < 2 or args.fps < 1:
        raise ValueError("Use positive fps and even dimensions")
    output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if args.project:
        env["FGEFUL_PROJECT"] = str(Path(args.project).resolve())
    with tempfile.TemporaryDirectory(prefix="fgeful-manim-") as directory:
        command = [args.python, "-m", "manim", "--renderer", "cairo", "--disable_caching", "--format", "mp4",
                   "--fps", str(args.fps), "-r", f"{args.width},{args.height}", "--media_dir", directory,
                   "-o", "scene.mp4", str(scene_file), args.scene]
        subprocess.run(command, check=True, env=env)
        videos = [p for p in Path(directory).rglob("scene.mp4") if "partial_movie_files" not in p.parts]
        if len(videos) != 1:
            raise RuntimeError(f"Expected one Manim movie, found {videos}")
        shutil.copyfile(videos[0], output)
    from .media import verify_video
    return verify_video(output, width=args.width, height=args.height, fps=args.fps)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Portable Manim + recorded-data + Rerun explainers")
    commands = ap.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Report tools and installed optional packages")
    demo = commands.add_parser("demo", help="Create a synthetic data project")
    demo.add_argument("destination")
    validate = commands.add_parser("validate", help="Check project geometry and metadata")
    validate.add_argument("project")
    serve = commands.add_parser("serve", help="Serve an interactive story on loopback")
    serve.add_argument("project")
    serve.add_argument("--port", type=int, default=8770)
    for name in ["render", "preview"]:
        parser = commands.add_parser(name, help="Render a video" if name == "render" else "Render chapter screenshots and check layout")
        parser.add_argument("project")
        parser.add_argument("--output", required=True)
        parser.add_argument("--start", type=float, default=0)
        parser.add_argument("--duration", type=float)
        parser.add_argument("--browser-executable")
        parser.add_argument("--software-gl", action="store_true", help="Use Chromium SwiftShader on machines without a GPU")
        parser.add_argument("--no-sandbox", action="store_true", help="Only for controlled containers that cannot use Chromium's sandbox")
        video_options(parser)
    rr = commands.add_parser("rerun", help="Export and read back an interactive RRD")
    rr.add_argument("project")
    rr.add_argument("--output", required=True)
    rr.add_argument("--steps", type=int, default=101)
    rr.add_argument("--point-stride", type=int, default=1)
    manim = commands.add_parser("manim", help="Render one Manim scene into a predictable filename")
    manim.add_argument("scene_file")
    manim.add_argument("scene")
    manim.add_argument("--project", help="Data project for data-dependent scenes")
    manim.add_argument("--python", default=sys.executable, help="Interpreter with Manim installed")
    manim.add_argument("--output", required=True)
    video_options(manim)
    assembly = commands.add_parser("assemble", help="Normalize clips and embed chapters")
    assembly.add_argument("manifest")
    assembly.add_argument("--output", required=True)
    video_options(assembly)
    verify = commands.add_parser("verify", help="Probe and fully decode an MP4")
    verify.add_argument("video")
    imp = commands.add_parser("import-acfa", help="Copy and normalize a local archived ACFA project")
    imp.add_argument("source")
    imp.add_argument("destination")
    imp.add_argument("--template-dir", default="examples/acfa")
    imp.add_argument("--local-preview")
    args = ap.parse_args(argv)
    try:
        if args.command == "doctor":
            result = doctor()
        elif args.command == "demo":
            from .demo import create_demo
            from .web import prepare_web
            create_demo(args.destination)
            result = prepare_web(args.destination).report()
        elif args.command == "validate":
            result = Project(args.project).report()
        elif args.command == "serve":
            from .web import prepare_web, serve as server
            import threading
            prepare_web(args.project)
            with server(args.project, args.port) as url:
                print(url, flush=True)
                threading.Event().wait()
        elif args.command in ["render", "preview"]:
            from .web import capture
            options = vars(args).copy()
            options.pop("command")
            options["root"] = options.pop("project")
            result = capture(**options, previews=args.command == "preview")
            result = {k: v for k, v in result.items() if k not in ("states", "inputs")}
        elif args.command == "rerun":
            from .rerun_export import export_rrd
            result = export_rrd(args.project, args.output, args.steps, args.point_stride)
            result = {k: v for k, v in result.items() if k not in ("accepted_state_indices", "inputs")}
        elif args.command == "manim":
            result = render_manim(args)
        elif args.command == "assemble":
            from .media import assemble
            result = assemble(args.manifest, args.output, width=args.width, height=args.height, fps=args.fps)
        elif args.command == "verify":
            from .media import verify_video
            result = verify_video(args.video)
        elif args.command == "import-acfa":
            from .acfa import import_acfa
            result = import_acfa(args.source, args.destination, args.template_dir, args.local_preview).report()
        else:
            raise ValueError("Unknown command")
        print(json.dumps(result, indent=2))
    except KeyboardInterrupt:
        return
    except (ValueError, OSError, RuntimeError, ImportError, subprocess.CalledProcessError) as error:
        ap.exit(1, f"fgeful-kit: {error}\n")


if __name__ == "__main__":
    main()
