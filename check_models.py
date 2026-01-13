import google.generativeai as genai
import os

def parse_secrets():
    secrets = {}
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    secrets[key] = value
    except Exception as e:
        print(f"Error reading secrets: {e}")
    return secrets

secrets = parse_secrets()
api_key = secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        genai.configure(api_key=api_key)
        print("Listing available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"API Error: {e}")
else:
    print("API Key not found in secrets.")
