"""One-shot setup + self-test. Run from the project root (setup.bat does this).

Writes a full report to logs/setup.log so problems can be diagnosed.
"""
import os
import platform
import subprocess
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "setup.log"


def log(msg: str) -> None:
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")


def step(name, fn):
    log(f"\n=== {name} ===")
    try:
        fn()
        log(f"[OK] {name}")
        return True
    except Exception:
        log(f"[FAIL] {name}\n{traceback.format_exc()}")
        return False


def run(cmd):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # Windows consoles can't print some Unicode
    p = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    log(p.stdout[-6000:])
    if p.stderr.strip():
        log("STDERR:\n" + p.stderr[-6000:])
    if p.returncode != 0:
        raise RuntimeError(f"exit code {p.returncode}: {' '.join(cmd)}")


def main():
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text("", encoding="utf-8")
    log(f"Python {sys.version} on {platform.platform()}")
    log(f"Executable: {sys.executable}")

    def ensure_pip():
        try:
            import pip  # noqa: F401
            log("pip already available")
        except ImportError:
            run([sys.executable, "-m", "ensurepip", "--upgrade"])

    if not step("ensure pip", ensure_pip):
        return
    ok = step("pip install", lambda: run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", "requirements.txt"]))
    if not ok:
        return
    step("import app modules", lambda: run([sys.executable, "-c", "import app.main; print('imports fine')"]))
    step("build index (python -m app.ingest)", lambda: run([sys.executable, "-m", "app.ingest"]))
    step("retrieval evaluation (about mode)", lambda: run([sys.executable, "-m", "eval.run_eval"]))
    step("retrieval evaluation (astrologer mode)", lambda: run([sys.executable, "-m", "eval.run_eval", "--mode", "astro"]))
    step("agent smoke test (needs GROQ_API_KEY in .env)", lambda: run([sys.executable, "scripts/smoke_test.py"]))
    log("\nSETUP FINISHED")


if __name__ == "__main__":
    main()
