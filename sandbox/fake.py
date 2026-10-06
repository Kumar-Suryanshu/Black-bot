from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import time

from .manager import RunResult

class FakeSandbox:
    def __init__(self, exit_code: Optional[int] = 0, timed_out: bool = False, oom: bool = False, output_text: str = ""):
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.oom = oom
        self.output_text = output_text
        self.calls = []
        
    def run_container(self, project_id: str, workspace: Path, is_setup: bool, command: str, kind: str, n: int) -> RunResult:
        self.calls.append({
            "project_id": project_id,
            "workspace": workspace,
            "is_setup": is_setup,
            "command": command,
            "kind": kind,
            "n": n
        })
        
        log_dir = Path("data") / "runs" / project_id / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{kind}_{n}.log"
        with open(log_path, "w") as f:
            f.write(self.output_text)
            
        dest_output_dir = Path("data") / "runs" / project_id / "outputs" / f"run_{n}"
        dest_output_dir.mkdir(parents=True, exist_ok=True)
        
        return RunResult(
            exit_code=self.exit_code,
            timed_out=self.timed_out,
            oom=self.oom,
            log_path=str(log_path),
            duration_s=0.1,
            output_dir=str(dest_output_dir)
        )

