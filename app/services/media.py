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

def extract_public_id(file_url: str, folder_prefix: str = "events") -> str:
    """
    Extracts the public_id from a Cloudinary URL.
    Assumes URL structure like: .../upload/v12345/events/event_1/file.jpg
    """
    try:
        parts = file_url.split("/")
        # Find 'events' (or folder_prefix) to start the public_id
        if folder_prefix in parts:
            idx = parts.index(folder_prefix)
            # stored public_id is usually folder/filename (no extension)
            # but we need to handle the extension. 
            # Cloudinary public_ids usually don't have extensions, 
            # but the URL does.
            
            # Join everything from folder_prefix
            full_path = "/".join(parts[idx:])
            
            # Remove extension
            import os
            public_id = os.path.splitext(full_path)[0]
            return public_id
            
    except Exception as e:
        print(f"Error extracting public_id: {e}")
        return ""
    return ""

def generate_download_url(public_id: str, resource_type: str = "image") -> str:
    """
    Generates a signed download URL (using fl_attachment).
    """
    configure_cloudinary()
    
    # cloudinary.utils.cloudinary_url returns a tuple (url, options)
    url, options = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=resource_type,
        flags="attachment",
        sign_url=True # IMPORTANT: Signs the URL to allow transformation if strict
    )
    return url
