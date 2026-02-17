import google.generativeai as genai
import os

api_key = "AIzaSyBXztlBxZaOJz_MAK7erf20gYi0mEaiv-g"
genai.configure(api_key=api_key)

print("Listing models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
