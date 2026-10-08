import os
import re
import csv
import json
import math
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from agent.state import Claim, ProjectState, MetricExtraction

logger = logging.getLogger(__name__)

class MetricExtractionResult:
    def __init__(
        self,
        success: bool,
        value: Optional[float] = None,
        std: Optional[float] = None,
        per_seed: Optional[List[float]] = None,
        error: Optional[str] = None,
        source_file: Optional[str] = None,
        line_number: Optional[int] = None,
        excerpt: Optional[str] = None,
        evidence_id: Optional[str] = None
    ):
        self.success = success
        self.value = value
        self.std = std
        self.per_seed = per_seed
        self.error = error
        self.source_file = source_file
        self.line_number = line_number
        self.excerpt = excerpt
        self.evidence_id = evidence_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "value": self.value,
            "std": self.std,
            "per_seed": self.per_seed,
            "error": self.error,
            "source_file": self.source_file,
            "line_number": self.line_number,
            "excerpt": self.excerpt,
            "evidence_id": self.evidence_id
        }

def _parse_numeric(raw_val: Any, reported_hint: Optional[float] = None) -> Optional[float]:
    """Helper to convert strings/numbers into float, handling percentages."""
    if raw_val is None:
        return None
    if isinstance(raw_val, (int, float)):
        return float(raw_val)
    if not isinstance(raw_val, str):
        return None

    cleaned = raw_val.strip()
    is_percent = cleaned.endswith("%")
    if is_percent:
        cleaned = cleaned[:-1].strip()

    try:
        val = float(cleaned)
        if is_percent:
            # If percentage e.g. 93.1%, convert to 0.931 if reported is ~0.931
            if reported_hint is not None and reported_hint <= 1.0 and val > 1.0:
                val = val / 100.0
            elif reported_hint is None and val > 1.0:
                val = val / 100.0
        return val
    except (ValueError, TypeError):
        return None

def extract_metric(
    workspace: Path | str,
    claim: Claim,
    log_path: Optional[str] = None,
    plan: Optional[Any] = None
) -> MetricExtractionResult:
    """
    Extracts metric value for a claim from experiment outputs or logs (R4).
    Extraction order:
      1. Explicit claim.metric_extraction configuration (if present)
      2. outputs/results.json convention (path + result_key / claim.metric)
      3. Candidate result files in workspace (*.csv, *.json)
      4. Regex over attempt log
    Returns MetricExtractionResult. NEVER defaults to 0 on failure.
    """
    ws = Path(workspace)
    cfg: Optional[MetricExtraction] = getattr(claim, "metric_extraction", None)

    # ---------------------------------------------------------
    # Case A: Explicit MetricExtraction configured
    # ---------------------------------------------------------
    if cfg:
        kind = cfg.kind
        target_path_str = cfg.path

        # 1. Regex over Log
        if kind == "regex_log":
            target_log = Path(target_path_str) if target_path_str else (Path(log_path) if log_path else None)
            if not target_log or not target_log.exists():
                return MetricExtractionResult(
                    success=False,
                    error=f"Log file not found for regex extraction: {target_log}"
                )
            regex_pat = cfg.regex or rf"(?i){re.escape(claim.metric)}\s*[:=]\s*(?P<val>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?%?)"
            return _extract_from_regex(target_log, regex_pat, claim.reported)

        # 2. CSV File
        elif kind == "csv_file":
            rel_path = target_path_str or "metrics.csv"
            csv_path = ws / rel_path if not os.path.isabs(rel_path) else Path(rel_path)
            col_name = cfg.column or cfg.key or claim.metric
            return _extract_from_csv(csv_path, col_name, cfg.aggregation, claim.reported)

        # 3. JSON File
        elif kind in ("json_file", "results_json"):
            rel_path = target_path_str or (plan.output_file if plan and plan.output_file else "outputs/results.json")
            json_path = ws / rel_path if not os.path.isabs(rel_path) else Path(rel_path)
            key_name = cfg.key or claim.result_key or claim.metric or claim.id
            return _extract_from_json(json_path, key_name, cfg.aggregation, plan, claim.reported)

        # 4. Text File
        elif kind == "txt_file":
            rel_path = target_path_str or "output.txt"
            txt_path = ws / rel_path if not os.path.isabs(rel_path) else Path(rel_path)
            if not txt_path.exists():
                return MetricExtractionResult(success=False, error=f"Text file '{rel_path}' not found")
            if cfg.regex:
                return _extract_from_regex(txt_path, cfg.regex, claim.reported)
            else:
                raw_text = txt_path.read_text(encoding="utf-8", errors="ignore").strip()
                val = _parse_numeric(raw_text, claim.reported)
                if val is not None:
                    return MetricExtractionResult(
                        success=True,
                        value=val,
                        source_file=str(txt_path),
                        line_number=1,
                        excerpt=raw_text[:200]
                    )
                return MetricExtractionResult(success=False, error=f"Could not parse numeric metric from {txt_path}")

    # ---------------------------------------------------------
    # Case B: Auto-Discovery Pipeline
    # ---------------------------------------------------------
    # 1. Try results.json (convention)
    default_json = ws / "outputs" / "results.json"
    if default_json.exists():
        candidate_keys = [
            claim.result_key,
            claim.metric,
            claim.id,
            f"{claim.metric}_mean",
            "test_accuracy_mean",  # benchmark compatibility
            "accuracy",
            "score",
            "metric"
        ]
        candidate_keys = [k for k in candidate_keys if k]
        for k in candidate_keys:
            res = _extract_from_json(default_json, k, "last", plan, claim.reported)
            if res.success:
                return res

    # 2. Try candidate CSV files in workspace
    for csv_candidate in [ws / "metrics.csv", ws / "outputs" / "metrics.csv", ws / "results.csv"]:
        if csv_candidate.exists():
            res = _extract_from_csv(csv_candidate, claim.metric, "last", claim.reported)
            if res.success:
                return res

    # 3. Try candidate JSON files in workspace
    for json_candidate in [ws / "eval.json", ws / "results.json", ws / "outputs" / "eval.json"]:
        if json_candidate.exists():
            res = _extract_from_json(json_candidate, claim.metric, "last", plan, claim.reported)
            if res.success:
                return res

    # 4. Try Regex over log
    if log_path and os.path.exists(log_path):
        # Specific metric pattern
        pat1 = rf"(?i){re.escape(claim.metric)}\s*[:=]\s*(?P<val>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?%?)"
        res1 = _extract_from_regex(Path(log_path), pat1, claim.reported)
        if res1.success:
            return res1

        # Common headline pattern e.g. "Accuracy: 93.1%"
        pat2 = r"(?i)Accuracy\s*[:=]\s*(?P<val>[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?%?)"
        res2 = _extract_from_regex(Path(log_path), pat2, claim.reported)
        if res2.success:
            return res2

    return MetricExtractionResult(
        success=False,
        error=f"Metric extraction failed: unable to extract '{claim.metric}' ({claim.id}) from outputs or logs"
    )

