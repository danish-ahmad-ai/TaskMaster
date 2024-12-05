import requests
import os
from dotenv import load_dotenv
from typing import Optional
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ImgBBAPI:
    """Handles image uploads to ImgBB service."""
    
    def __init__(self):
        """Initialize with API key from environment."""
        self.api_key = os.getenv('IMGBB_API_KEY')
        if not self.api_key:
            raise ValueError("ImgBB API key not found in environment variables")
        
        self.upload_url = "https://api.imgbb.com/1/upload"
        
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

# Create global instance
imgbb_api = ImgBBAPI() 