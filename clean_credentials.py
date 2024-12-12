import json
from pathlib import Path

def clean_config():
    """Create example config files with placeholder values"""
    
    # Clean firebase_config.json
    firebase_config = {
        "apiKey": "your-api-key",
        "authDomain": "your-project.firebaseapp.com",
        "databaseURL": "https://your-project.firebaseio.com",
        "projectId": "your-project-id",
        "storageBucket": "your-project.appspot.com",
        "messagingSenderId": "your-sender-id",
        "appId": "your-app-id"
    }
    
    # Clean serviceAccountKey.json
    service_account = {
        "type": "service_account",
        "project_id": "your-project-id",
        "private_key_id": "your-private-key-id",
        "private_key": "your-private-key",
        "client_email": "your-service-account-email",
        "client_id": "your-client-id",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "your-client-cert-url"
    }
    
    # Write example files
    examples_path = Path('examples')
    examples_path.mkdir(exist_ok=True)
    
    with open(examples_path / 'firebase_config.example.json', 'w') as f:
        json.dump(firebase_config, f, indent=4)
        
    with open(examples_path / 'serviceAccountKey.example.json', 'w') as f:
        json.dump(service_account, f, indent=4)
        
    print("Created example files with placeholder values")

if __name__ == "__main__":
    clean_config() 