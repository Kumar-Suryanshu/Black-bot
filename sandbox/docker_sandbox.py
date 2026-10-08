from pathlib import Path
from typing import Tuple, Optional
from agent.state import ProjectState
from sandbox.manager import run_container, RunResult

class DockerSandbox:
    """Real Docker sandbox adapter implementing the orchestrator execution interface."""

    def execute(self, state: ProjectState, workspace: str, command: str, kind: str, n: int) -> RunResult:
        """Run an experiment execution container (isolated, offline, CPU/mem/PID capped)."""
        ws = Path(workspace)
        return run_container(
            project_id=state.project_id,
            workspace=ws,
            is_setup=False,
            command=command,
            kind=kind,
            n=n
        )

    def install(self, state: ProjectState, workspace: str, n: int = 1) -> Tuple[Optional[int], str, RunResult]:
        """Run a setup container mounting the offline wheelhouse to install dependencies."""
        ws = Path(workspace)
        req_file = ws / "requirements.txt"
        if not req_file.exists():
            dummy = RunResult(
                exit_code=0,
                timed_out=False,
                oom=False,
                log_path="",
                duration_s=0.0,
                output_dir=""
            )
            return 0, "", dummy

        res = run_container(
            project_id=state.project_id,
            workspace=ws,
            is_setup=True,
            command="",
            kind="setup",
            n=n
        )
        return res.exit_code, res.log_path, res
