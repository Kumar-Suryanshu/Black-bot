import os
import sys
import time
import shlex
import docker
import threading
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from .limits import get_limits

@dataclass
class RunResult:
    exit_code: Optional[int]
    timed_out: bool
    oom: bool
    log_path: str
    duration_s: float
    output_dir: str

def probe_gpu() -> dict:
    """Check if the Docker daemon lists an nvidia runtime and can run a test container."""
    if sys.platform == "darwin":
        return {"usable": False, "reason": "GPU mode is not supported on macOS", "count": 0}
        
    try:
        client = docker.from_env()
        info = client.info()
        runtimes = info.get("Runtimes", {})
        if "nvidia" not in runtimes:
            return {"usable": False, "reason": "No nvidia runtime found in Docker daemon", "count": 0}
        
        limits = get_limits()
        device_requests = [docker.types.DeviceRequest(count=limits.gpu_count, capabilities=[["gpu"]])]
        client.containers.run(
            image=limits.gpu_image,
            command="nvidia-smi -L",
            device_requests=device_requests,
            remove=True,
            detach=False
        )
        return {"usable": True, "reason": "GPU probe successful", "count": limits.gpu_count}
    except Exception as e:
        return {"usable": False, "reason": f"GPU probe failed: {str(e)}", "count": 0}

def build_container_spec(project_id: str, workspace: Path, is_setup: bool, command: str) -> dict:
    limits = get_limits()
    wheelhouse = Path("wheelhouse").absolute()
    
    spec = dict(
        image="rerun-base:py311",
        detach=True,
        user="1000:1000",
        network_mode="none",
        read_only=True,
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        pids_limit=limits.pids,
        mem_limit=limits.mem,
        memswap_limit=limits.mem,
        nano_cpus=int(limits.cpus * 1e9),
        tmpfs={"/tmp": "rw,size=256m"},
        working_dir="/workspace",
        environment={
            "HOME": "/tmp",
            "PYTHONPATH": "/workspace/.site",
            "PYTHONHASHSEED": "0",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PIP_NO_CACHE_DIR": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1"
        },
        labels={"rerun": "1", "rerun_project": project_id},
        volumes={
            str(workspace.absolute()): {"bind": "/workspace", "mode": "rw"}
        },
    )
    
    if is_setup:
        spec["volumes"][str(wheelhouse)] = {"bind": "/wheelhouse", "mode": "ro"}
        spec["command"] = ["pip", "install", "--no-index", "--find-links", "/wheelhouse", "--target", "/workspace/.site", "-r", "requirements.txt"]
    else:
        spec["command"] = shlex.split(command)

    if limits.gpu_enabled:
        gpu_info = probe_gpu()
        if gpu_info["usable"]:
            spec["image"] = limits.gpu_image
            spec["device_requests"] = [docker.types.DeviceRequest(count=limits.gpu_count, capabilities=[["gpu"]])]
            
    return spec

def run_container(project_id: str, workspace: Path, is_setup: bool, command: str, kind: str, n: int) -> RunResult:
    limits = get_limits()
    client = docker.from_env()
    
    # 1. Create workspace output dir and log file
    # Note: On Windows (Docker Desktop), permissions are mostly inherited. The prompt advises a+rwX,
    # which we can attempt naively for standard POSIX if running on WSL/Linux, but Windows won't mind it missing.
    try:
        if sys.platform != "win32":
            os.system(f"chmod -R a+rwX {workspace.absolute()}")
    except Exception:
        pass
        
    outputs_dir = workspace / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    try:
        if sys.platform != "win32":
            os.system(f"chmod -R a+rwX {outputs_dir.absolute()}")
    except Exception:
        pass

    log_dir = Path("data") / "runs" / project_id / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{kind}_{n}.log"

    # 2. Build spec and run
    spec = build_container_spec(project_id, workspace, is_setup, command)
    container = client.containers.run(**spec)
    
    start_time = time.time()
    
    def stream_logs():
        written_bytes = 0
        with open(log_path, "wb") as f:
            for chunk in container.logs(stream=True, follow=True):
                if written_bytes < limits.log_cap_bytes:
                    # Write up to cap
                    chunk_to_write = chunk[:limits.log_cap_bytes - written_bytes]
                    f.write(chunk_to_write)
                    written_bytes += len(chunk_to_write)
    
    log_thread = threading.Thread(target=stream_logs)
    log_thread.daemon = True
    log_thread.start()
    
    timeout_s = limits.install_timeout_s if is_setup else limits.run_timeout_s
    
    # 3. Wait
    timed_out = False
    try:
        result = container.wait(timeout=timeout_s)
        exit_code = result.get("StatusCode")
    except Exception as e:
        # requests.exceptions.ReadTimeout, ConnectionError, or docker.errors.APIError wrapping it
        err_str = str(e).lower()
        if "timeout" in err_str or "timed out" in err_str or type(e).__name__ == "ReadTimeout" or type(e).__name__ == "TimeoutError":
            container.kill()
            exit_code = None
            timed_out = True
        else:
            container.kill()
            exit_code = -1
            timed_out = False
    
    log_thread.join(timeout=2.0)
    duration_s = time.time() - start_time
    
    # 4. Check OOM
    try:
        container.reload()
        oom = container.attrs.get("State", {}).get("OOMKilled", False)
    except Exception:
        oom = False
        
    # Harvest outputs
    dest_output_dir = Path("data") / "runs" / project_id / "outputs" / f"run_{n}"
    dest_output_dir.mkdir(parents=True, exist_ok=True)
    # Simple copy over if anything was written
    if outputs_dir.exists():
        import shutil
        for item in outputs_dir.iterdir():
            if item.is_file():
                shutil.copy2(item, dest_output_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, dest_output_dir / item.name, dirs_exist_ok=True)
                
    # 5. Remove container
    try:
        container.remove(force=True)
    except docker.errors.NotFound:
        pass
        
    return RunResult(
        exit_code=exit_code,
        timed_out=timed_out,
        oom=oom,
        log_path=str(log_path),
        duration_s=duration_s,
        output_dir=str(dest_output_dir)
    )

