# -*- coding: utf-8 -*-
"""Add voice loading logic to text2video_panel.py"""

import os
import shutil

def add_voice_loading():
    file_path = os.path.join("ui", "text2video_panel.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Backup
    backup = file_path + '.backup_add_voice_loading'
    shutil.copy2(file_path, backup)
    print(f"✅ Backup: {backup}\n")
    
    changes = []
    
    # ============================================
    # FIX 1: Initialize voice list on startup
    # ============================================
    
    # Find where voice ComboBox is created and add initial population
    old_voice_cb = '''        self.cb_voice = QComboBox()
        self.cb_voice.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_voice)  # Fix text clipping
        row1.addWidget(self.cb_voice, 1)
        voice_layout.addLayout(row1)'''
    
    new_voice_cb = '''        self.cb_voice = QComboBox()
        self.cb_voice.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_voice)  # Fix text clipping
        row1.addWidget(self.cb_voice, 1)
        voice_layout.addLayout(row1)
        
        # Initialize voice list based on default provider
        self._load_voices_for_provider()'''
    
    if old_voice_cb in content:
        content = content.replace(old_voice_cb, new_voice_cb)
        changes.append("✅ Added initial voice loading call")
    
    # ============================================
    # FIX 2: Add event connections for provider/language changes
    # ============================================
    
    # Find where domain/topic connections are and add voice connections
    old_connections = '''        # Domain/Topic cascade
        self.cb_domain.currentIndexChanged.connect(self._on_domain_changed)
        self.cb_topic.currentIndexChanged.connect(self._on_topic_changed)'''
    
    new_connections = '''        # Domain/Topic cascade
        self.cb_domain.currentIndexChanged.connect(self._on_domain_changed)
        self.cb_topic.currentIndexChanged.connect(self._on_topic_changed)
        
        # Voice loading - reload when provider or language changes
        self.cb_tts_provider.currentIndexChanged.connect(self._load_voices_for_provider)
        self.cb_out_lang.currentIndexChanged.connect(self._load_voices_for_provider)'''
    
    if old_connections in content:
        content = content.replace(old_connections, new_connections)
        changes.append("✅ Added voice loading event connections")
    
    # ============================================
    # FIX 3: Add _load_voices_for_provider method
    # ============================================
    
    # Add method before get_voice_settings
    insert_point = '    def get_voice_settings(self):'
    
    new_method = '''    def _load_voices_for_provider(self):
        """Load available voices based on selected provider and language"""
        provider = self.cb_tts_provider.currentData() or "google"
        language = self.cb_out_lang.currentData() or "vi"
        
        # Clear existing voices
        current_voice = self.cb_voice.currentData()  # Remember selection
        self.cb_voice.clear()
        
        try:
            from services.voice_options import get_voices_for_provider
            voices = get_voices_for_provider(provider, language)
            
            if voices:
                for voice in voices:
                    # Format: "🇻🇳 Nam Miền Bắc (Bình thường)"
                    voice_id = voice.get("id", "")
                    voice_name = voice.get("name", voice_id)
                    gender = voice.get("gender", "")
                    style = voice.get("style", "")
                    
                    # Build display name
                    display_parts = []
                    if gender:
                        display_parts.append(gender)
                    display_parts.append(voice_name)
                    if style:
                        display_parts.append(f"({style})")
                    
                    display_name = " ".join(display_parts)
                    self.cb_voice.addItem(display_name, voice_id)
                
                # Try to restore previous selection
                if current_voice:
                    idx = self.cb_voice.findData(current_voice)
                    if idx >= 0:
                        self.cb_voice.setCurrentIndex(idx)
                
                self._append_log(f"[INFO] Loaded {len(voices)} voices for {provider}/{language}")
            else:
                self.cb_voice.addItem("(Không có voice)", "")
                self._append_log(f"[WARN] No voices available for {provider}/{language}")
        
        except Exception as e:
            self._append_log(f"[ERR] Failed to load voices: {e}")
            self.cb_voice.addItem("(Lỗi load voice)", "")
    
    def get_voice_settings(self):'''
    
    if insert_point in content and '_load_voices_for_provider' not in content:
        content = content.replace(insert_point, new_method)
        changes.append("✅ Added _load_voices_for_provider() method")
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return changes

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ADDING VOICE LOADING FUNCTIONALITY")
    print("=" * 70 + "\n")
    
    changes = add_voice_loading()
    
    if changes:
        print("✅ APPLIED:")
        for change in changes:
            print(change)
        
        print("\n" + "=" * 70)
        print("🎉 VOICE LOADING ADDED!")
        print("=" * 70)
        
        print("\n📋 What was added:")
        print("  1. ✅ _load_voices_for_provider() method")
        print("  2. ✅ Initial voice loading on startup")
        print("  3. ✅ Auto-reload when provider changes")
        print("  4. ✅ Auto-reload when language changes")
        
        print("\n🚀 RUN:")
        print("  python -B main_image2video.py")
        
        print("\n✨ Expected:")
        print("  • Voice dropdown populated with Vietnamese voices")
        print("  • Change provider → voices update")
        print("  • Change language → voices update (Google TTS)")
    else:
        print("⚠️ No changes - may already exist or pattern not found")