#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv()

def run_cmd(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

def setup():
    print("Setting up environment...")
    run_cmd(f"{sys.executable} -m pip install --break-system-packages --user -r requirements-dev.txt")

def images():
    print("Building base Docker image...")
    run_cmd("docker build -t rerun-base:py311 -f sandbox/images/Dockerfile.base sandbox/images")

def hardened_smoke():
    print("Running hardened smoke test...")
    # Container prints 1
    # Write to / fails (read-only root)
    # TCP connect fails (no network)
    # Runs as uid 1000
    cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--read-only",
        "--tmpfs", "/tmp",
        "--user", "1000",
        "rerun-base:py311",
        "sh", "-c",
        'echo 1 && touch /test.txt 2>/dev/null || echo "write failed" && nc -z 8.8.8.8 53 2>/dev/null || echo "network failed" && id -u'
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout.strip().split('\n')
    
    if (len(out) >= 4 and
        out[0] == "1" and
        out[1] == "write failed" and 
        out[2] == "network failed" and
        out[3] == "1000"):
        print("PASS")
    else:
        print("FAIL")
        print(f"Output was: {out}")
        print(f"Stderr was: {res.stderr}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Rerun Developer Scripts")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("setup")
    subparsers.add_parser("images")
    subparsers.add_parser("hardened-smoke")
    
    # stubs for others
    subparsers.add_parser("wheelhouse")
    subparsers.add_parser("test")
    bench_parser = subparsers.add_parser("bench")
    bench_parser.add_argument("--systems", required=True, help="Comma-separated list of systems to evaluate (e.g., B-0,B-2)")
    subparsers.add_parser("demo-check")
    subparsers.add_parser("cleanup")
    subparsers.add_parser("api")
    subparsers.add_parser("ui")
    subparsers.add_parser("selftest")
    subparsers.add_parser("calibrate")
    subparsers.add_parser("papers")
    subparsers.add_parser("seed-faults")
    subparsers.add_parser("adversarial")
    subparsers.add_parser("record")
    subparsers.add_parser("bench-real")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--case", required=True, help="Benchmark case id (b1_control, b2_dependency, b3_silent_config, b4_combined, b5_unable)")
    subparsers.add_parser("build-benchmarks")
    subparsers.add_parser("export-digits")

    args = parser.parse_args()

    if args.command == "setup":
        setup()
    elif args.command == "images":
        images()
    elif args.command == "hardened-smoke":
        hardened_smoke()
    elif args.command == "wheelhouse":
        run_cmd(f"{sys.executable} scripts/make_wheelhouse.py")
    elif args.command == "selftest":
        run_cmd(f"{sys.executable} -m pytest tests/security/test_selftest.py -v")
    elif args.command == "calibrate":
        run_cmd(f"{sys.executable} scripts/calibrate_benchmark.py")
    elif args.command == "seed-faults":
        run_cmd(f"{sys.executable} scripts/seed_faults.py")
    elif args.command == "papers":
        run_cmd(f"{sys.executable} scripts/make_papers.py")
    elif args.command == "test":
        run_cmd(f"{sys.executable} -m pytest tests/unit tests/agent -v")
    elif args.command == "cleanup":
        from sandbox.cleanup import cleanup_orphans
        cleanup_orphans()
    elif args.command == "export-digits":
        run_cmd(f"{sys.executable} scripts/export_digits.py")
    elif args.command == "build-benchmarks":
        print("Building full Stage 4 benchmarks...")
        run_cmd(f"{sys.executable} scripts/export_digits.py")
        run_cmd(f"{sys.executable} scripts/calibrate_benchmark.py")
        run_cmd(f"{sys.executable} scripts/seed_faults.py")
        run_cmd(f"{sys.executable} scripts/make_papers.py")
        print("✅ Benchmarks built successfully!")
    elif args.command == "bench":
        run_cmd(f"{sys.executable} benchmarks/run_bench.py --systems {args.systems}")
    elif args.command == "bench-real":
        run_cmd(f"{sys.executable} scripts/run_real_bench.py")
    elif args.command == "adversarial":
        run_cmd(f"{sys.executable} scripts/run_adversarial.py")
    elif args.command == "run":
        from scripts.run_case import run_case_headless
        run_case_headless(args.case)
    elif args.command == "api":
        run_cmd(f"{sys.executable} -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload")
    elif args.command == "ui":
        run_cmd("npm run dev --prefix frontend")
    else:
        print(f"Command '{args.command}' is not yet implemented fully.")

if __name__ == "__main__":
    main()
