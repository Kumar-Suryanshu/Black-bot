import re

# Appendix A signature library
SIGNATURES = [
    ("gpu_required", "gpu-cuda", r"CUDA error|CUDA is not available|torch\.cuda|Torch not compiled with CUDA|No CUDA GPUs"),
    ("resource_oom", "oom", r"MemoryError"), # Also flag oom=True in runner
    ("dependency_missing", "modnotfound", r"ModuleNotFoundError: No module named '([\w\.]+)'|ImportError: No module named"),
    ("dependency_conflict", "pip-conflict", r"ResolutionImpossible|No matching distribution found|Could not find a version that satisfies|conflicting dependencies"),
    ("network_required", "net", r"Temporary failure in name resolution|Network is unreachable|Connection refused|URLError|ConnectionError|MaxRetryError|Name or service not known"),
    ("sandbox_permission", "perm", r"PermissionError|Read-only file system|\[Errno 13\]|\[Errno 30\]"),
    ("path_error", "fnf", r"FileNotFoundError|No such file or directory"),
    ("config_error", "cfg", r"unrecognized arguments|KeyError: '|yaml\.\w+\.\w*Error"),
    ("numerical_invalid", "nan", r"(?i)\bnan\b|\binf\b")
]

def classify(log_text):
    lines = log_text.splitlines()[-300:]
    text_to_scan = "\n".join(lines)
    
    for err_class, sig_id, pattern in SIGNATURES:
        match = re.search(pattern, text_to_scan)
        if match:
            # find line number roughly
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    return {
                        "error_class": err_class,
                        "signature_id": sig_id,
                        "line_start": len(log_text.splitlines()) - 300 + i + 1,
                        "line_end": len(log_text.splitlines()) - 300 + i + 1
                    }
            return {
                "error_class": err_class,
                "signature_id": sig_id,
                "line_start": None,
                "line_end": None
            }
            
    return {
        "error_class": "unknown",
        "signature_id": "unknown",
        "line_start": None,
        "line_end": None
    }
