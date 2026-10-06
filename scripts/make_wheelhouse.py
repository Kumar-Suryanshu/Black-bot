import docker
from pathlib import Path

def main():
    wheelhouse_dir = Path("wheelhouse").absolute()
    wheelhouse_dir.mkdir(exist_ok=True)
    
    req_dir = Path("sandbox/images").absolute()
    req_file = req_dir / "requirements.wheelhouse.txt"
    with open(req_file, "w") as f:
        f.write("numpy==1.26.4\n")
        f.write("PyYAML==6.0.1\n")
        
    client = docker.from_env()
    
    print(f"Building wheelhouse in {wheelhouse_dir}...")
    try:
        # Try to create container
        client.containers.run(
            image="rerun-base:py311",
            command=["pip", "download", "-d", "/wheelhouse", "-r", "/req/requirements.wheelhouse.txt"],
            volumes={
                str(wheelhouse_dir): {"bind": "/wheelhouse", "mode": "rw"},
                str(req_dir): {"bind": "/req", "mode": "ro"}
            },
            remove=True,
            network_mode="bridge",
            user="1000:1000"
        )
        print("Wheelhouse built successfully.")
    except Exception as e:
        print(f"Error building wheelhouse: {e}")

if __name__ == "__main__":
    main()

