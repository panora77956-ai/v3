"""Centralized Configuration"""
import json, os
from typing import Dict, Any

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path='config.json'):
        if self._initialized:
            return
        self.config_path = config_path
        self._config = {}
        self.load()
        self._initialized = True
    
    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except:
                self._config = {}
        else:
            self._config = {'tokens': [], 'google_keys': [], 'elevenlabs_keys': [], 'default_project_id': '', 'download_root': ''}
            self.save()
    
    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def get(self, key: str, default=None):
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        self._config[key] = value
        self.save()
    
    def get_all(self) -> Dict[str, Any]:
        return self._config.copy()

_config = ConfigManager()

def get_config_manager() -> ConfigManager:
    return _config
