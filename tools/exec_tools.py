import os
import re
from pathlib import Path
from typing import List

def query_package_index(package_name: str, wheelhouse_dir: str = "wheelhouse") -> List[str]:
    """
    Lists available versions for a given package name in the offline wheelhouse directory.
    Uses PEP 503 normalization.
    """
    wh_path = Path(wheelhouse_dir)
    if not wh_path.exists():
        return []
        
    norm_target = re.sub(r"[-_.]+", "-", package_name).lower()
    versions = []
    
    # Wheel format: {distribution}-{version}(-{build})?-{python}-{abi}-{platform}.whl
    for f in wh_path.iterdir():
        if f.suffix == ".whl":
            parts = f.name.split("-")
            if len(parts) >= 2:
                dist = re.sub(r"[-_.]+", "-", parts[0]).lower()
                if dist == norm_target:
                    ver = parts[1]
                    versions.append(ver)
                    
    return sorted(list(set(versions)))

