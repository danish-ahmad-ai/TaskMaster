import json
import os
from dotenv import load_dotenv

def test_config():
    # Test environment variables
    load_dotenv()
    env_vars = {
        "FIREBASE_API_KEY": os.getenv("FIREBASE_API_KEY"),
        "FIREBASE_AUTH_DOMAIN": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "FIREBASE_DATABASE_URL": os.getenv("FIREBASE_DATABASE_URL"),
        "FIREBASE_PROJECT_ID": os.getenv("FIREBASE_PROJECT_ID"),
        "FIREBASE_STORAGE_BUCKET": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "FIREBASE_MESSAGING_SENDER_ID": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "FIREBASE_APP_ID": os.getenv("FIREBASE_APP_ID")
    }
    
    print("\nEnvironment Variables:")
    for key, value in env_vars.items():
        status = "✓" if value else "✗"
        print(f"{status} {key}: {'[SET]' if value else '[MISSING]'}")
    
    # Test firebase_config.json
    config_path = os.path.join("credentials", "firebase_config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("\nFirebase Config File:")
        for key in ["apiKey", "authDomain", "databaseURL", "projectId"]:
            status = "✓" if key in config else "✗"
            print(f"{status} {key}: {'[SET]' if key in config else '[MISSING]'}")
    else:
        print("\nFirebase Config File: [MISSING]")

if __name__ == "__main__":
    test_config() 