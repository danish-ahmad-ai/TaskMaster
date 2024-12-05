"""
Firebase Configuration Example
Rename this file to firebase_config.py and update with your Firebase credentials
"""

import pyrebase
from typing import Dict

# Firebase Configuration
config: Dict = {
    "apiKey": "AIzaSyAKuYZPqIx829rD-Gh3zHoFu3dGhVcFK2A",
    "authDomain": "taskmaster-b63d8.firebaseapp.com",
    "databaseURL": "https://taskmaster-b63d8-default-rtdb.firebaseio.com",
    "projectId": "taskmaster-b63d8",
    "storageBucket": "taskmaster-b63d8.firebasestorage.app",
    "messagingSenderId": "328452627014",
    "appId": "1:328452627014:web:8cefeb92614d54aed78847"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(config)
db = firebase.database()
auth = firebase.auth()

# Token Manager
class TokenManager:
    def __init__(self):
        self.user_token = None
        
    def set_token(self, token):
        self.user_token = token
        
    def get_token(self):
        return self.user_token
        
    def clear_token(self):
        self.user_token = None

token_manager = TokenManager() 