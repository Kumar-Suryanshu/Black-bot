import json
import shutil
import os
from pathlib import Path

def main():
    with open("benchmarks/calibration.json") as f:
        calib = json.load(f)
        
    good_lr = calib["good_lr"]
    bad_lr = calib["bad_lr"]
    
    cases_dir = Path("benchmarks/cases")
    if cases_dir.exists():
        import stat
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(cases_dir, onerror=remove_readonly)
        
    gold_dir = Path("benchmarks/gold")
    if gold_dir.exists():
        import stat
        def remove_readonly(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(gold_dir, onerror=remove_readonly)
        
    cases_dir.mkdir(parents=True)
    gold_dir.mkdir(parents=True)
    
    registry = {"cases": []}
    
    def create_case(case_id, title, desc, configure_fn, gold_data):
        case_path = cases_dir / case_id
        shutil.copytree("benchmarks/template", case_path)
        
        # README substitution
        readme_path = case_path / "README.md"
        content = readme_path.read_text()
        content = content.replace("{good_lr}", str(good_lr))
        readme_path.write_text(content)
        
        configure_fn(case_path)
        
        registry["cases"].append({
            "id": case_id,
            "title": title,
            "description": desc,
            "repo_path": str(case_path),
            "paper_path": "benchmarks/papers/digits_softmax.pdf",
            "gold_path": str(gold_dir / f"{case_id}.json")
        })
        
        with open(gold_dir / f"{case_id}.json", "w") as f:
            json.dump(gold_data, f, indent=2)
            
    # b1_control
    def config_b1(path):
        with open(path / "configs/default.yaml", "w") as f:
            f.write(f"learning_rate: {good_lr}\nepochs: 20\nbatch_size: 32\nl2: 0.0\nseeds: [0, 1, 2, 3, 4]\ntest_size: 0.2\nsplit_seed: 1234\n")
            
    create_case("b1_control", "Control Case", "Correct paper implementation", config_b1, {
        "case_id": "b1_control", "expected_status": "REPRODUCED", "expected_patches": 0, "faults": []
    })
    
    # b2_dependency
    def config_b2(path):
        config_b1(path)
        reqs = (path / "requirements.txt").read_text()
        (path / "requirements.txt").write_text(reqs.replace("PyYAML==6.0.1\n", ""))
        
    create_case("b2_dependency", "Missing Dependency", "Omitted PyYAML", config_b2, {
        "case_id": "b2_dependency", "expected_status": "REPRODUCED", "expected_patches": 1, 
        "faults": [{"order": 1, "class": "dependency_missing", "file": "requirements.txt", "gold_patch": {"type": "dependency", "package": "pyyaml"}}]
    })
    
    # b3_silent_config
    def config_b3(path):
        with open(path / "configs/default.yaml", "w") as f:
            f.write(f"learning_rate: {bad_lr}\nepochs: 20\nbatch_size: 32\nl2: 0.0\nseeds: [0, 1, 2, 3, 4]\ntest_size: 0.2\nsplit_seed: 1234\n")
            
    create_case("b3_silent_config", "Silent Config Error", "Bad learning rate", config_b3, {
        "case_id": "b3_silent_config", "expected_status": "REPRODUCED", "expected_patches": 1,
        "faults": [{"order": 1, "class": "config_mismatch", "file": "configs/default.yaml", "key": "learning_rate", "gold_value": str(good_lr)}]
    })
    
    # b4_combined
    def config_b4(path):
        config_b3(path)
        reqs = (path / "requirements.txt").read_text()
        (path / "requirements.txt").write_text(reqs.replace("PyYAML==6.0.1\n", ""))
        
    create_case("b4_combined", "Combined Error", "Missing dependency and bad learning rate", config_b4, {
        "case_id": "b4_combined", "expected_status": "REPRODUCED", "expected_patches": 2,
        "faults": [
            {"order": 1, "class": "dependency_missing", "file": "requirements.txt", "gold_patch": {"type": "dependency", "package": "pyyaml"}},
            {"order": 2, "class": "config_mismatch", "file": "configs/default.yaml", "key": "learning_rate", "gold_value": str(good_lr)}
        ]
    })
    
    # b5_unable
    def config_b5(path):
        config_b1(path)
        with open(path / "requirements.txt", "a") as f:
            f.write("torch\n")
        model = (path / "model.py").read_text()
        model = model.replace("class SoftmaxRegression:", "class SoftmaxRegression:\n    device = 'cuda'\n")
        (path / "model.py").write_text(model)
        
    create_case("b5_unable", "GPU Required", "Code explicitly requires cuda", config_b5, {
        "case_id": "b5_unable", "expected_status": "UNABLE_TO_EXECUTE", "expected_blocker": "gpu_required", "expected_patches": 0, "faults": []
    })
    
    with open("benchmarks/registry.json", "w") as f:
        json.dump(registry, f, indent=2)
        
    print("Seeded faults successfully.")

if __name__ == '__main__':
    main()

