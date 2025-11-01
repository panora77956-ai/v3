"""Key rotation with exponential backoff"""
import time
from typing import Callable, List, Any

class KeyRotator:
    def __init__(self, keys: List[str], log_callback=None):
        self.keys = [k for k in keys if k and k.strip()]
        self.log = log_callback or print
        self.max_retries_per_key = 3
        self.initial_delay = 2.0
    
    def execute(self, api_call: Callable[[str], Any]) -> Any:
        if not self.keys:
            raise ValueError("No API keys")
        last_error = None
        for key_index, key in enumerate(self.keys):
            if not key:
                continue
            retries = 0
            while retries < self.max_retries_per_key:
                try:
                    return api_call(key)
                except Exception as error:
                    last_error = error
                    error_msg = str(error).lower()
                    is_quota = any(kw in error_msg for kw in ['quota', '429', 'rate limit'])
                    if is_quota:
                        retries += 1
                        if retries < self.max_retries_per_key:
                            delay = self.initial_delay * (2 ** (retries - 1))
                            self.log(f"Quota error, retry in {delay}s...")
                            time.sleep(delay)
                        else:
                            break
                    else:
                        raise
        raise Exception(f"All keys failed: {last_error}")
