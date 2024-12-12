import requests
import os
from dotenv import load_dotenv
from typing import Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def get_credentials_path():
    """Get path to secure credentials folder"""
    secure_path = os.getenv('TASKMASTER_CREDENTIALS_PATH', 
                           r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    return Path(secure_path)

class ImgBBAPI:
    """Handles image uploads to ImgBB service."""
    
    def __init__(self):
        """Initialize with API key from secure location."""
        self.api_key = self._get_api_key()
        if not self.api_key:
            raise ValueError("ImgBB API key not found")
        
        self.upload_url = "https://api.imgbb.com/1/upload"
        
    def _get_api_key(self) -> Optional[str]:
        """Get API key from secure location"""
        try:
            # First try secure credentials folder
            env_path = get_credentials_path() / '.env'
            if env_path.exists():
                load_dotenv(env_path)
            else:
                # Fallback to local .env
                load_dotenv()
            
            api_key = os.getenv('IMGBB_API_KEY')
            if api_key:
                logger.info("Successfully loaded ImgBB API key")
                return api_key
                
            raise ValueError("ImgBB API key not found in environment variables")
            
        except Exception as e:
            logger.error(f"Error loading ImgBB API key: {str(e)}")
            return None
    
    def upload_image(self, image_data: bytes, name: Optional[str] = None) -> Optional[str]:
        """
        Upload image to ImgBB.
        
        Args:
            image_data: Image data in bytes
            name: Optional name for the image
            
        Returns:
            URL of uploaded image or None if upload fails
        """
        try:
            payload = {
                'key': self.api_key,
                'image': image_data,
            }
            
            if name:
                payload['name'] = name
                
            response = requests.post(
                self.upload_url,
                payload,
                timeout=30  # 30 seconds timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['data']['url']
                    
            logger.error(f"Upload failed: {response.text}")
            return None
            
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return None
            
    def upload_image_file(self, file_path: str) -> Optional[str]:
        """
        Upload image from file.
        
        Args:
            file_path: Path to image file
            
        Returns:
            URL of uploaded image or None if upload fails
        """
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            return self.upload_image(image_data)
            
        except Exception as e:
            logger.error(f"Error reading image file: {str(e)}")
            return None

    def test_imgbb_connection(self) -> bool:
        """Test ImgBB API key validity"""
        try:
            # Create a small test image
            test_data = "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw=="
            payload = {
                'key': self.api_key,
                'image': test_data
            }
            
            response = requests.post(
                self.upload_url,
                payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("ImgBB API key is valid")
                return True
            
            logger.error(f"ImgBB API test failed: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"Error testing ImgBB connection: {str(e)}")
            return False

# Create global instance
imgbb_api = ImgBBAPI() 