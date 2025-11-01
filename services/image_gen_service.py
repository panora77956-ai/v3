# -*- coding: utf-8 -*-
import os, base64, json, requests, mimetypes, uuid, time
from typing import Optional, Dict, Any
from services.core.api_config import GEMINI_IMAGE_MODEL, gemini_image_endpoint, IMAGE_GEN_TIMEOUT
from services.core.key_manager import get_all_keys, refresh


class ImageGenError(Exception):
    """Image generation error"""
    pass


def generate_image_gemini(prompt: str, timeout: int = None, retry_delay: float = 15.0, enforce_rate_limit: bool = True, log_callback=None) -> bytes:
    """
    Generate image using Gemini Flash Image model with ENHANCED rate limiting
    
    FIXED PR#4: Increased delay from 10s to 15s between key switches
    Added enforce_rate_limit parameter for better control
    Retry delay increased to 30s between key switches
    
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
    
    # PR#4: Enforce rate limit before first call
    if enforce_rate_limit:
        log(f"[RATE LIMIT] Đợi {retry_delay}s trước khi gọi API...")
        time.sleep(retry_delay)
    
    last_error = None
    rate_limited_count = 0
    
    for key_idx, api_key in enumerate(keys):
        try:
            # CRITICAL FIX PR#4: Increase delay between key switches to 30s
            # Gemini Free Tier: 15 req/min = 4s/req minimum, use 30s for safety on retry
            if key_idx > 0:
                log(f"[INFO] Chờ 30s trước khi thử key tiếp theo...")
                time.sleep(30.0)
            
            key_preview = f"...{api_key[-6:]}"
            log(f"[INFO] Key {key_preview} (lần {key_idx + 1})")
            
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
            
            # Check for rate limiting
            if response.status_code == 429:
                rate_limited_count += 1
                log(f"[DEBUG] HTTP 429")
                log(f"[WARNING] Key {key_preview} rate limited, trying next key...")
                last_error = ImageGenError(f"Rate limited (HTTP 429)")
                continue
            
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
                            log(f"[DEBUG] HTTP 200 - Image generated successfully")
                            return base64.b64decode(b64_data)
            
            raise ImageGenError("No image data found in response")
            
        except requests.exceptions.Timeout:
            last_error = ImageGenError(f"Timeout after {timeout}s")
            log(f"[ERROR] Timeout với key {key_preview}")
            continue
            
        except requests.exceptions.RequestException as e:
            last_error = ImageGenError(f"Request error: {str(e)}")
            log(f"[ERROR] Request error với key {key_preview}: {str(e)[:100]}")
            continue
            
        except Exception as e:
            last_error = ImageGenError(f"Unexpected error: {str(e)}")
            log(f"[ERROR] Unexpected error: {str(e)[:100]}")
            continue
    
    # All keys exhausted
    if rate_limited_count == len(keys):
        log(f"[ERROR] All API keys are rate limited!")
        log(f"[INFO] Waiting 60s before final retry...")
        time.sleep(60)
        
        # Final retry with first key after cooldown
        try:
            api_key = keys[0]
            key_preview = f"...{api_key[-6:]}"
            log(f"[INFO] Final retry with key {key_preview}")
            
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
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                for part in parts:
                    if "inline_data" in part:
                        mime_type = part["inline_data"].get("mime_type", "")
                        if mime_type.startswith("image/"):
                            b64_data = part["inline_data"].get("data", "")
                            if b64_data:
                                log(f"[DEBUG] Final retry successful!")
                                return base64.b64decode(b64_data)
        except Exception as e:
            log(f"[ERROR] Final retry failed: {str(e)[:100]}")
    
    # Raise final error
    error_msg = "All API keys exhausted quota" if rate_limited_count == len(keys) else str(last_error)
    log(f"[ERROR] Generation failed: {error_msg}")
    raise ImageGenError(error_msg)


def generate_image_with_rate_limit(prompt: str, delay_before: float = 0, log_callback=None) -> Optional[bytes]:
    """
    Wrapper with pre-delay for rate limiting
    
    Args:
        prompt: Image generation prompt
        delay_before: Delay in seconds before generation (for rate limiting)
        log_callback: Optional logging callback
        
    Returns:
        Image bytes or None if failed
    """
    if delay_before > 0:
        if log_callback:
            log_callback(f"[INFO] Rate limit delay: {delay_before}s...")
        time.sleep(delay_before)
    
    try:
        return generate_image_gemini(prompt, log_callback=log_callback)
    except ImageGenError as e:
        if log_callback:
            log_callback(f"[ERROR] {str(e)}")
        return None