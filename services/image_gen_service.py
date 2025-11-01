# -*- coding: utf-8 -*-
import os, base64, json, requests, mimetypes, uuid, time
from typing import Optional, Dict, Any, List
from services.core.api_config import GEMINI_IMAGE_MODEL, GEMINI_BASE, gemini_image_endpoint, IMAGE_GEN_TIMEOUT
from services.core.key_manager import get_all_keys, refresh
from services.core.api_key_rotator import APIKeyRotator, APIKeyRotationError


class ImageGenError(Exception):
    """Image generation error"""
    pass


def generate_image_gemini(prompt: str, timeout: int = None, retry_delay: float = 15.0, enforce_rate_limit: bool = True, log_callback=None) -> bytes:
    """
    Generate image using Gemini Flash Image model with APIKeyRotator (PR#5)
    
    Args:
        prompt: Text prompt for image generation
        timeout: Request timeout in seconds (default from api_config)
        retry_delay: Base delay before first API call (15.0s for Gemini free tier safety)
        enforce_rate_limit: If True, wait before first API call (default True)
        log_callback: Optional callback function for logging (receives string messages)
        
    Returns:
        Generated image as bytes
        
    Raises:
        ImageGenError: If generation fails
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
    
    timeout = timeout or IMAGE_GEN_TIMEOUT
    refresh()
    keys = get_all_keys('google')
    if not keys:
        raise ImageGenError("No Google API keys available")
    
    log(f"[DEBUG] Tìm thấy {len(keys)} Google API keys")
    
    # Enforce rate limit before first call
    if enforce_rate_limit:
        log(f"[RATE LIMIT] Đợi {retry_delay}s trước khi gọi API...")
        time.sleep(retry_delay)
    
    # PR#5: Define API call function for APIKeyRotator
    def api_call_with_key(api_key: str) -> bytes:
        """Make API call with given key"""
        url = gemini_image_endpoint(api_key)
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.9,
                "topK": 40,
                "topP": 0.95,
            }
        }
        
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract image data
        candidates = data.get("candidates", [])
        if not candidates:
            raise ImageGenError("No candidates in response")
        
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise ImageGenError("No parts in candidate")
        
        # Look for inline_data with image
        for part in parts:
            if "inline_data" in part:
                mime_type = part["inline_data"].get("mime_type", "")
                if mime_type.startswith("image/"):
                    b64_data = part["inline_data"].get("data", "")
                    if b64_data:
                        return base64.b64decode(b64_data)
        
        raise ImageGenError("No image data found in response")
    
    # PR#5: Use APIKeyRotator
    try:
        rotator = APIKeyRotator(keys, log_callback=log)
        return rotator.execute(api_call_with_key)
    except APIKeyRotationError as e:
        raise ImageGenError(str(e))


# New implementation: Intelligent rate-limited image generation with API key rotation
def generate_image_with_rate_limit(
    prompt: str,
    api_keys: Optional[List[str]] = None,
    model: str = "gemini",
    aspect_ratio: str = "1:1",
    log_callback=None
) -> Optional[bytes]:
    """
    Generate image with intelligent API key rotation and rate limiting
    
    This function uses the new APIKeyRotationManager to handle:
    - Per-key usage tracking and cooldowns
    - Exponential backoff (2s, 4s, 8s) on rate limits
    - 60s cooldown after exhausting retries on a key
    - Minimum 2s interval between calls on same key
    - Smart rotation that skips rate-limited keys
    
    Args:
        prompt: Image generation prompt
        api_keys: List of Google API keys (if None, loads from config)
        model: Model to use - 'gemini' for Gemini Flash Image or 'imagen_4' for Imagen 4
        aspect_ratio: Image aspect ratio from UI (e.g., "9:16", "16:9", "1:1", "4:5")
        log_callback: Optional callback function for logging
    
    Returns:
        Generated image bytes or None if generation fails
        
    Note:
        - For Imagen 4: Automatically normalizes 4:5 to 3:4 (closest supported ratio)
        - For Gemini: Accepts any aspect ratio from UI
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
    
    # Load API keys if not provided
    if api_keys is None:
        from services.core.key_manager import get_all_keys, refresh
        refresh()
        api_keys = get_all_keys('google')
    
    if not api_keys:
        log("[ERROR] No Google API keys available")
        return None
    
    log(f"[IMAGE GEN] Using {len(api_keys)} API keys with intelligent rotation")
    
    # Normalize aspect ratio for Imagen 4
    normalized_ratio = aspect_ratio
    if model.lower() == 'imagen_4':
        # Imagen 4 doesn't support 4:5, normalize to 3:4
        if aspect_ratio == "4:5":
            normalized_ratio = "3:4"
            log(f"[ASPECT RATIO] Normalized {aspect_ratio} to {normalized_ratio} for Imagen 4")
    
    try:
        # Import the new APIKeyRotationManager
        from services.google.api_key_manager import APIKeyRotationManager
        
        # Create rotation manager
        rotation_manager = APIKeyRotationManager(api_keys, log_callback=log)
        
        # Define the API call function based on model
        if model.lower() == "gemini":
            def api_call_with_key(api_key: str) -> bytes:
                """Make Gemini API call with the given key"""
                url = gemini_image_endpoint(api_key)
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.9,
                        "topK": 40,
                        "topP": 0.95,
                    }
                }
                
                response = requests.post(url, json=payload, timeout=IMAGE_GEN_TIMEOUT)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract image data
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ImageGenError("No candidates in response")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise ImageGenError("No parts in candidate")
                
                # Look for inline_data with image
                for part in parts:
                    if "inline_data" in part:
                        mime_type = part["inline_data"].get("mime_type", "")
                        if mime_type.startswith("image/"):
                            b64_data = part["inline_data"].get("data", "")
                            if b64_data:
                                return base64.b64decode(b64_data)
                
                raise ImageGenError("No image data found in response")
        
        elif model.lower() == "imagen_4":
            def api_call_with_key(api_key: str) -> bytes:
                """Make Imagen 4 API call with the given key"""
                # Imagen 4 endpoint (placeholder - adjust based on actual API)
                # This is a simplified example - actual implementation may vary
                url = f"{GEMINI_BASE}/models/imagen-4.0-generate:generateContent?key={api_key}"
                
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "aspectRatio": normalized_ratio,
                        "temperature": 0.9,
                    }
                }
                
                response = requests.post(url, json=payload, timeout=IMAGE_GEN_TIMEOUT)
                response.raise_for_status()
                
                data = response.json()
                
                # Extract image data (same format as Gemini)
                candidates = data.get("candidates", [])
                if not candidates:
                    raise ImageGenError("No candidates in response")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise ImageGenError("No parts in candidate")
                
                for part in parts:
                    if "inline_data" in part:
                        mime_type = part["inline_data"].get("mime_type", "")
                        if mime_type.startswith("image/"):
                            b64_data = part["inline_data"].get("data", "")
                            if b64_data:
                                return base64.b64decode(b64_data)
                
                raise ImageGenError("No image data found in response")
        else:
            log(f"[ERROR] Unsupported model: {model}")
            return None
        
        # Execute with intelligent rotation
        log(f"[IMAGE GEN] Generating with {model} (aspect ratio: {normalized_ratio})...")
        result = rotation_manager.execute_with_rotation(api_call_with_key)
        
        # Log final status
        status = rotation_manager.get_status()
        log(f"[STATUS] Keys: {status['available_keys']}/{status['total_keys']} available, "
            f"{status['rate_limited_keys']} rate-limited")
        
        return result
        
    except Exception as e:
        log(f"[ERROR] Image generation failed: {str(e)[:200]}")
        return None
