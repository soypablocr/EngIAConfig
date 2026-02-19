import google.generativeai as genai
import os

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    # Try loading from .env manually
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print("No API Key found")
    exit(1)

genai.configure(api_key=API_KEY)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error listing models: {e}")