def _extract_from_json(
    json_path: Path,
    key_name: str,
    aggregation: str,
    plan: Optional[Any],
    reported_hint: Optional[float]
) -> MetricExtractionResult:
    if not json_path.exists():
        return MetricExtractionResult(success=False, error=f"JSON result file not found: {json_path}")
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as e:
        return MetricExtractionResult(success=False, error=f"Invalid JSON in {json_path}: {e}")

    # Support nested dot notation: e.g. "eval.accuracy"
    val = data
    for part in key_name.split("."):
        if isinstance(val, dict) and part in val:
            val = val[part]
        else:
            val = None
            break

    if val is None:
        return MetricExtractionResult(success=False, error=f"Key '{key_name}' not found in {json_path}")

    # Extract per-seed and std if present
    per_seed_key = key_name.replace("_mean", "_per_seed") if "_mean" in key_name else f"{key_name}_per_seed"
    std_key = key_name.replace("_mean", "_std") if "_mean" in key_name else f"{key_name}_std"
    per_seed_vals = data.get(per_seed_key) if isinstance(data, dict) else None
    std_val = data.get(std_key) if isinstance(data, dict) else None

    # Handle aggregation if val is a list
    if isinstance(val, list):
        if not val:
            return MetricExtractionResult(success=False, error=f"List for '{key_name}' is empty")
        nums = [_parse_numeric(x, reported_hint) for x in val if _parse_numeric(x, reported_hint) is not None]
        if not nums:
            return MetricExtractionResult(success=False, error=f"No numeric values in list for '{key_name}'")
        per_seed_vals = nums
        if aggregation == "mean_over_seeds" or aggregation == "mean":
            mean_v = sum(nums) / len(nums)
            return MetricExtractionResult(
                success=True,
                value=mean_v,
                per_seed=nums,
                source_file=str(json_path),
                excerpt=json.dumps({key_name: val})[:400]
            )
        elif aggregation == "max":
            return MetricExtractionResult(success=True, value=max(nums), per_seed=nums, source_file=str(json_path))
        elif aggregation == "min":
            return MetricExtractionResult(success=True, value=min(nums), per_seed=nums, source_file=str(json_path))
        else: # last
            return MetricExtractionResult(success=True, value=nums[-1], per_seed=nums, source_file=str(json_path))

    numeric_val = _parse_numeric(val, reported_hint)
    if numeric_val is None or not math.isfinite(numeric_val):
        return MetricExtractionResult(success=False, error=f"Value for '{key_name}' is not finite: {val}")

    return MetricExtractionResult(
        success=True,
        value=numeric_val,
        std=float(std_val) if std_val is not None else None,
        per_seed=per_seed_vals if isinstance(per_seed_vals, list) else None,
        source_file=str(json_path),
        excerpt=json.dumps({key_name: val})[:400]
    )

