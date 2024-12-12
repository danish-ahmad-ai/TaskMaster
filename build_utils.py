import shutil
from pathlib import Path
import os

def get_credentials_path():
    """Get path to secure credentials folder"""
    secure_path = os.getenv('TASKMASTER_CREDENTIALS_PATH', 
                           r'C:\Users\E-TIME\PycharmProjects\LiteProjs\credentials')
    return Path(secure_path)

def prepare_build():
    """Prepare files for build"""
    # Get paths
    secure_path = get_credentials_path()
    build_path = Path('build_temp')
    
    # Create build directory
    build_path.mkdir(exist_ok=True)
    
    # Copy secure files
    shutil.copy(secure_path / 'firebase_config.json', build_path)
    shutil.copy(secure_path / 'serviceAccountKey.json', build_path)
    shutil.copy(secure_path / '.env', build_path)

if __name__ == "__main__":
    prepare_build() 