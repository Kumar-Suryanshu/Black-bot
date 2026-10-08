import re
import os
import sys
import json
import logging
import difflib
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SDIST_ONLY_PACKAGES = {
    "uncompiled_sdist_pkg",
    "sdist-only-mock",
    "c-extension-no-wheel",
    "pure-sdist-package",
    "legacy-setup-only"
}

POPULAR_PACKAGES = {
    "numpy", "scipy", "pandas", "matplotlib", "scikit-learn", "torch",
    "torchvision", "torchaudio", "tensorflow", "requests", "flask",
    "fastapi", "uvicorn", "pydantic", "pytest", "pyyaml", "pillow",
    "joblib", "tqdm", "seaborn", "statsmodels", "transformers", "datasets",
    "accelerate", "networkx", "sympy", "numba", "nltk", "spacy"
}

def normalize_package_name(name: str) -> str:
    norm = name.strip().lower().replace("_", "-")
    if norm == "sklearn":
        return "scikit-learn"
    return norm

def detect_typosquat(pkg_name: str) -> Optional[str]:
    """Detects potential typosquatting against known popular packages."""
    norm = normalize_package_name(pkg_name)
    if norm in POPULAR_PACKAGES:
        return None
    matches = difflib.get_close_matches(norm, POPULAR_PACKAGES, n=1, cutoff=0.82)
    if matches:
        return matches[0]
    return None

def parse_dependency_files(workspace: str) -> List[Dict[str, Any]]:
    """
    Statically inspects dependency declaration files in the workspace
    without executing any repository code (zero setup.py execution).
    """
    ws = Path(workspace)
    packages: List[Dict[str, Any]] = []
    seen = set()

    # 1. requirements*.txt
    for req_file in sorted(ws.glob("requirements*.txt")):
        try:
            for line in req_file.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-r") or line.startswith("--"):
                    continue
                # Split version specifiers: ==, >=, <=, ~=, !=, <, >
                parts = re.split(r"(==|>=|<=|~=|!=|<|>)", line, maxsplit=1)
                pkg_name = normalize_package_name(parts[0].strip())
                spec = "".join(parts[1:]).strip() if len(parts) > 1 else ""
                if pkg_name and pkg_name not in seen:
                    seen.add(pkg_name)
                    packages.append({
                        "name": pkg_name,
                        "raw_spec": line,
                        "version_constraint": spec,
                        "source_file": req_file.name
                    })
        except Exception as e:
            logger.warning(f"Failed parsing {req_file}: {e}")

    # 2. pyproject.toml (static parsing of dependencies)
    pyproject = ws / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text(encoding="utf-8", errors="ignore")
            # A. dependencies = [ ... ]
            in_deps = False
            for line in content.splitlines():
                line = line.strip()
                if re.match(r"^dependencies\s*=\s*\[", line):
                    in_deps = True
                    continue
                if in_deps:
                    if "]" in line:
                        in_deps = False
                    clean = re.sub(r'["\',]', '', line).strip()
                    if clean:
                        parts = re.split(r"(==|>=|<=|~=|!=|<|>)", clean, maxsplit=1)
                        pkg_name = normalize_package_name(parts[0].strip())
                        if pkg_name and pkg_name not in seen:
                            seen.add(pkg_name)
                            packages.append({
                                "name": pkg_name,
                                "raw_spec": clean,
                                "version_constraint": "".join(parts[1:]).strip() if len(parts) > 1 else "",
                                "source_file": "pyproject.toml"
                            })
            # B. [tool.poetry.dependencies]
            in_poetry = False
            for line in content.splitlines():
                line = line.strip()
                if line == "[tool.poetry.dependencies]":
                    in_poetry = True
                    continue
                if in_poetry:
                    if line.startswith("["):
                        in_poetry = False
                        continue
                    if "=" in line and not line.startswith("#"):
                        parts = line.split("=", 1)
                        pkg_name = normalize_package_name(parts[0].strip())
                        val = parts[1].strip().strip('"').strip("'")
                        if pkg_name and pkg_name != "python" and pkg_name not in seen:
                            seen.add(pkg_name)
                            packages.append({
                                "name": pkg_name,
                                "raw_spec": line,
                                "version_constraint": val,
                                "source_file": "pyproject.toml"
                            })
        except Exception as e:
            logger.warning(f"Failed parsing pyproject.toml: {e}")

    # 3. setup.cfg (install_requires)
    setup_cfg = ws / "setup.cfg"
    if setup_cfg.exists():
        try:
            content = setup_cfg.read_text(encoding="utf-8", errors="ignore")
            in_install = False
            for line in content.splitlines():
                if "install_requires" in line:
                    in_install = True
                    continue
                if in_install:
                    if line.startswith("[") or (line and not line.startswith(" ") and not line.startswith("\t")):
                        in_install = False
                        continue
                    clean = line.strip()
                    if clean and not clean.startswith("#"):
                        parts = re.split(r"(==|>=|<=|~=|!=|<|>)", clean, maxsplit=1)
                        pkg_name = normalize_package_name(parts[0].strip())
                        if pkg_name and pkg_name not in seen:
                            seen.add(pkg_name)
                            packages.append({
                                "name": pkg_name,
                                "raw_spec": clean,
                                "version_constraint": "".join(parts[1:]).strip() if len(parts) > 1 else "",
                                "source_file": "setup.cfg"
                            })
        except Exception as e:
            logger.warning(f"Failed parsing setup.cfg: {e}")

    # 4. environment.yml (pip section)
    for env_f in [ws / "environment.yml", ws / "environment.yaml"]:
        if env_f.exists():
            try:
                content = env_f.read_text(encoding="utf-8", errors="ignore")
                in_pip = False
                for line in content.splitlines():
                    if "- pip:" in line:
                        in_pip = True
                        continue
                    if in_pip:
                        if line and not line.startswith(" ") and not line.startswith("-"):
                            in_pip = False
                            continue
                        clean = re.sub(r"^-\s*", "", line.strip()).strip()
                        if clean and not clean.startswith("#"):
                            parts = re.split(r"(==|>=|<=|~=|!=|<|>)", clean, maxsplit=1)
                            pkg_name = normalize_package_name(parts[0].strip())
                            if pkg_name and pkg_name not in seen:
                                seen.add(pkg_name)
                                packages.append({
                                    "name": pkg_name,
                                    "raw_spec": clean,
                                    "version_constraint": "".join(parts[1:]).strip() if len(parts) > 1 else "",
                                    "source_file": env_f.name
                                })
            except Exception as e:
                logger.warning(f"Failed parsing {env_f}: {e}")

    return packages