def _extract_from_csv(
    csv_path: Path,
    col_name: str,
    aggregation: str,
    reported_hint: Optional[float]
) -> MetricExtractionResult:
    if not csv_path.exists():
        return MetricExtractionResult(success=False, error=f"CSV file not found: {csv_path}")

    rows: List[Dict[str, str]] = []
    try:
        with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
    except Exception as e:
        return MetricExtractionResult(success=False, error=f"Failed reading CSV {csv_path}: {e}")

    if not rows:
        return MetricExtractionResult(success=False, error=f"CSV file {csv_path} is empty")

    # Match column (case-insensitive fallback)
    matched_col = None
    for field in rows[0].keys():
        if field and field.strip().lower() == col_name.strip().lower():
            matched_col = field
            break

    if not matched_col:
        # Check if there is only 1 or 2 columns, pick the last numeric one
        cols = list(rows[0].keys())
        if len(cols) == 1:
            matched_col = cols[0]
        else:
            return MetricExtractionResult(success=False, error=f"Column '{col_name}' not found in CSV {csv_path}")

    vals = []
    for r in rows:
        num = _parse_numeric(r.get(matched_col), reported_hint)
        if num is not None and math.isfinite(num):
            vals.append(num)

    if not vals:
        return MetricExtractionResult(success=False, error=f"No valid numeric entries found in column '{matched_col}'")

    if aggregation == "mean_over_seeds" or aggregation == "mean":
        final_val = sum(vals) / len(vals)
    elif aggregation == "max":
        final_val = max(vals)
    elif aggregation == "min":
        final_val = min(vals)
    else: # last
        final_val = vals[-1]

    return MetricExtractionResult(
        success=True,
        value=final_val,
        per_seed=vals if len(vals) > 1 else None,
        source_file=str(csv_path),
        line_number=len(rows) + 1,
        excerpt=f"{matched_col}: {final_val} (from {len(rows)} rows)"
    )

def _extract_from_regex(
    log_file: Path,
    regex_pattern: str,
    reported_hint: Optional[float]
) -> MetricExtractionResult:
    if not log_file.exists():
        return MetricExtractionResult(success=False, error=f"Log file not found: {log_file}")

    content = log_file.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()

    matched_val = None
    matched_line_num = None
    matched_line_text = ""

    compiled = re.compile(regex_pattern)
    for idx, line in enumerate(lines, start=1):
        m = compiled.search(line)
        if m:
            group_dict = m.groupdict()
            if "val" in group_dict:
                matched_val = group_dict["val"]
            elif "metric" in group_dict:
                matched_val = group_dict["metric"]
            elif len(m.groups()) > 0:
                matched_val = m.group(1)
            else:
                matched_val = m.group(0)

            matched_line_num = idx
            matched_line_text = line
            # Keep iterating to get the last occurrence if multiple
            # (or break if first; standard is last logged value)

    if matched_val is None:
        return MetricExtractionResult(
            success=False,
            error=f"Regex '{regex_pattern}' produced no match in log {log_file.name}"
        )

    parsed = _parse_numeric(matched_val, reported_hint)
    if parsed is None or not math.isfinite(parsed):
        return MetricExtractionResult(
            success=False,
            error=f"Regex matched '{matched_val}', but could not parse as finite numeric value"
        )

    return MetricExtractionResult(
        success=True,
        value=parsed,
        source_file=str(log_file),
        line_number=matched_line_num,
        excerpt=matched_line_text[:300]
    )

def record_metric_evidence(
    state: ProjectState,
    result: MetricExtractionResult,
    tool_call_id: str
) -> Optional[str]:
    """Snapshots the extracted metric source into the immutable evidence ledger."""
    if not result.success or not result.source_file or not os.path.exists(result.source_file):
        return None

    try:
        from tools.evidence import record_evidence
        ev_type = "log" if result.source_file.endswith(".log") else "result"
        ev = record_evidence(
            state,
            type_=ev_type,
            source_path=result.source_file,
            line_start=result.line_number,
            line_end=result.line_number,
            tool="extract_metric",
            tool_call_id=tool_call_id
        )
        result.evidence_id = ev.id
        return ev.id
    except Exception as e:
        logger.warning(f"Failed to record evidence for extracted metric: {e}")
        return None
