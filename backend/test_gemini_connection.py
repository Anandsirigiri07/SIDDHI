# backend/test_gemini_connection.py
import os
import sys
import time
import json
import google.generativeai as genai

# Reconfigure stdout/stderr to use UTF-8 to prevent encoding crashes on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def load_env():
    """Loads .env file manually from the current or parent directory."""
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
                print(f"Error loading .env from {env_path}: {e}")

def main():
    load_env()
    
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        print(json.dumps({
            "success": False,
            "error": "GEMINI_API_KEY not found in environment or .env file",
            "sdk_version": genai.__version__,
            "model": "gemini-2.5-flash"
        }, indent=2))
        sys.exit(1)
        
    genai.configure(api_key=api_key)
    
    model_name = "gemini-2.5-flash"
    prompt = "Respond with the word CONNECTED"
    
    start_time = time.time()
    try:
        model = genai.GenerativeModel(model_name=model_name)
        response = model.generate_content(prompt)
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        response_text = response.text.strip()
        success = response_text.upper() == "CONNECTED"
        
        print(json.dumps({
            "success": success,
            "model": model_name,
            "response": response_text,
            "execution_time_ms": execution_time_ms,
            "sdk_version": genai.__version__
        }, indent=2))
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        print(json.dumps({
            "success": False,
            "error": str(e),
            "sdk_version": genai.__version__,
            "model": model_name,
            "api_endpoint": "generativelanguage.googleapis.com",
            "execution_time_ms": execution_time_ms
        }, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()
