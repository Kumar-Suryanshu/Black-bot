import json
import time
import sys
import os
import csv
from datetime import datetime
from baselines.b0_fixed import run_b0

class SimulatedApprover:
    def approve(self, policy_passed, critic_verdict, critic_banner):
        return policy_passed and critic_verdict == "SUPPORTED" and not critic_banner

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--systems", type=str, default="B-0", help="Comma separated systems: B-0,B-2,Rerun")
    args = parser.parse_args()
    
    systems = args.systems.split(",")
    repeats = 3
    
    with open("benchmarks/registry.json") as f:
        registry = json.load(f)
        
    out_dir = f"benchmarks/results/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(out_dir, exist_ok=True)
    
    results = []
    
    for case in registry["cases"]:
        case_id = case["id"]
        with open(case["gold_path"]) as f:
            gold = json.load(f)
            
        for sys_name in systems:
            if sys_name == "B-0":
                for i in range(repeats):
                    print(f"Running {sys_name} on {case_id} (run {i+1}/{repeats})...")
                    start_t = time.time()
                    try:
                        status = run_b0(case_id, case, run_n=i+1)
                    except Exception as e:
                        print(f"Error: {e}")
                        status = "FAILED_TO_RUN"
                    wall_time = time.time() - start_t
                    
                    matches_gold = (status == gold["expected_status"])
                    
                    res = {
                        "case": case_id,
                        "system": sys_name,
                        "run": i+1,
                        "final_status": status,
                        "matches_gold": matches_gold,
                        "diagnosed_class": None,
                        "gold_class_match": False,
                        "patches_proposed": 0,
                        "patches_applied": 0,
                        "false_repairs": 0,
                        "metric_chasing_incidents": 0,
                        "retries": 0,
                        "wall_time_s": round(wall_time, 2),
                        "human_interventions": 0,
                        "evidence_completeness": 0,
                        "hallucinated_evidence_counters": 0,
                        "critic_verdicts": "",
                        "human_simulated": True
                    }
                    results.append(res)
                    print(f"Result: {status} (matches gold: {matches_gold})")
            elif sys_name == "B-2":
                print("B-2 not fully implemented.")
            elif sys_name == "Rerun":
                print("Rerun harness via SimulatedApprover will be implemented in Stage 7.")
                
    if results:
        keys = results[0].keys()
        with open(f"{out_dir}/results.csv", "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
            
        with open(f"{out_dir}/results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        md = "# Benchmark Results\n\n"
        md += "| Case | System | Run | Status | Matches Gold | Time (s) |\n"
        md += "|---|---|---|---|---|---|\n"
        for r in results:
            md += f"| {r['case']} | {r['system']} | {r['run']} | {r['final_status']} | {r['matches_gold']} | {r['wall_time_s']} |\n"
            
        with open(f"{out_dir}/results.md", "w") as f:
            f.write(md)
            
        with open("benchmarks/MEASURED.md", "a") as f:
            f.write("\n\n" + md)
            
        print(f"Wrote results to {out_dir}")

if __name__ == "__main__":
    main()

