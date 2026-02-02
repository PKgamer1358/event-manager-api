import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from app.services.media import parse_cloudinary_url

url = "https://res.cloudinary.com/dhv85dwtn/image/upload/v1770055035/events/event_65/xzcfb0keej0quanbvrbf.png"
print(f"Testing URL: {url}")
result = parse_cloudinary_url(url)
print(f"Result: {result}")

if result and result["resource_type"] == "image":
    print("SUCCESS: Correctly identified as image.")
else:
    print("FAILURE: Incorrect identification.")
