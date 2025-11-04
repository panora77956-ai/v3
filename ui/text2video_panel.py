
import json
import os
import re

from PyQt5.Qt import QDesktopServices
from PyQt5.QtCore import QLocale, QSize, Qt, QThread, QUrl
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QScrollArea,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from utils import config as cfg
from services.voice_options import get_style_list, get_style_info, SPEAKING_STYLES

from .text2video_panel_impl import _ASPECT_MAP, _LANGS, _VIDEO_MODELS, _Worker, build_prompt_json, get_model_key_from_display


class CollapsibleGroupBox(QGroupBox):
    """A GroupBox that can be collapsed/expanded by clicking the title"""
    
    def __init__(self, title="", parent=None, accordion_group=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self._accordion_group = accordion_group  # Store reference to sibling
        
        # Create container widget for content
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(10, 5, 10, 5)
        self._content_layout.setSpacing(6)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 0)
        main_layout.addWidget(self._content_widget)
        
        # ⭐ CRITICAL: Block signals during initialization
        self.blockSignals(True)
        self._content_widget.setVisible(False)
        self.setChecked(False)
        self.blockSignals(False)
        
        # Connect after setup
        self.toggled.connect(self._on_toggle)
    
    def content_layout(self):
        """Return the layout where content should be added"""
        return self._content_layout
    
    def _on_toggle(self, checked):
        """Show/hide content when toggled"""
        self._content_widget.setVisible(checked)
        
        # Accordion behavior: close sibling when opening this one
        if checked and self._accordion_group:
            self._accordion_group.setChecked(False)


    def __init__(self, title="", parent=None, accordion_group=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self._accordion_group = accordion_group  # Store reference to sibling
        
        # Create container widget for content
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(10, 5, 10, 5)  # Reduced bottom margin: 10 → 8
        self._content_layout.setSpacing(6)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 8, 0, 0)  # Reduced bottom: 20 → 5
        main_layout.addWidget(self._content_widget)
        
        # Initially hide content and set unchecked AFTER layout setup
        # ⭐ BLOCK SIGNALS during initialization
        self.blockSignals(True)
        self._content_widget.setVisible(False)
        self.setChecked(False)  # Set AFTER hiding content
        self.blockSignals(False)
        
        # Connect toggle AFTER initial setup
        self.toggled.connect(self._on_toggle)
    
    def content_layout(self):
        """Return the layout where content should be added"""
        return self._content_layout
    
    def _on_toggle(self, checked):
        """Show/hide content when toggled"""
        self._content_widget.setVisible(checked)
        
        # Accordion behavior: close sibling when opening this one
        if checked and self._accordion_group:
            self._accordion_group.setChecked(False)


