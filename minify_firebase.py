import json
import os

file_path = "app/core/firebase-service-account.json"

if not os.path.exists(file_path):
    print(f"❌ Error: File not found at {file_path}")
    exit(1)

try:
    with open(file_path, "r") as f:
        data = json.load(f)
    
    # Minify (remove spaces/newlines)
    minified = json.dumps(data, separators=(',', ':'))
    
    print("\n✅ COPY THE LINE BELOW (IT IS ONE LONG LINE):")
    print("---------------------------------------------------")
    print(minified)
    print("---------------------------------------------------")
    print("\n👉 Paste this into Render -> Environment -> FIREBASE_CREDENTIALS")

except json.JSONDecodeError:
    print("❌ Error: Your local JSON file is also invalid.")
except Exception as e:
    print(f"❌ Error: {e}")
