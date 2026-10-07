import threading
import logging
from agent.loop import run_project
from backend.app.db import get_project_state, save_project_state

logger = logging.getLogger(__name__)

def run_project_thread(project_id: str):
    """
    Background worker that runs the synchronous `run_project` loop.
    It returns when `state.pending` is set or when phase is "DONE".
    """
    logger.info(f"Starting worker for project {project_id}")
    state = get_project_state("data/rerun.db", project_id)
    if not state:
        logger.error(f"Project {project_id} not found.")
        return
        
    try:
        run_project(state, deps={})
    except Exception as e:
        logger.exception(f"Exception in worker for project {project_id}: {e}")
        state.phase = "DONE"
        state.final = {"status": "INCONCLUSIVE", "reason": f"internal error: {str(e)}"}
        
    # Save state back after loop returns
    # The status column is updated for convenience
    status = state.final.get("status") if state.final else state.phase
    save_project_state("data/rerun.db", project_id, state.benchmark_id, state.repo_commit, status, state)
    logger.info(f"Worker for project {project_id} finished. Phase: {state.phase}, Pending: {state.pending}")

def start_project_worker(project_id: str):
    """Starts the synchronous orchestrator in a background thread."""
    t = threading.Thread(target=run_project_thread, args=(project_id,), daemon=True)
    t.start()

