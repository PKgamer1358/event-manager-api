import cloudinary
import cloudinary.uploader
from app.config import settings
from fastapi import HTTPException, status

def configure_cloudinary():
    cloudinary.config( 
        cloud_name = settings.CLOUDINARY_CLOUD_NAME, 
        api_key = settings.CLOUDINARY_API_KEY, 
        api_secret = settings.CLOUDINARY_API_SECRET 
    )

def upload_to_cloudinary(file, folder: str, resource_type: str = "auto"):
    configure_cloudinary()
    try:
        result = cloudinary.uploader.upload(
            file, 
            folder=folder,
            resource_type=resource_type
        )
        return result
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )

import re

def parse_cloudinary_url(url: str):
    """
    Parses a Cloudinary URL to extract key components.
    Returns: dict with resource_type, type, version, public_id, format
    """
    # Regex to capture:
    # /resource_type/type/(v_version/)?public_id.format
    # Example: https://res.cloudinary.com/cloudname/image/upload/v1234/folder/file.jpg
    
    pattern = r"\/([^\/]+)\/([^\/]+)\/(?:v(\d+)\/)?(.+?)(?:\.(\w+))?$"
    match = re.search(pattern, url)
    
    if not match:
        return None
        
    resource_type = match.group(1) # image, raw, video
    upload_type = match.group(2)   # upload, private
    version = match.group(3)       # 1234 (optional)
    public_id = match.group(4)     # folder/file
    fmt = match.group(5)           # jpg (optional)
    
    return {
        "resource_type": resource_type,
        "type": upload_type,
        "version": version,
        "public_id": public_id,
        "format": fmt
    }

def generate_download_url(public_id: str, resource_type: str = "image", format: str = None, version: str = None) -> str:
    """
    Generates a signed download URL (using fl_attachment).
    """
    configure_cloudinary()
    
    # If resource_type is "raw", Cloudinary usually includes the extension in the public_id
    # and "format" should be None.
    # If "image", format is separate.
    
    if resource_type == "raw" and format:
         public_id = f"{public_id}.{format}"
         format = None

    # Construct options
    options = {
        "resource_type": resource_type,
        "flags": "attachment",
        "sign_url": True,
        "type": "upload" # Default, but we usually want to match original. 
                         # Ideally passed in, but 'upload' is standard.
    }
    
    if format:
        options["format"] = format
        
    if version:
        options["version"] = version

    url, _ = cloudinary.utils.cloudinary_url(public_id, **options)
    return url
