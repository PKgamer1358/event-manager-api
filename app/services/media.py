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