class Text2VideoPane(QWidget):
    def __init__(self, parent=None):
        self._cards_state = {}  # scene->data
        super().__init__(parent)
        self._ctx = {}
        self._title = "Project"
        self._character_bible = None  # Part D: Store character bible
        self._script_data = None  # Store script data for bible generation
        self._build_ui()
        self._apply_styles()
        # Initialize folder label
        self._update_folder_label()

    def _build_ui(self):
        root = QHBoxLayout(self); root.setSpacing(12); root.setContentsMargins(8,8,8,8)
        self.setMinimumWidth(1000)  # Prevent severe clipping

        # LEFT (1/3) - PR#4: 6-row redesigned layout
        colL = QVBoxLayout(); colL.setSpacing(8)

        # PROJECT INFO GROUP
        project_group = QGroupBox("📋 Dự án")
        project_layout = QVBoxLayout(project_group)
        project_layout.setContentsMargins(10, 15, 10, 8)  # Reduced margins
        project_layout.setSpacing(6)  # Reduced spacing

        # Project name (moved from top)
        proj_row = QHBoxLayout()
        proj_row.addWidget(QLabel("<b>Tên dự án:</b>"))
        self.ed_project = QLineEdit()
        self.ed_project.setPlaceholderText("Nhập tên dự án (để trống sẽ tự tạo)")
        proj_row.addWidget(self.ed_project, 1)
        project_layout.addLayout(proj_row)

        # Idea text area (moved from top)
        project_layout.addWidget(QLabel("<b>Ý tưởng (đoạn văn):</b>"))
        self.ed_idea = QTextEdit()
        self.ed_idea.setAcceptRichText(False)
        self.ed_idea.setLocale(QLocale(QLocale.Vietnamese, QLocale.Vietnam))
        self.ed_idea.setPlaceholderText("Nhập ý tưởng thô (<10 từ)…")
        self.ed_idea.setMaximumHeight(100)
        project_layout.addWidget(self.ed_idea)

        # Domain selection
        domain_row = QHBoxLayout()
        lbl_domain = QLabel("Lĩnh vực:")
        lbl_domain.setStyleSheet("font-size: 12px;")
        domain_row.addWidget(lbl_domain)
        self.cb_domain = QComboBox()
        self.cb_domain.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_domain)  # Fix text clipping
        self.cb_domain.addItem("(Không chọn)", "")
        from services.domain_prompts import get_all_domains
        for domain in get_all_domains():
            self.cb_domain.addItem(domain, domain)
        domain_row.addWidget(self.cb_domain, 1)
        project_layout.addLayout(domain_row)

        # Topic selection
        topic_row = QHBoxLayout()
        lbl_topic = QLabel("Chủ đề:")
        lbl_topic.setStyleSheet("font-size: 12px;")
        topic_row.addWidget(lbl_topic)
        self.cb_topic = QComboBox()
        self.cb_topic.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_topic)  # Fix text clipping
        self.cb_topic.addItem("(Chọn lĩnh vực để load chủ đề)", "")
        self.cb_topic.setEnabled(False)
        topic_row.addWidget(self.cb_topic, 1)
        project_layout.addLayout(topic_row)

        # Remove empty space at bottom
        project_layout.addStretch()

        project_layout.addStretch(0)  # Remove bottom space
        colL.addWidget(project_group)

        # VIDEO SETTINGS - Collapsible (will be linked to voice after creation)
        video_settings_group = CollapsibleGroupBox("⚙️ Cài đặt video")
        video_layout = video_settings_group.content_layout()

        # Row 1: Video style + Model
        row1 = QHBoxLayout()
        lbl = QLabel("<b>Phong cách:</b>")
        lbl.setMinimumHeight(24)  # Ensure bold text visible
        row1.addWidget(lbl)
        self.cb_style = QComboBox()
        self._fix_combobox_height(self.cb_style)  # Fix text clipping
        self.cb_style.addItems(["Điện ảnh (Cinematic)", "Anime", "Tài liệu", "Quay thực", "3D/CGI", "Stop-motion"])
        row1.addWidget(self.cb_style, 1)
        row1.addSpacing(8)
        lbl = QLabel("<b>Model:</b>")
        lbl.setMinimumHeight(24)  # Ensure bold text visible
        row1.addWidget(lbl)
        self.cb_model = QComboBox()
        self._fix_combobox_height(self.cb_model)  # Fix text clipping
        # SHORT MODEL NAMES
        self.cb_model.addItems([
            "Veo3.1 i2v Fast Portrait",
            "Veo3.1 i2v Fast Landscape", 
            "Veo3.1 i2v Slow Portrait",
            "Veo3.1 i2v Slow Landscape",
            "Veo2 General",
            "Veo2 i2v"
        ])
        row1.addWidget(self.cb_model, 1)
        video_layout.addLayout(row1)

        # Row 2: Duration + Videos per scene
        row2 = QHBoxLayout()
        lbl = QLabel("<b>Thời lượng (s):</b>")
        lbl.setMinimumHeight(24)  # Ensure bold text visible
        row2.addWidget(lbl)
        self.sp_duration = QSpinBox()
        self.sp_duration.setRange(3, 3600)
        self.sp_duration.setValue(100)
        row2.addWidget(self.sp_duration, 1)
        row2.addSpacing(8)
        lbl = QLabel("<b>Số video/cảnh:</b>")
        lbl.setMinimumHeight(24)  # Ensure bold text visible
        row2.addWidget(lbl)
        self.sp_copies = QSpinBox()
        self.sp_copies.setRange(1, 5)
        self.sp_copies.setValue(1)
        row2.addWidget(self.sp_copies, 1)
        video_layout.addLayout(row2)

        # Row 3: Aspect ratio + Language
        row3 = QHBoxLayout()
        lbl = QLabel("<b>Tỉ lệ:</b>")
        lbl.setMinimumHeight(24)  # Ensure bold text visible
        row3.addWidget(lbl)
        self.cb_ratio = QComboBox()
        self._fix_combobox_height(self.cb_ratio)  # Fix text clipping
        self.cb_ratio.addItems(["16:9", "9:16", "1:1", "4:5", "21:9"])
        row3.addWidget(self.cb_ratio, 1)
        row3.addSpacing(8)
        lbl = QLabel("<b>Ngôn ngữ:</b>")
        lbl.setMinimumHeight(24)  # Ensure bold text visible
        row3.addWidget(lbl)
        self.cb_out_lang = QComboBox()
        self._fix_combobox_height(self.cb_out_lang)  # Fix text clipping
        for name, code in _LANGS:
            self.cb_out_lang.addItem(name, code)
        row3.addWidget(self.cb_out_lang, 1)
        video_layout.addLayout(row3)

        # Row 4: Up Scale 4K
        self.cb_upscale = QCheckBox("Up Scale 4K")
        self.cb_upscale.setStyleSheet("font-size: 12px;")
        video_layout.addWidget(self.cb_upscale)

        # Remove empty space at bottom
        video_layout.addStretch()

        video_layout.addStretch(0)  # Remove bottom space
        colL.addWidget(video_settings_group)

        # VOICE SETTINGS - Collapsible (linked to video for accordion)
        voice_settings_group = CollapsibleGroupBox("🎙️ Cài đặt voice")
        
        # Link them for accordion behavior (only one open at a time)
        video_settings_group._accordion_group = voice_settings_group
        voice_settings_group._accordion_group = video_settings_group
        voice_layout = voice_settings_group.content_layout()

        # Row 1: Provider + Voice
        row1 = QHBoxLayout()
        lbl_provider = QLabel("Provider:")
        lbl_provider.setStyleSheet("font-size: 12px;")
        row1.addWidget(lbl_provider)
        self.cb_tts_provider = QComboBox()
        self.cb_tts_provider.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_tts_provider)  # Fix text clipping
        from services.voice_options import TTS_PROVIDERS
        for provider_id, provider_name in TTS_PROVIDERS:
            self.cb_tts_provider.addItem(provider_name, provider_id)
        row1.addWidget(self.cb_tts_provider, 1)
        row1.addSpacing(8)
        lbl_voice = QLabel("Voice:")
        lbl_voice.setStyleSheet("font-size: 12px;")
        row1.addWidget(lbl_voice)
        self.cb_voice = QComboBox()
        self.cb_voice.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_voice)  # Fix text clipping
        row1.addWidget(self.cb_voice, 1)
        voice_layout.addLayout(row1)

        # Row 2: Custom voice (full width)
        row2 = QHBoxLayout()
        lbl_custom = QLabel("Custom:")
        lbl_custom.setStyleSheet("font-size: 12px;")
        row2.addWidget(lbl_custom)
        self.ed_custom_voice = QLineEdit()
        self.ed_custom_voice.setStyleSheet("font-size: 12px;")
        self.ed_custom_voice.setPlaceholderText("Override voice ID")
        row2.addWidget(self.ed_custom_voice, 1)
        voice_layout.addLayout(row2)

        # Prosody section separator
        lbl_prosody = QLabel("<b>Ngữ điệu:</b>")
        lbl_prosody.setStyleSheet("font-size: 12px;")
        lbl_prosody.setMinimumHeight(24)  # Ensure bold text visible
        voice_layout.addWidget(lbl_prosody)

        # Row 3: Style preset (full width)
        row3 = QHBoxLayout()
        lbl_style = QLabel("Phong cách:")
        lbl_style.setStyleSheet("font-size: 12px;")
        row3.addWidget(lbl_style)
        self.cb_speaking_style = QComboBox()
        self.cb_speaking_style.setStyleSheet("font-size: 12px;")
        self._fix_combobox_height(self.cb_speaking_style)  # Fix text clipping
        # Populate style list from voice_options
        for key, name, desc in get_style_list():
            self.cb_speaking_style.addItem(name, key)
        self.cb_speaking_style.setCurrentIndex(2)  # Default to "storytelling"
        row3.addWidget(self.cb_speaking_style, 1)
        voice_layout.addLayout(row3)

        # Style description (compact)
        self.lbl_style_description = QLabel("Giọng sinh động, có cảm xúc, hấp dẫn")
        self.lbl_style_description.setStyleSheet("font-size: 11px; color: #666;")  # Increased from 10px
        self.lbl_style_description.setMaximumHeight(20)
        self.lbl_style_description.setWordWrap(True)
        voice_layout.addWidget(self.lbl_style_description)

        # Row 4: Rate + Pitch (2 columns)
        row4 = QHBoxLayout()
        lbl_rate_label = QLabel("Tốc độ:")
        lbl_rate_label.setStyleSheet("font-size: 12px;")
        row4.addWidget(lbl_rate_label)
        self.slider_rate = QSlider(Qt.Horizontal)
        self.slider_rate.setRange(50, 200)  # 0.5x to 2.0x
        self.slider_rate.setValue(100)  # Default 1.0x
        self.slider_rate.setTickPosition(QSlider.TicksBelow)
        self.slider_rate.setTickInterval(25)
        row4.addWidget(self.slider_rate, 1)
        self.lbl_rate = QLabel("1.0x")
        self.lbl_rate.setMinimumWidth(45)  # Increased from 40
        self.lbl_rate.setStyleSheet("font-size: 11px;")
        self.lbl_rate.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.lbl_rate)
        row4.addSpacing(8)
        lbl_pitch_label = QLabel("Cao độ:")
        lbl_pitch_label.setStyleSheet("font-size: 12px;")
        row4.addWidget(lbl_pitch_label)
        self.slider_pitch = QSlider(Qt.Horizontal)
        self.slider_pitch.setRange(-5, 5)  # -5st to +5st
        self.slider_pitch.setValue(0)  # Default 0st
        self.slider_pitch.setTickPosition(QSlider.TicksBelow)
        self.slider_pitch.setTickInterval(1)
        row4.addWidget(self.slider_pitch, 1)
        self.lbl_pitch = QLabel("0st")
        self.lbl_pitch.setMinimumWidth(45)  # Increased from 40
        self.lbl_pitch.setStyleSheet("font-size: 11px;")
        self.lbl_pitch.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.lbl_pitch)
        voice_layout.addLayout(row4)

        # Row 5: Expressiveness (full width)
        row5 = QHBoxLayout()
        lbl_expr_label = QLabel("Biểu cảm:")
        lbl_expr_label.setStyleSheet("font-size: 12px;")
        row5.addWidget(lbl_expr_label)
        self.slider_expressiveness = QSlider(Qt.Horizontal)
        self.slider_expressiveness.setRange(0, 100)  # 0.0 to 1.0
        self.slider_expressiveness.setValue(50)  # Default 0.5
        self.slider_expressiveness.setTickPosition(QSlider.TicksBelow)
        self.slider_expressiveness.setTickInterval(10)
        row5.addWidget(self.slider_expressiveness, 1)
        self.lbl_expressiveness = QLabel("0.5")
        self.lbl_expressiveness.setMinimumWidth(45)  # Increased from 40
        self.lbl_expressiveness.setStyleSheet("font-size: 11px;")
        self.lbl_expressiveness.setAlignment(Qt.AlignCenter)
        row5.addWidget(self.lbl_expressiveness)
        voice_layout.addLayout(row5)

        # Checkbox
        self.cb_apply_voice_all = QCheckBox("Áp dụng tất cả cảnh")
        self.cb_apply_voice_all.setChecked(True)
        voice_layout.addWidget(self.cb_apply_voice_all)

        # Remove empty space at bottom
        voice_layout.addStretch()

        voice_layout.addStretch(0)  # Remove bottom space
        colL.addWidget(voice_settings_group)
        
        # Keep download settings for internal use but don't display them
        # These are still needed by the backend
        self.cb_auto_download = QCheckBox()
        self.cb_auto_download.setChecked(True)
        self.cb_auto_download.setVisible(False)
        self.cb_quality = QComboBox()
        self.cb_quality.addItems(["1080p", "720p"])
        self.cb_quality.setVisible(False)
        self.lbl_download_folder = QLabel()
        self.lbl_download_folder.setVisible(False)
        self.btn_change_folder = QPushButton()
        self.btn_change_folder.setVisible(False)

        # Row 6: Single auto button + Stop button (PR#6: Part B #7-8)
        hb = QHBoxLayout()
        self.btn_auto = QPushButton("⚡ Tạo video tự động (3 bước)")
        self.btn_auto.setObjectName("btn_warning")  # Orange color
        self.btn_auto.setMinimumHeight(44)
        self.btn_stop = QPushButton("⏹ Dừng")
        self.btn_stop.setObjectName("btn_gray")  # Gray color
        self.btn_stop.setMaximumWidth(80)
        self.btn_stop.setEnabled(False)
        hb.addWidget(self.btn_auto)
        hb.addWidget(self.btn_stop)
        colL.addLayout(hb)

        self.btn_open_folder = QPushButton("📁 Mở thư mục dự án")
        self.btn_open_folder.setObjectName("btn_primary_open")
        colL.addWidget(self.btn_open_folder)

        colL.addWidget(QLabel("<b>Console:</b>"))
        self.console = QTextEdit(); self.console.setReadOnly(True); self.console.setMinimumHeight(120)
        colL.addWidget(self.console, 0)

        # RIGHT (2/3) - PR#6: Part B #5 - Implement 3 result tabs
        colR = QVBoxLayout(); colR.setSpacing(8)

        # Note: Story/Script view now moved into Tab 1 of result_tabs below

        # Hidden table (legacy)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalHeaderLabels(["Cảnh","Prompt (VI)","Prompt (Đích)","Tỉ lệ","Thời lượng (s)","Xem"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHidden(True); colR.addWidget(self.table, 0)

        # PR#6: Part B #5 - Create result tabs with correct order
        # Tab 1: Script Details, Tab 2: Character Bible, Tab 3: Scene Results, Tab 4: Thumbnail, Tab 5: Social
        from PyQt5.QtWidgets import QTabWidget
        self.result_tabs = QTabWidget()

        # Tab 1: Script Details (Chi tiết kịch bản)
        script_widget = QWidget()
        script_layout = QVBoxLayout(script_widget)
        script_layout.setContentsMargins(4, 4, 4, 4)
        self.view_story = QTextEdit()
        self.view_story.setReadOnly(True)
        self.view_story.setPlaceholderText("Kịch bản chi tiết (Bible + Outline + Screenplay) sẽ hiển thị ở đây sau khi tạo")
        script_layout.addWidget(self.view_story)
        self.result_tabs.addTab(script_widget, "📝 Chi tiết kịch bản")

        # Tab 2: Character Bible (Moved here from standalone section)
        bible_widget = QWidget()
        bible_layout = QVBoxLayout(bible_widget)
        bible_layout.setContentsMargins(8, 8, 8, 8)
        bible_layout.setSpacing(4)

        # Button row with generate button
        bible_btn_row = QHBoxLayout()
        self.btn_generate_bible = QPushButton("✨ Tạo Character Bible")
        self.btn_generate_bible.setObjectName("btn_primary")
        self.btn_generate_bible.setEnabled(False)  # Enabled after script generation
        bible_btn_row.addWidget(self.btn_generate_bible)
        bible_btn_row.addStretch()
        bible_layout.addLayout(bible_btn_row)

        # Character Bible text display
        self.view_bible = QTextEdit()
        self.view_bible.setReadOnly(False)  # Allow editing
        self.view_bible.setAcceptRichText(False)  # Plain text only for consistency
        self.view_bible.setPlaceholderText("Character Bible sẽ hiển thị ở đây sau khi tạo...\n\nCharacter Bible đảm bảo nhân vật có cùng diện mạo và đặc điểm trong tất cả các cảnh.")
        bible_layout.addWidget(self.view_bible)

        self.result_tabs.addTab(bible_widget, "📖 Character Bible")

        # Tab 3: Scene Results (Kết quả cảnh)
        scenes_widget = QWidget()
        scenes_layout = QVBoxLayout(scenes_widget)
        scenes_layout.setContentsMargins(4, 4, 4, 4)
        self.cards = QListWidget()
        self.cards.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards.setIconSize(QSize(240, 135))
        scenes_layout.addWidget(self.cards)
        self.result_tabs.addTab(scenes_widget, "🎬 Kết quả cảnh")

        # Tab 4: Thumbnail
        thumbnail_widget = QWidget()
        thumbnail_layout = QVBoxLayout(thumbnail_widget)
        thumbnail_layout.setContentsMargins(4, 4, 4, 4)
        self.thumbnail_display = QTextEdit()
        self.thumbnail_display.setReadOnly(True)
        self.thumbnail_display.setPlaceholderText("Thumbnail preview sẽ hiển thị ở đây sau khi tạo video")
        thumbnail_layout.addWidget(self.thumbnail_display)
        self.result_tabs.addTab(thumbnail_widget, "📺 Thumbnail")

        # Tab 5: Social
        social_widget = QWidget()
        social_layout = QVBoxLayout(social_widget)
        social_layout.setContentsMargins(4, 4, 4, 4)
        self.social_display = QTextEdit()
        self.social_display.setReadOnly(True)
        self.social_display.setPlaceholderText("Social media content sẽ hiển thị ở đây sau khi tạo kịch bản")
        social_layout.addWidget(self.social_display)
        self.result_tabs.addTab(social_widget, "📱 Social")

        colR.addWidget(self.result_tabs, 1)

        root.addLayout(colL, 1); root.addLayout(colR, 2)  # Left: 1, Right: 2 (balanced)
        self.setMinimumWidth(1000)  # Prevent severe clipping

        # Wire up (PR#4: Updated for new auto button + stop button)
        self.btn_auto.clicked.connect(self._on_auto_generate)
        self.btn_stop.clicked.connect(self.stop_processing)
        self.table.cellDoubleClicked.connect(self._open_prompt_view)
        self.cards.itemDoubleClicked.connect(self._open_card_prompt)
        self.btn_open_folder.clicked.connect(self._open_project_dir)
        self.btn_generate_bible.clicked.connect(self._on_generate_bible)
        self.btn_change_folder.clicked.connect(self._on_change_folder)

        # Voice controls wire up
        self.cb_speaking_style.currentIndexChanged.connect(self._on_speaking_style_changed)
        self.slider_rate.valueChanged.connect(self._on_rate_changed)
        self.slider_pitch.valueChanged.connect(self._on_pitch_changed)
        self.slider_expressiveness.valueChanged.connect(self._on_expressiveness_changed)

        # Domain/Topic cascade
        self.cb_domain.currentIndexChanged.connect(self._on_domain_changed)
        self.cb_topic.currentIndexChanged.connect(self._on_topic_changed)

        # Keep worker reference
        self.worker = None
        self.thread = None

    def _fix_combobox_height(self, combobox):
        """Fix ComboBox text clipping by setting minimum height"""
        combobox.setMinimumHeight(28)  # Ensure full text visible
        # Get existing style and append padding - called once during initialization
        existing_style = combobox.styleSheet()
        if existing_style:
            # Append new QComboBox rule after existing styles
            combobox.setStyleSheet(existing_style + " QComboBox { padding: 4px; }")
        else:
            # No existing styles, add directly
            combobox.setStyleSheet("QComboBox { padding: 4px; }")

    def _render_card_text(self, scene:int):
        st = self._cards_state.get(scene, {})
        vi = st.get('vi','').strip()
        tgt = st.get('tgt','').strip()
        lines = [f'Cảnh {scene}']
        if tgt or vi:
            lines.append('— PROMPT (đích/VI) —')
            if tgt: lines.append(tgt)
            if vi: lines.append(vi)
        vids = st.get('videos', {})
        if vids:
            lines.append('— Video —')
            for copy, info in sorted(vids.items()):
                tag = f"Video {copy}: {info.get('status','?')}"
                if info.get('completed_at'):
                    tag += f" — hoàn tất: {info['completed_at']}"
                if info.get('path'):
                    tag += f"\n📥 {info['path']}"
                elif info.get('url'):
                    tag += f"\n🔗 {info['url']}"
                lines.append(tag)
        return '\n'.join(lines)

    def _apply_styles(self):
        # Fix QGroupBox title visibility
        groupbox_style = """
        QGroupBox {
            font-weight: bold;
            font-size: 13px;
            border: 1px solid #d0d0d0;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 4px 10px;
            left: 10px;
            top: 0px;
        }
        """
        self.setStyleSheet(groupbox_style)

    def _append_log(self, msg):
        self.console.append(msg)

    def stop_processing(self):
        """PR#4: Stop all workers"""
        if self.worker:
            self.worker.should_stop = True
            self._append_log("[INFO] Đang dừng xử lý...")

        self.btn_auto.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_auto_generate(self):
        """PR#4: Auto-generate - runs script generation then video creation"""
        idea = self.ed_idea.toPlainText().strip()
        if not idea:
            QMessageBox.warning(self, "Thiếu thông tin", "Nhập ý tưởng trước.")
            return

        self.btn_auto.setEnabled(False)
        self.btn_stop.setEnabled(True)

        # Step 1: Generate script
        # Get voice settings
        tts_provider = self.cb_tts_provider.currentData()
        voice_id = self.ed_custom_voice.text().strip() or self.cb_voice.currentData()
        
        # Get domain/topic settings
        domain = self.cb_domain.currentData()
        topic = self.cb_topic.currentData()
        
        payload = dict(
            project=self.ed_project.text().strip(),
            idea=idea,
            style=self.cb_style.currentText(),
            duration=int(self.sp_duration.value()),
            provider="Gemini 2.5",
            out_lang_code=self.cb_out_lang.currentData(),
            # Voice settings
            tts_provider=tts_provider,
            voice_id=voice_id,
            # Domain/topic settings
            domain=domain or None,
            topic=topic or None,
        )
        self._append_log("[INFO] Bước 1/3: Sinh kịch bản...")
        self._run_in_thread("script", payload)

    def _on_write_script_clicked(self):
        """Legacy script generation"""
        idea = self.ed_idea.toPlainText().strip()
        if not idea: QMessageBox.warning(self,"Thiếu thông tin","Nhập ý tưởng trước."); return
        payload = dict(
            project=self.ed_project.text().strip(),
            idea=idea, style=self.cb_style.currentText(),
            duration=int(self.sp_duration.value()),
            provider="Gemini 2.5",
            out_lang_code=self.cb_out_lang.currentData()
        )
        self._append_log("[INFO] Yêu cầu sinh kịch bản...")
        self._run_in_thread("script", payload)

    def _on_create_video_clicked(self):
        if self.table.rowCount()<=0: QMessageBox.information(self,"Chưa có kịch bản","Hãy tạo kịch bản trước."); return
        lang_code=self.cb_out_lang.currentData()
        ratio_key=self.cb_ratio.currentText()
        ratio = _ASPECT_MAP.get(ratio_key,"VIDEO_ASPECT_RATIO_LANDSCAPE")
        style=self.cb_style.currentText()
        scenes=[]

        # Part D: Get character bible for injection
        character_bible_basic = self._script_data.get("character_bible", []) if self._script_data else []
        
        # Get voice settings
        voice_settings = self.get_voice_settings()

        for r in range(self.table.rowCount()):
            vi = self.table.item(r,1).text() if self.table.item(r,1) else ""
            tgt= self.table.item(r,2).text() if self.table.item(r,2) else vi

            # Part D: Pass enhanced bible and voice settings to build_prompt_json
            j=build_prompt_json(
                r+1, vi, tgt, lang_code, ratio_key, style,
                character_bible=character_bible_basic,
                enhanced_bible=self._character_bible,
                voice_settings=voice_settings
            )
            scenes.append({"prompt": json.dumps(j, ensure_ascii=False, indent=2), "aspect": ratio})

        model_display = self.cb_model.currentText()
        model_key = get_model_key_from_display(model_display)
        payload=dict(
            scenes=scenes, copies=self._t2v_get_copies(), model_key=model_key,
            title=self._title, dir_videos=self._ctx.get("dir_videos",""),
            upscale_4k=self.cb_upscale.isChecked(),  # PR#4: Use checkbox instead of button
            auto_download=self.cb_auto_download.isChecked(),  # Part D: Auto-download flag
            quality=self.cb_quality.currentText()  # Video quality (1080p/720p)
        )
        if not payload["dir_videos"]:
            st=cfg.load(); root=st.get("download_dir") or ""
            if not root:
                QMessageBox.warning(self,"Thiếu cấu hình","Vào tab Cài đặt để chọn 'Thư mục tải về' trước."); return
            import os; prj=os.path.join(root, self._title or "Project"); os.makedirs(prj, exist_ok=True)
            payload["dir_videos"]=os.path.join(prj,"03_Videos"); os.makedirs(payload["dir_videos"], exist_ok=True)
        self._append_log("[INFO] Bắt đầu tạo video...")
        self._run_in_thread("video", payload)

    def _run_in_thread(self, task, payload):
        # PR#4: Store worker and thread references for stop functionality
        self.thread = QThread(self)
        self.worker = _Worker(task, payload)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.log.connect(self._append_log)
        if task=="script":
            self.worker.story_done.connect(self._on_story_ready)
        else:
            self.worker.job_card.connect(self._on_job_card)
            self.worker.job_finished.connect(lambda: self._on_worker_finished())
        self.thread.start()

    def _on_worker_finished(self):
        """PR#4: Re-enable buttons when worker completes"""
        self._append_log("[INFO] Worker hoàn tất.")
        self.btn_auto.setEnabled(True)
        self.btn_stop.setEnabled(False)

    def _on_story_ready(self, data, ctx):
        self._ctx = ctx
        # title/project
        self._title = self.ed_project.text().strip() or data.get("title_vi") or data.get("title_tgt") or ctx.get("title")
        # show Bible + Outline + Screenplay
        parts=[]
        cb = data.get("character_bible") or []
        if cb:
            parts.append("=== HỒ SƠ NHÂN VẬT ===")
            for c in cb:
                parts.append(f"- {c.get('name','?')} [{c.get('role','?')}]: key_trait={c.get('key_trait','')}; motivation={c.get('motivation','')}; default={c.get('default_behavior','')}; visual={c.get('visual_identity','')}; archetype={c.get('archetype','')}; fatal_flaw={c.get('fatal_flaw','')}")
        ol_vi = data.get("outline_vi","" ).strip()
        if ol_vi: parts.append("\n=== DÀN Ý ===\n"+ol_vi)
        sp_vi = data.get("screenplay_vi","" ).strip()
        sp_tgt = data.get("screenplay_tgt","" ).strip()
        if sp_vi or sp_tgt: parts.append(f"\n=== KỊCH BẢN (VI) ===\n{sp_vi}\n\n=== SCREENPLAY ===\n{sp_tgt}")
        self.view_story.setPlainText("\n\n".join(parts) if parts else "(Không có dữ liệu)")
        self.cards.clear()
        self._cards_state = {}
        for i, sc in enumerate(data.get('scenes', []), 1):
            vi = sc.get('prompt_vi','')
            tgt = sc.get('prompt_tgt','')
            self._cards_state[i] = {'vi': vi, 'tgt': tgt, 'thumb':'', 'videos':{}}
            it = QListWidgetItem(self._render_card_text(i))
            it.setData(Qt.UserRole, ('scene', i))
            self.cards.addItem(it)

        # fill table & save prompts
        self.table.setRowCount(0)
        prdir = ctx.get("dir_prompts","" )
        for i, sc in enumerate(data.get("scenes", []), 1):
            r=self.table.rowCount(); self.table.insertRow(r)
            self.table.setItem(r,0,QTableWidgetItem(str(i)))
            self.table.setItem(r,1,QTableWidgetItem(sc.get("prompt_vi","" )))
            self.table.setItem(r,2,QTableWidgetItem(sc.get("prompt_tgt","" )))
            self.table.setItem(r,3,QTableWidgetItem(self.cb_ratio.currentText()))
            self.table.setItem(r,4,QTableWidgetItem(str(sc.get("duration",8))))
            btn = QPushButton("Xem"); btn.clicked.connect(lambda _=None, row=r: self._open_prompt_view(row))
            self.table.setCellWidget(r,5,btn)
            # save prompt json per scene
            try:
                lang_code=self.cb_out_lang.currentData()
                # Part D: Will be enhanced with bible later when user generates it
                character_bible_basic = data.get("character_bible", [])
                # Get current voice settings
                voice_settings = self.get_voice_settings()
                j=build_prompt_json(
                    i, sc.get("prompt_vi","" ), sc.get("prompt_tgt","" ), lang_code,
                    self.cb_ratio.currentText(), self.cb_style.currentText(),
                    character_bible=character_bible_basic,
                    voice_settings=voice_settings
                )
                if prdir:
                    with open(os.path.join(prdir, f"scene_{i:02d}.json"), "w", encoding="utf-8") as f:
                        json.dump(j, f, ensure_ascii=False, indent=2)
            except Exception: pass
        self._append_log("[INFO] Kịch bản đã hiển thị & lưu file.")

        # Part D: Store script data and enable bible generation button
        self._script_data = data
        self.btn_generate_bible.setEnabled(True)

        # Part D: Auto-generate character bible if exists in data
        cb = data.get("character_bible") or []
        if cb:
            self._generate_character_bible_from_data(data)

        # PR#4: If stop button is enabled (auto mode), automatically start video generation
        if not self.btn_stop.isEnabled():
            # Normal mode - re-enable auto button
            self.btn_auto.setEnabled(True)
        else:
            # Auto mode - proceed to step 2 (video generation)
            self._append_log("[INFO] Bước 2/3: Bắt đầu tạo video...")
            self._on_create_video_clicked()

    def _open_project_dir(self):
        d = self._ctx.get("prj_dir")
        if d and os.path.isdir(d):
            QDesktopServices.openUrl(QUrl.fromLocalFile(d))
        else:
            QMessageBox.information(self,"Chưa có thư mục","Hãy viết kịch bản trước để tạo cấu trúc dự án.")

    def _open_prompt_view(self, row):
        if row<0 or row>=self.table.rowCount(): return
        vi = self.table.item(row,1).text() if self.table.item(row,1) else ""
        tgt= self.table.item(row,2).text() if self.table.item(row,2) else ""
        lang_code=self.cb_out_lang.currentData()
        voice_settings = self.get_voice_settings()
        j=build_prompt_json(row+1, vi, tgt, lang_code, self.cb_ratio.currentText(), self.cb_style.currentText(), voice_settings=voice_settings)
        from ui.prompt_viewer import PromptViewer
        dlg = PromptViewer(json.dumps(j, ensure_ascii=False, indent=2), None, self); dlg.exec_()


    def _on_job_card(self, data:dict):
        scene = int(data.get('scene', 0) or 0)
        copy  = int(data.get('copy', 0) or 0)
        if scene <= 0 or copy <= 0: return
        st = self._cards_state.setdefault(scene, {'vi':'','tgt':'','thumb':'','videos':{}})
        v  = st['videos'].setdefault(copy, {})
        for k in ('status','url','path','thumb','completed_at'):
            if data.get(k): v[k] = data.get(k)
        if data.get('thumb') and os.path.isfile(data['thumb']):
            st['thumb'] = data['thumb']
        for i in range(self.cards.count()):
            it = self.cards.item(i)
            role = it.data(Qt.UserRole)
            if isinstance(role, tuple) and role == ('scene', scene):
                it.setText(self._render_card_text(scene))
                if st.get('thumb') and os.path.isfile(st['thumb']):
                    from PyQt5.QtGui import QIcon, QPixmap
                    pix=QPixmap(st['thumb']).scaled(self.cards.iconSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    it.setIcon(QIcon(pix))
                col = self._t2v_status_color(v.get('status'))
                if col: it.setBackground(col)
                break

    def _t2v_status_color(self, status):
        s = (status or "").upper()
        if s in ("QUEUED","PROCESSING","RENDERING","DOWNLOADING"): return QColor("#36D1BE")
        if s in ("COMPLETED","DOWNLOADED","UPSCALED_4K"): return QColor("#3FD175")
        if s in ("ERROR","FAILED"): return QColor("#ED6D6A")
        return None

    def _t2v_tick(self):
        try:
            self._spin_idx = (self._spin_idx + 1) % len(self._spin_frames)
            if hasattr(self, "table") and self.table is not None:
                rows = self.table.rowCount()
                for r in range(rows):
                    it = self.table.item(r, 3)  # status col
                    if not it:
                        continue
                    status = (it.text() or "").upper()
                    col = self._t2v_status_color(status)
                    if col: it.setBackground(col)
                    if status in ("QUEUED","PROCESSING","RENDERING","DOWNLOADING"):
                        base = status.title()
                        it.setText(base + " " + self._spin_frames[self._spin_idx])
            if hasattr(self, "cards") and self.cards is not None:
                for i in range(self.cards.count()):
                    it = self.cards.item(i)
                    txt = it.text()
                    if any(k in txt for k in ["PROCESSING","RENDERING","DOWNLOADING","QUEUED"]):
                        tail = " " + self._spin_frames[self._spin_idx]
                        if not txt.endswith(tail): it.setText(txt + tail)
        except Exception:
            pass

    def _t2v_get_copies(self):
        # Try common spinbox names; fallback 2
        cand = ["sp_copies","sb_copies","spin_copies","sp_num_videos","spVideos","sp_copies_per_scene"]
        for name in cand:
            try:
                w = getattr(self, name)
                val = int(w.value())
                if val >= 1:
                    return val
            except Exception:
                pass
        return 2

    def _open_card_prompt(self, it):
        try:
            role = it.data(Qt.UserRole)
            scene = None
            if isinstance(role, tuple) and role[0]=='scene':
                scene = int(role[1])
            if not scene:
                return
            st = self._cards_state.get(scene, {})
            txt = st.get('prompt_json','')
            if not txt:
                pr = getattr(self, '_project_root', '')
                if pr:
                    p = os.path.join(pr, '02_Prompts', f'scene_{scene:02d}.json')
                    if os.path.isfile(p):
                        try:
                            txt = open(p,'r',encoding='utf-8').read()
                        except Exception:
                            pass
            if not txt:
                return
            from ui.prompt_viewer import PromptViewer
            dlg = PromptViewer(txt, None, self)
            dlg.exec_()
        except Exception:
            pass

    def _on_generate_bible(self):
        """Part D: Generate detailed character bible"""
        if not self._script_data:
            QMessageBox.warning(self, "Chưa có kịch bản", "Hãy tạo kịch bản trước khi tạo Character Bible.")
            return

        self._append_log("[INFO] Đang tạo Character Bible chi tiết...")
        self._generate_character_bible_from_data(self._script_data)
        self._append_log("[INFO] Character Bible đã tạo xong.")

    def _on_change_folder(self):
        """Change download folder"""
        from PyQt5.QtWidgets import QFileDialog
        st = cfg.load()
        current_dir = st.get("download_root") or os.path.expanduser("~/Downloads")

        folder = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục tải video",
            current_dir,
            QFileDialog.ShowDirsOnly
        )

        if folder:
            # Update config
            st["download_root"] = folder
            cfg.save(st)
            # Update label
            self._update_folder_label(folder)
            self._append_log(f"[INFO] Đã đổi thư mục tải về: {folder}")

    def _update_folder_label(self, folder_path=None):
        """Update folder label display"""
        if not folder_path:
            st = cfg.load()
            folder_path = st.get("download_root") or "Chưa đặt"

        # Truncate long paths
        if len(folder_path) > 40:
            folder_path = "..." + folder_path[-37:]

        self.lbl_download_folder.setText(f"Thư mục: {folder_path}")

    def _generate_character_bible_from_data(self, data):
        """Part D: Generate character bible from script data"""
        try:
            from services.google.character_bible import (
                create_character_bible,
                format_character_bible_for_display,
            )

            # Get components
            video_concept = self.ed_idea.toPlainText().strip()
            screenplay = data.get("screenplay_tgt", "") or data.get("screenplay_vi", "")
            existing_bible = data.get("character_bible", [])

            # Create detailed bible
            self._character_bible = create_character_bible(video_concept, screenplay, existing_bible)

            # Display in UI
            formatted = format_character_bible_for_display(self._character_bible)
            self.view_bible.setPlainText(formatted)

            # Save to file
            if self._ctx.get("dir_script"):
                bible_path = os.path.join(self._ctx["dir_script"], "character_bible_detailed.json")
                try:
                    with open(bible_path, "w", encoding="utf-8") as f:
                        f.write(self._character_bible.to_json())
                    self._append_log(f"[INFO] Character Bible đã lưu: {bible_path}")
                except (IOError, OSError) as e:
                    self._append_log(f"[WARN] Không thể lưu Character Bible: {type(e).__name__}: {e}")
                except Exception as e:
                    self._append_log(f"[WARN] Lỗi không xác định khi lưu Character Bible: {type(e).__name__}: {e}")

        except Exception as e:
            self._append_log(f"[ERR] Lỗi tạo Character Bible: {e}")
            QMessageBox.warning(self, "Lỗi", f"Không thể tạo Character Bible: {e}")

    def _on_speaking_style_changed(self):
        """Handle speaking style preset change"""
        style_key = self.cb_speaking_style.currentData()
        if not style_key:
            return
        
        # Update description
        style_info = get_style_info(style_key)
        self.lbl_style_description.setText(style_info["description"])
        
        # Update sliders to match preset
        style_config = SPEAKING_STYLES[style_key]
        
        # Rate preset mapping: slow=75, medium=100, fast=125
        rate_map = {"slow": 75, "medium": 100, "fast": 125}
        preset_rate = rate_map.get(style_config["google_tts"]["rate"], 100)
        self.slider_rate.setValue(preset_rate)
        
        # Pitch preset extraction
        pitch_str = style_config["google_tts"]["pitch"]
        match = re.match(r'([+-]?\d+)st', pitch_str)
        preset_pitch = int(match.group(1)) if match else 0
        self.slider_pitch.setValue(preset_pitch)
        
        # Expressiveness from ElevenLabs style
        preset_expr = int(style_config["elevenlabs"]["style"] * 100)
        self.slider_expressiveness.setValue(preset_expr)

    def _on_rate_changed(self, value):
        """Handle speaking rate slider change"""
        # Convert slider value (50-200) to multiplier (0.5-2.0)
        multiplier = value / 100.0
        self.lbl_rate.setText(f"{multiplier:.1f}x")

    def _on_pitch_changed(self, value):
        """Handle pitch slider change"""
        # Display semitones
        if value > 0:
            self.lbl_pitch.setText(f"+{value}st")
        elif value < 0:
            self.lbl_pitch.setText(f"{value}st")
        else:
            self.lbl_pitch.setText("0st")

    def _on_expressiveness_changed(self, value):
        """Handle expressiveness slider change"""
        # Convert slider value (0-100) to decimal (0.0-1.0)
        decimal = value / 100.0
        self.lbl_expressiveness.setText(f"{decimal:.1f}")

    def _on_domain_changed(self):
        """Handle domain selection - load topics"""
        domain = self.cb_domain.currentData()
        self.cb_topic.clear()
        self.cb_topic.addItem("(Chọn lĩnh vực để load chủ đề)", "")
        # Preview removed - no action needed
        
        if not domain:
            self.cb_topic.setEnabled(False)
            return
        
        try:
            from services.domain_prompts import get_topics_for_domain
            topics = get_topics_for_domain(domain)
            if topics:
                self.cb_topic.clear()
                self.cb_topic.addItem("(Chọn chủ đề)", "")
                for topic in topics:
                    self.cb_topic.addItem(topic, topic)
                self.cb_topic.setEnabled(True)
        except Exception as e:
            self._append_log(f"[ERR] {e}")
            self.cb_topic.setEnabled(False)
    
    def _on_topic_changed(self):
        """Handle topic selection - show preview"""
        domain = self.cb_domain.currentData()
        topic = self.cb_topic.currentData()
        # Preview removed - no action needed
        
        if domain and topic:
            try:
                from services.domain_prompts import get_system_prompt
                prompt = get_system_prompt(domain, topic)
                if prompt:
                    preview = prompt[:200] + "..."
                    # Preview removed - content not displayed
            except Exception as e:
                self._append_log(f"[ERR] {e}")
    
    def get_voice_settings(self):
        """Get current voice settings for video generation
        
        Returns:
            Dictionary with voice prosody settings
        """
        style_key = self.cb_speaking_style.currentData() or "storytelling"
        rate_multiplier = self.slider_rate.value() / 100.0
        pitch_adjust = self.slider_pitch.value()
        expressiveness = self.slider_expressiveness.value() / 100.0
        apply_all = self.cb_apply_voice_all.isChecked()
        
        return {
            "speaking_style": style_key,
            "rate_multiplier": rate_multiplier,
            "pitch_adjust": pitch_adjust,
            "expressiveness": expressiveness,
            "apply_to_all_scenes": apply_all
        }
