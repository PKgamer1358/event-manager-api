import re

def parse_cloudinary_url(url: str):
    pattern = r"\/([^\/]+)\/([^\/]+)\/(?:v(\d+)\/)?(.+?)(?:\.(\w+))?$"
    match = re.search(pattern, url)
    
    if not match:
        return None
        
    return {
        "resource_type": match.group(1),
        "type": match.group(2),
        "version": match.group(3),
        "public_id": match.group(4),
        "format": match.group(5)
    }

url = "https://res.cloudinary.com/dhv85dwtn/image/upload/v1770055035/events/event_65/xzcfb0keej0quanbvrbf.png"
print(f"Testing URL: {url}")
result = parse_cloudinary_url(url)
print(f"Result: {result}")

print("-" * 20)

# Proposed Fix: Anchoring or explicit types
def parse_strict(url: str):
    # Match standard Cloudinary path structure:
    # .../<resource_type>/<type>/...
    # resource_type is likely image, video, raw
    # type is likely upload, private, authenticated
    
    pattern = r"\/(image|video|raw)\/(upload|private|authenticated)\/(?:v(\d+)\/)?(.+?)(?:\.(\w+))?$"
    match = re.search(pattern, url)
    
    if not match:
        return None
    
    return {
        "resource_type": match.group(1),
        "type": match.group(2),
        "version": match.group(3),
        "public_id": match.group(4),
        "format": match.group(5)
    }

print("Testing Strict Regex:")
result_strict = parse_strict(url)
print(f"Result: {result_strict}")
