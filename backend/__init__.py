# backend/__init__.py
import os

# Load .env file manually if exists
for env_dir in [os.path.dirname(__file__), os.path.join(os.path.dirname(__file__), "..")]:
    env_path = os.path.join(env_dir, ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip()
        except Exception as e:
            print(f"Error loading .env from {env_path} in backend/__init__.py: {e}")
