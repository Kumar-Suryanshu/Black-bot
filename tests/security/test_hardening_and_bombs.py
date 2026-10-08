import os
import json
import pytest
from pathlib import Path
import docker

from sandbox.manager import build_container_spec, run_container, get_limits

def is_docker_available():
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False

def test_container_spec_hardening_attributes(tmp_path):
    """
    Gate: Verify container specification strictly adheres to defense-in-depth:
    - network_mode="none" (offline)
    - user="1000:1000" (non-root)
    - read_only=True (immutable root filesystem)
    - cap_drop=["ALL"] (all Linux capabilities dropped)
    - security_opt=["no-new-privileges"]
    - no privileged mode
    - tmpfs capped (/tmp 256m)
    - strictly isolated volume bindings
    """
    ws = tmp_path / "workspace"
    ws.mkdir()
    
    spec = build_container_spec("proj_sec_spec", ws, is_setup=False, command="python test.py")
    
    assert spec["network_mode"] == "none", "Network must be disabled ('none')"
    assert spec["user"] == "1000:1000", "User must be non-root (1000:1000)"
    assert spec["read_only"] is True, "Root filesystem must be read-only"
    assert "ALL" in spec["cap_drop"], "All capabilities must be dropped"
    assert "no-new-privileges" in spec["security_opt"], "no-new-privileges must be enforced"
    assert spec.get("privileged", False) is False, "Privileged containers are strictly forbidden"
    assert "/tmp" in spec["tmpfs"], "tmpfs must be configured for temporary scratch space"
    
    # Check volume mounts: only the workspace should be bound
    volumes = spec["volumes"]
    for host_path, mount_cfg in volumes.items():
        assert "/workspace" in mount_cfg["bind"] or "/wheelhouse" in mount_cfg["bind"]
        # Ensure no sensitive host files are mounted
        assert "/var/run/docker.sock" not in host_path
        assert "/etc" not in host_path
        assert "/root" not in host_path

@pytest.mark.skipif(not is_docker_available(), reason="Docker is not available")
def test_container_disk_bomb_contained(tmp_path):
    """
    Gate: Host disk is protected. Attempt to fill /tmp beyond tmpfs cap (256MB)
    fails with ENOSPC (No space left on device) while host remains completely unharmed.
    """
    ws = tmp_path / "disk_bomb_repo"
    ws.mkdir()
    
    # Python script attempting to write 400MB to /tmp (tmpfs is 256MB)
    bomb_script = ws / "fill_tmp.py"
    bomb_script.write_text(
        "import os\n"
        "try:\n"
        "    with open('/tmp/bomb.bin', 'wb') as f:\n"
        "        for _ in range(400):\n"
        "            f.write(b'\\x00' * (1024 * 1024))\n"
        "    print('FAIL_ALLOWED')\n"
        "except OSError as e:\n"
        "    print(f'CAUGHT_ENOSPC: {e}')\n"
    )
    
    res = run_container(
        project_id="selftest_disk_bomb",
        workspace=ws,
        is_setup=False,
        command="python fill_tmp.py",
        kind="run",
        n=1
    )
    
    log_content = Path(res.log_path).read_text()
    assert "CAUGHT_ENOSPC" in log_content or "No space left on device" in log_content or res.exit_code != 0
    assert "FAIL_ALLOWED" not in log_content
    # Assert host tmp is clean
    assert not os.path.exists("/tmp/bomb.bin")