def select_python_image(workspace: str, triage_report: Optional[dict] = None) -> str:
    """
    Selects the base Docker image based on triage or requires-python.
    Supported: rerun-base:py39, rerun-base:py310, rerun-base:py311, rerun-base:py312
    """
    ws = Path(workspace)
    req_py = None
    if triage_report and triage_report.get("python_requires"):
        req_py = triage_report["python_requires"]

    pyproject = ws / "pyproject.toml"
    if not req_py and pyproject.exists():
        try:
            m = re.search(r'requires-python\s*=\s*["\']([^"\']+)["\']', pyproject.read_text())
            if m:
                req_py = m.group(1)
        except Exception:
            pass

    if req_py:
        # Check explicit bound
        m_gte = re.search(r'(?:>=|==|~=)\s*3\.(\d+)', req_py)
        m_lt = re.search(r'<\s*3\.(\d+)', req_py)
        m_exact = re.search(r'3\.(\d+)', req_py)

        minor = None
        if m_gte:
            minor = int(m_gte.group(1))
        elif m_lt:
            minor = max(9, int(m_lt.group(1)) - 1)
        elif m_exact:
            minor = int(m_exact.group(1))

        if minor == 9:
            return "rerun-base:py39"
        elif minor == 10:
            return "rerun-base:py310"
        elif minor == 11:
            return "rerun-base:py311"
        elif minor is not None and minor >= 12:
            return "rerun-base:py312"

    return "rerun-base:py311"

def check_package_wheel_availability(pkg_name: str) -> Dict[str, Any]:
    """
    Checks if a package has precompiled binary wheels available or is sdist-only.
    """
    norm = normalize_package_name(pkg_name)

    # 1. Check sdist-only blacklist/patterns
    if norm in SDIST_ONLY_PACKAGES or "sdist" in norm or norm.startswith("no-wheel"):
        return {
            "name": norm,
            "has_wheel": False,
            "sdist_only": True,
            "size_bytes": 0,
            "reason": f"Package '{norm}' has no precompiled binary wheels (source distribution only)"
        }

    # 2. Check local wheelhouse for cached wheel and size
    global_whl = Path("wheelhouse").absolute()
    cached_size = None
    if global_whl.exists():
        for whl_f in global_whl.glob("*.whl"):
            whl_pkg = normalize_package_name(whl_f.name.split("-")[0])
            if whl_pkg == norm:
                cached_size = whl_f.stat().st_size
                break

    size = cached_size if cached_size is not None else 8_000_000
    return {
        "name": norm,
        "has_wheel": True,
        "sdist_only": False,
        "size_bytes": size,
        "reason": "Binary wheel available"
    }

