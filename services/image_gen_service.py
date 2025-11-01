# -*- coding: utf-8 -*-
import os, base64, json, requests, mimetypes, uuid, time
from typing import Optional, Dict, Any
from services.core.api_config import GEMINI_IMAGE_MODEL, gemini_image_endpoint, IMAGE_GEN_TIMEOUT
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


# Issue 6: Add missing rate-limited image generation function
# Rate limit tracking
_last_call_time = {}
_call_counts = {}


def generate_image_with_rate_limit(
    prompt: str,
    api_keys: list = None,
    model: str = "gemini",
    aspect_ratio: str = "1:1",
    size: str = "1024x1024",
    delay_before: float = 0.0,
    rate_limit_delay: float = 10.0,
    max_calls_per_minute: int = 6,
    logger=None,
    log_callback=None
) -> Optional[bytes]:
    """
    Generate image with rate limiting to avoid 429 errors
    
    Args:
        prompt: Image generation prompt
        api_keys: List of API keys to rotate through (optional, uses config if not provided)
        model: Model to use (gemini, dalle, imagen_4, etc.)
        aspect_ratio: Image aspect ratio (e.g., "9:16", "16:9", "1:1", "4:5")
        size: Image size
        delay_before: Seconds to wait before making the call (default 0, no delay)
        rate_limit_delay: Minimum seconds between calls (default 10.0)
        max_calls_per_minute: Maximum API calls per minute (default 6)
        logger: Optional callback function for logging (alias for log_callback)
        log_callback: Optional callback function for logging
    
    Returns:
        Generated image bytes or None if generation fails
    """
    # Support both logger and log_callback parameter names
    log_fn = logger or log_callback
    
    def log(msg):
        if log_fn:
            log_fn(msg)
    
    global _last_call_time, _call_counts
    
    # Optional delay before call (for manual rate limiting)
    if delay_before > 0:
        log(f"[RATE LIMIT] Đợi {delay_before}s trước khi gọi API...")
        time.sleep(delay_before)
    
    # Check rate limit
    current_time = time.time()
    model_key = f"{model}_{size}"
    
    # Initialize tracking for this model
    if model_key not in _last_call_time:
        _last_call_time[model_key] = 0
        _call_counts[model_key] = 0
    
    # Check if we need to wait based on last call time
    time_since_last = current_time - _last_call_time[model_key]
    
    if time_since_last < rate_limit_delay and _last_call_time[model_key] > 0:
        wait_time = rate_limit_delay - time_since_last
        log(f"[RATE LIMIT] Chờ {wait_time:.1f}s trước lần gọi tiếp theo...")
        time.sleep(wait_time)
        current_time = time.time()
    
    # Reset call count every minute
    if time_since_last > 60:
        _call_counts[model_key] = 0
    
    # Check max calls per minute
    if _call_counts[model_key] >= max_calls_per_minute:
        log(f"[RATE LIMIT] Đạt giới hạn {max_calls_per_minute} lần gọi/phút. Chờ 60s...")
        time.sleep(60)
        _call_counts[model_key] = 0
    
    # Update tracking
    _last_call_time[model_key] = time.time()
    _call_counts[model_key] += 1
    
    # Get API keys from parameter or config
    if api_keys is None or len(api_keys) == 0:
        refresh()
        api_keys = get_all_keys('google')
    
    if not api_keys or len(api_keys) == 0:
        log("[ERROR] Không có Google API keys khả dụng")
        return None
    
    log(f"[INFO] Sử dụng {len(api_keys)} API keys với rotation")
    
    # Call appropriate generation function with key rotation
    try:
        if model.lower() in ("gemini", "imagen_4"):
            log(f"[IMAGE GEN] Tạo ảnh với {model} (lần gọi {_call_counts[model_key]}/{max_calls_per_minute})...")
            
            # Use APIKeyRotator for key rotation
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
            
            # Use APIKeyRotator with provided keys
            rotator = APIKeyRotator(api_keys, log_callback=log_fn)
            return rotator.execute(api_call_with_key)
            
        elif model.lower() == "dalle":
            log(f"[IMAGE GEN] Tạo ảnh với DALL-E...")
            # Import DALL-E client if available
            try:
                from services.openai.dalle_client import generate_image
                return generate_image(prompt, size=size)
            except ImportError:
                log("[ERROR] DALL-E client không khả dụng")
                return None
        else:
            log(f"[ERROR] Model không được hỗ trợ: {model}")
            return None
    except Exception as e:
        log(f"[ERROR] Lỗi tạo ảnh: {str(e)[:200]}")
        return None