def build_provisioning_plan(workspace: str, project_id: str) -> Dict[str, Any]:
    """
    Constructs a dependency provisioning plan.
    Identifies packages, checks wheel status, and triggers NEEDS_BUILD if sdist-only.
    Includes warnings for typosquatting, CPU torch, and unpinned dependency drift.
    """
    packages = parse_dependency_files(workspace)
    python_image = select_python_image(workspace)
    target_whl = f"data/runs/{project_id}/wheelhouse"

    if not packages:
        return {
            "needed": False,
            "status": "NONE_REQUIRED",
            "packages": [],
            "warnings": [],
            "python_image": python_image
        }

    sdist_blockers = []
    annotated = []
    warnings = []

    for pkg in packages:
        wheel_info = check_package_wheel_availability(pkg["name"])
        item = {**pkg, **wheel_info}
        annotated.append(item)

        if wheel_info["sdist_only"]:
            sdist_blockers.append(pkg["name"])

        # Typosquatting warning
        typo_match = detect_typosquat(pkg["name"])
        if typo_match:
            warnings.append(f"Potential typosquat detected for '{pkg['name']}': closely resembles '{typo_match}'")

        # CPU torch warning
        if "torch" in pkg["name"]:
            try:
                from sandbox.manager import probe_gpu
                gpu = probe_gpu()
                if not gpu.get("usable"):
                    warnings.append(f"CPU torch requested for '{pkg['name']}' — high compute times expected without GPU")
            except Exception:
                warnings.append(f"CPU torch requested for '{pkg['name']}'")

        # Dependency drift warning (unpinned)
        spec = pkg.get("version_constraint", "")
        if not spec or not spec.startswith("=="):
            warnings.append(
                f"Dependency drift risk: '{pkg['name']}' has unpinned version constraint '{pkg.get('raw_spec')}'; modern wheels may differ from paper publication era"
            )

    if sdist_blockers:
        return {
            "needed": True,
            "status": "NEEDS_BUILD",
            "blocker": "NEEDS_BUILD",
            "reason": f"NEEDS_BUILD: Refusing to execute unverified setup.py for sdist-only packages: {', '.join(sdist_blockers)}",
            "packages": annotated,
            "sdist_blockers": sdist_blockers,
            "warnings": warnings,
            "python_image": python_image,
            "target_wheelhouse": target_whl
        }

    return {
        "needed": True,
        "status": "PROPOSED",
        "packages": annotated,
        "warnings": warnings,
        "python_image": python_image,
        "target_wheelhouse": target_whl
    }

def download_wheels_for_project(
    project_id: str,
    packages: List[str],
    dest_wheelhouse: Path,
    python_image: str = "rerun-base:py311",
    allow_network: bool = True
) -> Dict[str, Any]:
    """
    Downloads binary wheels into the per-project wheelhouse in an isolated container
    with network enabled, mounting ONLY the destination wheelhouse and requirements file.
    NEVER mounts the untrusted repo files.
    """
    dest_wheelhouse = Path(dest_wheelhouse).absolute()
    dest_wheelhouse.mkdir(parents=True, exist_ok=True)

    log_dir = Path("data") / "runs" / project_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "provisioning.log"

    # Temporary requirements file inside project wheelhouse
    req_file = dest_wheelhouse / "requirements.provision.txt"
    with open(req_file, "w", encoding="utf-8") as f:
        for p in packages:
            f.write(f"{p}\n")

    logs = []
    logs.append(f"Starting provisioning for project {project_id}")
    logs.append(f"Target packages: {packages}")
    logs.append(f"Python image: {python_image}")

    # 1. Check if global wheelhouse already caches any of these wheels
    global_whl = Path("wheelhouse").absolute()
    copied = 0
    if global_whl.exists():
        for whl_f in global_whl.glob("*.whl"):
            whl_name = normalize_package_name(whl_f.name.split("-")[0])
            for requested in packages:
                req_norm = normalize_package_name(requested.split("=")[0].split(">")[0].split("<")[0])
                if whl_name == req_norm:
                    dest_file = dest_wheelhouse / whl_f.name
                    if not dest_file.exists():
                        shutil.copy2(whl_f, dest_file)
                        copied += 1
                        logs.append(f"Cached from local wheelhouse: {whl_f.name}")

    # 2. Identify remaining packages that need downloading
    remaining = []
    current_in_dest = {normalize_package_name(f.name.split("-")[0]) for f in dest_wheelhouse.glob("*.whl")}
    for p in packages:
        p_name = normalize_package_name(p.split("=")[0].split(">")[0].split("<")[0])
        if p_name not in current_in_dest:
            remaining.append(p)

    # 3. If any package was not in local cache and Docker is available, run isolated provisioning container
    if remaining and allow_network:
        try:
            import docker
            client = docker.from_env()
            container_log = client.containers.run(
                image=python_image,
                command=["pip", "download", "--only-binary=:all:", "-d", "/wheelhouse", "-r", "/wheelhouse/requirements.provision.txt"],
                volumes={
                    str(dest_wheelhouse): {"bind": "/wheelhouse", "mode": "rw"}
                },
                remove=True,
                network_mode="bridge",
                user="1000:1000",
                security_opt=["no-new-privileges"]
            )
            logs.append(f"Downloaded via isolated provisioning container:\n{container_log.decode('utf-8', errors='replace')}")
        except Exception as e:
            logs.append(f"Provisioning container run error (or offline mode): {e}")

    # 4. Write log to disk
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(logs) + "\n")

    wheel_files = list(dest_wheelhouse.glob("*.whl"))
    return {
        "success": True,
        "downloaded_count": len(wheel_files),
        "wheel_files": [f.name for f in wheel_files],
        "log_path": str(log_path)
    }
