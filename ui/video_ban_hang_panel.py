# -*- coding: utf-8 -*-
"""
Video Bán Hàng Panel - Redesigned with 3-step workflow
FIXED: Removed QSS autoload block to prevent theme conflicts
"""
import datetime
import math
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from services import image_gen_service
from services import sales_script_service as sscript
from services import sales_video_service as svc
from ui.widgets.model_selector import ModelSelectorWidget
from ui.widgets.scene_result_card import SceneResultCard
from ui.workers.script_worker import ScriptWorker
from utils.image_utils import convert_to_bytes

# Fonts
FONT_LABEL = QFont()
FONT_LABEL.setPixelSize(13)
FONT_INPUT = QFont()
FONT_INPUT.setPixelSize(12)

# Sizes
THUMBNAIL_SIZE = 72
MODEL_IMG = 128

# Rate limiting
RATE_LIMIT_DELAY_SEC = 10.0  # Delay between image generation requests to avoid 429 errors


class SceneCardWidget(QFrame):
    """Scene card widget with image preview and action buttons"""

    def __init__(self, scene_data, parent=None):
        super().__init__(parent)
        self.scene_data = scene_data
        self.image_label = None
        self._build_ui()

    def _build_ui(self):
        """Build the scene card UI - using unified theme"""
        # Styling handled by unified theme

        layout = QHBoxLayout(self)

        # Preview image
        self.image_label = QLabel()
        self.image_label.setFixedSize(320, 180)  # 16:9 preview
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText("Chưa tạo")
        layout.addWidget(self.image_label)

        # Info and buttons section
        info_layout = QVBoxLayout()

        # Title
        title = QLabel(f"Cảnh {self.scene_data.get('index')}")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        info_layout.addWidget(title)

        # Description
        desc_text = self.scene_data.get("desc", "")
        if len(desc_text) > 150:
            desc_text = desc_text[:150] + "..."
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        info_layout.addWidget(desc)

        # Speech text
        speech_text = self.scene_data.get("speech", "")
        if len(speech_text) > 100:
            speech_text = speech_text[:100] + "..."
        speech = QLabel(f"🎤 {speech_text}")
        speech.setWordWrap(True)
        speech.setFont(QFont("Segoe UI", 11))
        info_layout.addWidget(speech)

        info_layout.addStretch(1)

        # Action buttons
        btn_layout = QHBoxLayout()

        # Prompt button
        btn_prompt = QPushButton("📝 Prompt ảnh/video")
        btn_prompt.setObjectName("btn_info_prompt")
        btn_prompt.clicked.connect(self._show_prompts)
        btn_layout.addWidget(btn_prompt)

        # Regenerate button
        btn_regen = QPushButton("🔄 Tạo lại")
        btn_regen.setObjectName("btn_warning_regen")
        btn_layout.addWidget(btn_regen)

        # Video button
        btn_video = QPushButton("🎬 Video")
        btn_video.setObjectName("btn_primary_video")
        btn_layout.addWidget(btn_video)

        info_layout.addLayout(btn_layout)

        layout.addLayout(info_layout, 1)

    def _show_prompts(self):
        """Show prompt dialog with image and video prompts"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Prompts - Cảnh {self.scene_data.get('index')}")
        dialog.setFixedSize(700, 500)

        layout = QVBoxLayout(dialog)

        # Image prompt section
        lbl_img = QLabel("📷 Prompt Ảnh:")
        layout.addWidget(lbl_img)

        ed_img_prompt = QTextEdit()
        ed_img_prompt.setReadOnly(True)
        ed_img_prompt.setPlainText(self.scene_data.get("prompt_image", ""))
        ed_img_prompt.setMaximumHeight(180)
        layout.addWidget(ed_img_prompt)

        btn_copy_img = QPushButton("📋 Copy Prompt Ảnh")
        btn_copy_img.setObjectName("btn_info_copy")
        btn_copy_img.clicked.connect(
            lambda: self._copy_to_clipboard(self.scene_data.get("prompt_image", ""))
        )
        layout.addWidget(btn_copy_img)

        # Video prompt section
        lbl_vid = QLabel("🎬 Prompt Video:")
        layout.addWidget(lbl_vid)

        ed_vid_prompt = QTextEdit()
        ed_vid_prompt.setReadOnly(True)
        ed_vid_prompt.setPlainText(self.scene_data.get("prompt_video", ""))
        ed_vid_prompt.setMaximumHeight(180)
        layout.addWidget(ed_vid_prompt)

        btn_copy_vid = QPushButton("📋 Copy Prompt Video")
        btn_copy_vid.setObjectName("btn_info_copy_vid")
        btn_copy_vid.clicked.connect(
            lambda: self._copy_to_clipboard(self.scene_data.get("prompt_video", ""))
        )
        layout.addWidget(btn_copy_vid)

        # Close button
        btn_close = QPushButton("✖ Đóng")
        btn_close.setObjectName("btn_primary_close")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)

        dialog.exec_()

    def _copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Thành công", "Đã copy vào clipboard!")

    def set_image(self, pixmap):
        """Set the preview image"""
        if self.image_label:
            self.image_label.setPixmap(
                pixmap.scaled(320, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )


class ImageGenerationWorker(QThread):
    """Worker thread for generating images (scenes + thumbnails)"""

    progress = pyqtSignal(str)
    scene_image_ready = pyqtSignal(int, bytes)
    thumbnail_ready = pyqtSignal(int, bytes)
    finished = pyqtSignal(bool)

    def __init__(self, outline, cfg, model_paths, prod_paths, use_whisk=False, character_bible=None):
        super().__init__()
        self.outline = outline
        self.cfg = cfg
        self.model_paths = model_paths
        self.prod_paths = prod_paths
        self.use_whisk = use_whisk
        self.character_bible = character_bible
        self.should_stop = False

    def run(self):
        try:
            # Get API keys and settings from config
            from services.core.config import load as load_cfg
            cfg_data = load_cfg()
            api_keys = cfg_data.get('google_api_keys', [])

            if not api_keys:
                self.progress.emit("[ERROR] Không có Google API keys trong config")
                self.finished.emit(False)
                return

            # Get aspect ratio and model from config
            aspect_ratio = self.cfg.get('ratio', '9:16')
            model = 'gemini' if 'Gemini' in self.cfg.get('image_model', 'Gemini') else 'imagen_4'

            self.progress.emit(f"[INFO] Sử dụng {len(api_keys)} API keys, model: {model}, tỷ lệ: {aspect_ratio}")
            
            # Log character bible usage
            if self.character_bible and hasattr(self.character_bible, 'characters'):
                char_count = len(self.character_bible.characters)
                if char_count > 0:
                    self.progress.emit(f"[CHARACTER BIBLE] Injecting consistency anchors for {char_count} character(s)")
            
            # Generate scene images
            scenes = self.outline.get("scenes", [])
            for i, scene in enumerate(scenes):
                if self.should_stop:
                    break

                # CRITICAL FIX: Add mandatory delay BEFORE every request (except first)
                # This prevents rate limiting regardless of which key is used
                if i > 0:
                    self.progress.emit(
                        f"[RATE LIMIT] Chờ {RATE_LIMIT_DELAY_SEC}s trước khi tạo ảnh cảnh {scene.get('index')}..."
                    )
                    time.sleep(RATE_LIMIT_DELAY_SEC)

                self.progress.emit(f"Tạo ảnh cảnh {scene.get('index')}...")

                # Get prompt
                prompt = scene.get("prompt_image", "")
                
                # Inject character consistency if available
                if self.character_bible and hasattr(self.character_bible, 'characters'):
                    try:
                        from services.google.character_bible import inject_character_consistency
                        prompt = inject_character_consistency(prompt, self.character_bible)
                        self.progress.emit(f"[CHARACTER BIBLE] Injected consistency anchors into scene {scene.get('index')}")
                    except Exception as e:
                        self.progress.emit(f"[WARNING] Failed to inject character consistency: {e}")

                # Try to generate image
                img_data = None
                if self.use_whisk and self.model_paths and self.prod_paths:
                    # Try Whisk first
                    try:
                        from services import whisk_service

                        img_data = whisk_service.generate_image(
                            prompt=prompt,
                            model_image=self.model_paths[0] if self.model_paths else None,
                            product_image=self.prod_paths[0] if self.prod_paths else None,
                            debug_callback=self.progress.emit,
                        )
                        if img_data:
                            self.progress.emit(f"Cảnh {scene.get('index')}: Whisk ✓")
                    except Exception as e:
                        self.progress.emit(f"Whisk failed: {str(e)[:100]}")
                        img_data = None

                # Fallback to Gemini with rate limiting
                if img_data is None:
                    try:
                        self.progress.emit(f"Cảnh {scene.get('index')}: Dùng Gemini...")

                        # Use rate-limited generation with API key rotation
                        img_data_url = image_gen_service.generate_image_with_rate_limit(
                            text=prompt,  # Fixed: 'prompt' → 'text'
                            api_keys=api_keys,
                            model=model,
                            aspect_ratio=aspect_ratio,
                            delay_before=0,
                            logger=lambda msg: self.progress.emit(msg),
                        )

                        if img_data_url:
                            # Convert to bytes, handling both formats
                            img_data, error = convert_to_bytes(img_data_url)
                            if img_data:
                                self.progress.emit(f"Cảnh {scene.get('index')}: Gemini ✓")
                            else:
                                self.progress.emit(f"Cảnh {scene.get('index')}: {error}")
                        else:
                            self.progress.emit(f"Cảnh {scene.get('index')}: Không tạo được ảnh")
                            img_data = None
                    except Exception as e:
                        self.progress.emit(f"Gemini failed for scene {scene.get('index')}: {e}")
                        img_data = None

                if img_data:
                    self.scene_image_ready.emit(scene.get("index"), img_data)

            # Generate social media thumbnails
            social_media = self.outline.get("social_media", {})
            versions = social_media.get("versions", [])

            for i, version in enumerate(versions):
                if self.should_stop:
                    break

                # CRITICAL FIX: Delay before thumbnails too
                # First thumbnail comes after all scene images, so always delay
                self.progress.emit(
                    f"[RATE LIMIT] Chờ {RATE_LIMIT_DELAY_SEC}s trước thumbnail {i+1}..."
                )
                time.sleep(RATE_LIMIT_DELAY_SEC)

                self.progress.emit(f"Tạo thumbnail phiên bản {i+1}...")

                prompt = version.get("thumbnail_prompt", "")
                text_overlay = version.get("thumbnail_text_overlay", "")

                try:
                    # Use rate-limited generation with API key rotation
                    thumb_data_url = image_gen_service.generate_image_with_rate_limit(
                        text=prompt,  # Fixed: 'prompt' → 'text'
                        api_keys=api_keys,
                        model=model,
                        aspect_ratio=aspect_ratio,
                        delay_before=0,
                        logger=lambda msg: self.progress.emit(msg)
                    )

                    if thumb_data_url:
                        # Convert to bytes, handling both formats
                        thumb_data, error = convert_to_bytes(thumb_data_url)
                        
                        if thumb_data:
                            import tempfile

                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                                tmp.write(thumb_data)
                                tmp_path = tmp.name

                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_out:
                                out_path = tmp_out.name

                            sscript.generate_thumbnail_with_text(tmp_path, text_overlay, out_path)

                            with open(out_path, "rb") as f:
                                final_thumb = f.read()

                            os.unlink(tmp_path)
                            os.unlink(out_path)

                            self.thumbnail_ready.emit(i, final_thumb)
                            self.progress.emit(f"Thumbnail {i+1}: ✓")
                        else:
                            self.progress.emit(f"Thumbnail {i+1}: {error}")
                    else:
                        self.progress.emit(f"Thumbnail {i+1}: Không tạo được")

                except Exception as e:
                    self.progress.emit(f"Thumbnail {i+1} lỗi: {e}")

            self.finished.emit(True)

        except Exception as e:
            self.progress.emit(f"Lỗi: {e}")
            self.finished.emit(False)

    def stop(self):
        self.should_stop = True


class VideoBanHangPanel(QWidget):
    """Redesigned Video Bán Hàng panel with 3-step workflow + cache system"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.prod_paths = []
        self.last_outline = None
        self.scene_images = {}
        self.thumbnail_images = {}
        self.character_bible = None  # Store character bible object

        # Cache system to persist data across workflow steps
        self.cache = {
            "outline": None,
            "scene_images": {},
            "scene_prompts": {},
            "thumbnails": {},
            "character_bible": None,
        }
        
        # Initialize download settings (moved to Settings tab, but keep for compatibility)
        self.chk_auto_download = None
        self.ed_download_path = None

        self._build_ui()

    def _build_ui(self):
        """Build the 2-column UI"""
        # Main layout: Left column (400px) + Right area
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # LEFT COLUMN - EXACTLY 480px (was 400px, +80px for better spacing)
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(460)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self._build_left_column(left_layout)

        main_layout.addWidget(self.left_widget)

        # RIGHT AREA - Takes remaining space
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self._build_right_column(right_layout)

        main_layout.addWidget(self.right_widget, 1)

    def _build_left_column(self, layout):
        """Build left column with fixed project info and collapsible sections"""
        
        # ===== FIXED SECTION (Always Visible) =====
        
        # Project name - Full width, no truncation
        lbl_proj = QLabel("📁 Dự án")
        lbl_proj.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(lbl_proj)
        
        lbl_name = QLabel("Tên dự án:")
        lbl_name.setFont(QFont("Segoe UI", 11))
        layout.addWidget(lbl_name)
        
        self.ed_name = QLineEdit()
        self.ed_name.setFont(QFont("Segoe UI", 13))
        self.ed_name.setPlaceholderText("Nhập tên dự án...")
        self.ed_name.setText(svc.default_project_name())
        self.ed_name.setMinimumHeight(42)
        layout.addWidget(self.ed_name)
        
        # Idea input - 3 fixed lines, 13px
        lbl_idea = QLabel("Ý tưởng:")
        lbl_idea.setFont(QFont("Segoe UI", 11))
        layout.addWidget(lbl_idea)
        
        self.ed_idea = QTextEdit()
        self.ed_idea.setFont(QFont("Segoe UI", 13))
        self.ed_idea.setPlaceholderText("Nhập ý tưởng cho video...")
        self.ed_idea.setFixedHeight(80)  # ~3 lines at 13px
        layout.addWidget(self.ed_idea)
        
        # Content input - 10 fixed lines, 13px
        lbl_content = QLabel("Nội dung:")
        lbl_content.setFont(QFont("Segoe UI", 11))
        layout.addWidget(lbl_content)
        
        self.ed_product = QTextEdit()
        self.ed_product.setFont(QFont("Segoe UI", 13))
        self.ed_product.setPlaceholderText("Nhập nội dung chi tiết...")
        self.ed_product.setFixedHeight(130)  # 6 lines at 13px font  # ~10 lines at 13px
        layout.addWidget(self.ed_product)
        
        layout.addSpacing(16)

        # ===== COLLAPSIBLE SECTIONS (Accordion) =====
        
        # Model section
        self.gb_model = self._create_collapsible_group("👤 Thông tin người mẫu")
        self.gb_model.setCheckable(True)
        self.gb_model.setChecked(False)  # Collapsed by default
        self.gb_model.toggled.connect(lambda checked: self._on_section_toggled(self.gb_model, checked))
        
        # Create container widget for model section
        self._model_container = QWidget()
        model_content_layout = QVBoxLayout(self._model_container)
        model_content_layout.setContentsMargins(0, 0, 0, 0)
        model_content_layout.setSpacing(4)  # Tight spacing
        
        # Model selector widget
        self.model_selector = ModelSelectorWidget(title="")
        model_content_layout.addWidget(self.model_selector)
        

        
        # Wrap container in GroupBox layout
        model_layout = QVBoxLayout()
        model_layout.addWidget(self._model_container)
        self._model_container.setVisible(False)  # Hidden by default
        
        self.gb_model.setLayout(model_layout)
        layout.addWidget(self.gb_model)

        # Product images section
        self.gb_products = self._create_collapsible_group("📦 Ảnh sản phẩm")
        self.gb_products.setCheckable(True)
        self.gb_products.setChecked(False)
        self.gb_products.toggled.connect(lambda checked: self._on_section_toggled(self.gb_products, checked))
        
        # Create container widget
        self._products_container = QWidget()
        prod_content_layout = QVBoxLayout(self._products_container)
        prod_content_layout.setContentsMargins(0, 0, 0, 0)
        
        btn_prod = QPushButton("📁 Chọn ảnh sản phẩm")
        btn_prod.setObjectName("btn_primary")
        btn_prod.setMinimumHeight(32)
        btn_prod.clicked.connect(self._pick_product_images)
        prod_content_layout.addWidget(btn_prod)
        
        self.prod_thumb_container = QHBoxLayout()
        self.prod_thumb_container.setSpacing(4)
        prod_content_layout.addLayout(self.prod_thumb_container)
        
        # Wrap in GroupBox layout
        prod_layout = QVBoxLayout()
        prod_layout.addWidget(self._products_container)
        self._products_container.setVisible(False)  # Hidden by default
        
        self.gb_products.setLayout(prod_layout)
        layout.addWidget(self.gb_products)

        # Video settings section
        self.gb_settings = self._create_collapsible_group("⚙️ Cài đặt video")
        self.gb_settings.setCheckable(True)
        self.gb_settings.setChecked(False)
        self.gb_settings.toggled.connect(lambda checked: self._on_section_toggled(self.gb_settings, checked))
        
        # Create container widget for settings
        self._settings_container = QWidget()
        settings_content_layout = QVBoxLayout(self._settings_container)
        settings_content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Settings form using QGridLayout for 2-column layout
        form = QGridLayout()
        form.setSpacing(8)
        form.setColumnMinimumWidth(0, 110)  # Label column 1
        form.setColumnMinimumWidth(2, 110)  # Label column 2
        form.setColumnStretch(1, 1)  # Value column 1
        form.setColumnStretch(3, 1)  # Value column 2
        
        def make_widget(widget_class, **kwargs):
            w = widget_class()
            w.setMinimumHeight(32)
            for k, v in kwargs.items():
                if hasattr(w, k):
                    getattr(w, k)(v) if callable(getattr(w, k)) else setattr(w, k, v)
            return w
        
        # Row 0: Style columns
        self.cb_style = make_widget(QComboBox)
        self.cb_style.addItems(["Viral", "KOC Review", "Kể chuyện"])
        form.addWidget(QLabel("Kịch bản:"), 0, 0)
        form.addWidget(self.cb_style, 0, 1)
        
        self.cb_imgstyle = make_widget(QComboBox)
        self.cb_imgstyle.addItems(["Điện ảnh", "Hiện đại/Trendy", "Anime", "Hoạt hình 3D"])
        form.addWidget(QLabel("Hình ảnh:"), 0, 3)
        form.addWidget(self.cb_imgstyle, 0, 4)
        
        # Row 1: Model columns
        self.cb_script_model = make_widget(QComboBox)
        self.cb_script_model.addItems(["Gemini", "ChatGPT"])
        form.addWidget(QLabel("Model KB:"), 1, 0)
        form.addWidget(self.cb_script_model, 1, 1)
        
        self.cb_image_model = make_widget(QComboBox)
        self.cb_image_model.addItems(["Gemini", "Whisk"])
        form.addWidget(QLabel("Tạo ảnh:"), 1, 3)
        form.addWidget(self.cb_image_model, 1, 4)
        
        # Row 2: Voice | Language
        self.ed_voice = make_widget(QLineEdit)
        self.ed_voice.setPlaceholderText("ElevenLabs VoiceID")
        form.addWidget(QLabel("Lời thoại:"), 2, 0)
        form.addWidget(self.ed_voice, 2, 1)
        
        self.cb_lang = make_widget(QComboBox)
        LANGUAGES = [
            "Tiếng Việt",
            "Tiếng Anh",
            "Tiếng Trung - Giản thể",
            "Tiếng Trung - Phồn thể",
            "Tiếng Nhật",
            "Tiếng Hàn",
            "Tiếng Thái",
            "Tiếng Indonesia",
            "Tiếng Mã Lai",
            "Tiếng Tagalog",
            "Tiếng Pháp",
            "Tiếng Đức",
            "Tiếng Tây Ban Nha",
            "Tiếng Bồ Đào Nha",
            "Tiếng Ý",
            "Tiếng Nga",
            "Tiếng Ả Rập",
            "Tiếng Hindi",
            "Tiếng Bengal",
            "Tiếng Punjab",
            "Tiếng Thổ Nhĩ Kỳ",
            "Tiếng Ba Lan",
            "Tiếng Ukraina",
            "Tiếng Hà Lan",
            "Tiếng Thụy Điển",
            "Tiếng Na Uy",
        ]
        self.cb_lang.addItems(LANGUAGES)
        
        # Mapping dictionary to convert display names to language codes
        self.LANGUAGE_MAP = {
            "Tiếng Việt": "vi",
            "Tiếng Anh": "en",
            "Tiếng Trung - Giản thể": "zh-CN",
            "Tiếng Trung - Phồn thể": "zh-TW",
            "Tiếng Nhật": "ja",
            "Tiếng Hàn": "ko",
            "Tiếng Thái": "th",
            "Tiếng Indonesia": "id",
            "Tiếng Mã Lai": "ms",
            "Tiếng Tagalog": "tl",
            "Tiếng Pháp": "fr",
            "Tiếng Đức": "de",
            "Tiếng Tây Ban Nha": "es",
            "Tiếng Bồ Đào Nha": "pt",
            "Tiếng Ý": "it",
            "Tiếng Nga": "ru",
            "Tiếng Ả Rập": "ar",
            "Tiếng Hindi": "hi",
            "Tiếng Bengal": "bn",
            "Tiếng Punjab": "pa",
            "Tiếng Thổ Nhĩ Kỳ": "tr",
            "Tiếng Ba Lan": "pl",
            "Tiếng Ukraina": "uk",
            "Tiếng Hà Lan": "nl",
            "Tiếng Thụy Điển": "sv",
            "Tiếng Na Uy": "no",
        }
        form.addWidget(QLabel("Ngôn ngữ:"), 2, 3)
        form.addWidget(self.cb_lang, 2, 4)
        
        # Row 3: Duration | Videos
        self.sp_duration = make_widget(QSpinBox)
        self.sp_duration.setRange(8, 1200)
        self.sp_duration.setSingleStep(8)
        self.sp_duration.setValue(32)
        self.sp_duration.setSuffix(" s")
        self.sp_duration.valueChanged.connect(self._update_scenes)
        form.addWidget(QLabel("Thời lượng:"), 3, 0)
        form.addWidget(self.sp_duration, 3, 1)
        
        self.sp_videos = make_widget(QSpinBox)
        self.sp_videos.setRange(1, 4)
        self.sp_videos.setValue(1)
        form.addWidget(QLabel("Số vid/cảnh:"), 3, 3)
        form.addWidget(self.sp_videos, 3, 4)
        
        # Row 4: Ratio | Platform
        self.cb_ratio = make_widget(QComboBox)
        self.cb_ratio.addItems(["9:16", "16:9", "1:1", "4:5"])
        form.addWidget(QLabel("Tỉ lệ:"), 4, 0)
        form.addWidget(self.cb_ratio, 4, 1)
        
        self.cb_social = make_widget(QComboBox)
        self.cb_social.addItems(["TikTok", "Facebook", "YouTube"])
        form.addWidget(QLabel("Nền tảng:"), 4, 3)
        form.addWidget(self.cb_social, 4, 4)
        
        settings_content_layout.addLayout(form)
        
        
        # Wrap container in GroupBox layout
        settings_layout = QVBoxLayout()
        settings_layout.addWidget(self._settings_container)
        self._settings_container.setVisible(False)  # Hidden by default
        
        self.gb_settings.setLayout(settings_layout)
        layout.addWidget(self.gb_settings)

        # NOTE: REMOVED "💾 Tự động tải" section - use Settings tab instead
        
        layout.addStretch()

        # Action buttons at bottom of left column
        self._build_action_buttons(layout)

        self._update_scenes()

    def _build_right_column(self, layout):
        """Build right column with results tabs"""

        # Tab widget
        self.results_tabs = QTabWidget()

        # Tab 1: Scenes
        scenes_tab = self._build_scenes_tab()
        self.results_tabs.addTab(scenes_tab, "🎬 Cảnh")

        # Tab 2: Character Bible
        character_bible_tab = self._build_character_bible_tab()
        self.results_tabs.addTab(character_bible_tab, "👤 Character Bible")

        # Tab 3: Thumbnail
        thumbnail_tab = self._build_thumbnail_tab()
        self.results_tabs.addTab(thumbnail_tab, "📺 Thumbnail")

        # Tab 4: Social
        social_tab = self._build_social_tab()
        self.results_tabs.addTab(social_tab, "📱 Social")

        layout.addWidget(self.results_tabs, 1)

        # Log area (compact)
        gb_log = QGroupBox("Nhật ký xử lý")
        lv = QVBoxLayout(gb_log)
        self.ed_log = QPlainTextEdit()
        self.ed_log.setFont(FONT_INPUT)
        self.ed_log.setReadOnly(True)
        self.ed_log.setMaximumHeight(80)
        lv.addWidget(self.ed_log)
        layout.addWidget(gb_log)

    def _build_action_buttons(self, layout):
        """Build action buttons at bottom of left column"""

        # === ROW 1: Workflow Buttons (Viết/Tạo/Video) - Horizontal ===
        workflow_row = QHBoxLayout()
        workflow_row.setSpacing(6)

        self.btn_script = QPushButton("📝 Viết kịch bản")
        self.btn_script.setMinimumHeight(42)
        self.btn_script.setStyleSheet(
            """
            QPushButton {
                background-color: #FF6B2C;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #F4511E; }
        """
        )
        self.btn_script.clicked.connect(self._on_write_script)

        self.btn_images = QPushButton("🎨 Tạo ảnh")
        self.btn_images.setMinimumHeight(42)
        self.btn_images.setEnabled(False)
        self.btn_images.setStyleSheet(
            """
            QPushButton {
                background-color: #FF6B2C;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #F4511E; }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """
        )
        self.btn_images.clicked.connect(self._on_generate_images)

        self.btn_video = QPushButton("🎬 Video")
        self.btn_video.setMinimumHeight(42)
        self.btn_video.setEnabled(False)
        self.btn_video.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #388E3C; }
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """
        )
        self.btn_video.clicked.connect(self._on_generate_video)

        workflow_row.addWidget(self.btn_script)
        workflow_row.addWidget(self.btn_images)
        workflow_row.addWidget(self.btn_video)

        layout.addLayout(workflow_row)

        # === ROW 2: Auto + Stop Buttons - Horizontal ===
        auto_row = QHBoxLayout()
        auto_row.setSpacing(6)

        self.btn_auto = QPushButton("⚡ Tạo video tự động (3 bước)")
        self.btn_auto.setMinimumHeight(42)
        self.btn_auto.setStyleSheet(
            """
            QPushButton {
                background-color: #FF6B2C;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #F4511E; }
        """
        )
        self.btn_auto.clicked.connect(self._on_auto_workflow)

        self.btn_stop = QPushButton("⏹️ Dừng")
        self.btn_stop.setMinimumHeight(42)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(
            """
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #D32F2F; }
            QPushButton:disabled {
                background-color: #FFCDD2;
                color: #BDBDBD;
            }
        """
        )
        self.btn_stop.clicked.connect(self.stop_processing)

        auto_row.addWidget(self.btn_auto, 3)  # 75% width
        auto_row.addWidget(self.btn_stop, 1)  # 25% width

        layout.addLayout(auto_row)

    def _build_scenes_tab(self):
        """Build scenes tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        self.scenes_layout = QVBoxLayout(container)
        self.scenes_layout.setContentsMargins(16, 16, 16, 16)
        self.scenes_layout.setSpacing(0)

        self.scene_cards = []

        self.scenes_layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_character_bible_tab(self):
        """Build Character Bible tab"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header with title and buttons
        header_layout = QHBoxLayout()
        
        title_label = QLabel("📖 Character Bible - Visual Consistency System")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Regenerate button
        self.btn_regen_bible = QPushButton("🔄 Regenerate")
        self.btn_regen_bible.setObjectName("btn_warning_regen")
        self.btn_regen_bible.setMinimumHeight(32)
        self.btn_regen_bible.setEnabled(False)
        self.btn_regen_bible.clicked.connect(self._regenerate_character_bible)
        header_layout.addWidget(self.btn_regen_bible)
        
        # Copy button
        self.btn_copy_bible = QPushButton("📋 Copy Summary")
        self.btn_copy_bible.setObjectName("btn_info_copy")
        self.btn_copy_bible.setMinimumHeight(32)
        self.btn_copy_bible.setEnabled(False)
        self.btn_copy_bible.clicked.connect(self._copy_character_bible)
        header_layout.addWidget(self.btn_copy_bible)
        
        layout.addLayout(header_layout)

        # Description
        desc_label = QLabel(
            "The Character Bible ensures consistent character appearance across all scenes. "
            "Each character has 5 unique consistency anchors that are automatically injected "
            "into scene prompts during image generation."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 8px; background: #f5f5f5; border-radius: 4px;")
        layout.addWidget(desc_label)

        # Character Bible display area
        self.ed_character_bible = QTextEdit()
        self.ed_character_bible.setReadOnly(True)
        self.ed_character_bible.setFont(QFont("Courier New", 10))
        self.ed_character_bible.setPlaceholderText(
            "Character Bible will appear here after script generation.\n\n"
            "It will include:\n"
            "• Character physical blueprint (age, ethnicity, height, build, skin tone)\n"
            "• Hair DNA (color, length, style, texture)\n"
            "• Eye signature (color, shape, expression)\n"
            "• Facial map (nose, lips, jawline, distinguishing marks)\n"
            "• 5 unique consistency anchors for each character\n"
            "• Scene reminders to maintain visual consistency"
        )
        layout.addWidget(self.ed_character_bible, 1)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_thumbnail_tab(self):
        """Build thumbnail tab with horizontal layout"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        # Changed from QVBoxLayout to QHBoxLayout for horizontal display
        layout = QHBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        self.thumbnail_widgets = []
        for i in range(3):
            version_card = QGroupBox(f"Phiên bản {i+1}")
            version_card.setMinimumWidth(290)

            card_layout = QVBoxLayout(version_card)

            img_thumb = QLabel()
            img_thumb.setFixedSize(270, 480)
            img_thumb.setAlignment(Qt.AlignCenter)
            img_thumb.setText("Chưa tạo")
            card_layout.addWidget(img_thumb)

            self.thumbnail_widgets.append({"thumbnail": img_thumb})
            layout.addWidget(version_card)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_social_tab(self):
        """Build social media tab with improved formatting - Issue 5"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(20)  # Issue 5: Increased from 16 for better separation

        self.social_version_widgets = []
        for i in range(3):
            version_card = QGroupBox(f"📱 Phiên bản {i+1}")
            card_layout = QVBoxLayout(version_card)
            card_layout.setSpacing(12)

            # Caption section
            lbl_caption = QLabel("📝 Caption:")
            lbl_caption.setFont(QFont("Segoe UI", 13, QFont.Bold))
            card_layout.addWidget(lbl_caption)

            ed_caption = QTextEdit()
            ed_caption.setReadOnly(True)
            ed_caption.setMinimumHeight(100)
            ed_caption.setFont(QFont("Segoe UI", 13))
            card_layout.addWidget(ed_caption)

            # Hashtags section
            lbl_hashtags = QLabel("🏷️ Hashtags:")
            lbl_hashtags.setFont(QFont("Segoe UI", 13, QFont.Bold))
            card_layout.addWidget(lbl_hashtags)

            ed_hashtags = QTextEdit()
            ed_hashtags.setReadOnly(True)
            ed_hashtags.setMinimumHeight(60)
            ed_hashtags.setFont(QFont("Courier New", 12))  # Issue 5: Monospace for hashtags
            card_layout.addWidget(ed_hashtags)

            # Copy buttons
            btn_row = QHBoxLayout()

            btn_copy_caption = QPushButton("📋 Copy Caption")
            btn_copy_caption.setObjectName("btn_info_copy")
            btn_copy_caption.clicked.connect(
                lambda _, e=ed_caption: self._copy_to_clipboard(e.toPlainText())
            )
            btn_row.addWidget(btn_copy_caption)

            btn_copy_hashtags = QPushButton("📋 Copy Hashtags")
            btn_copy_hashtags.setObjectName("btn_info_copy")
            btn_copy_hashtags.clicked.connect(
                lambda _, e=ed_hashtags: self._copy_to_clipboard(e.toPlainText())
            )
            btn_row.addWidget(btn_copy_hashtags)

            btn_copy_all = QPushButton("📋 Copy All")
            btn_copy_all.setObjectName("btn_primary")
            btn_copy_all.clicked.connect(
                lambda _, c=ed_caption, h=ed_hashtags:
                    self._copy_to_clipboard(f"{c.toPlainText()}\n\n{h.toPlainText()}")
            )
            btn_row.addWidget(btn_copy_all)

            card_layout.addLayout(btn_row)

            self.social_version_widgets.append({
                "widget": version_card,
                "caption": ed_caption,
                "hashtags": ed_hashtags
            })

            layout.addWidget(version_card)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_group(self, title):
        """Create a styled group box"""
        gb = QGroupBox(title)
        return gb

    def _update_scenes(self):
        """Update scene count (removed label display)"""
        # Scene count calculation only - label removed from UI
        n = max(1, math.ceil(self.sp_duration.value() / 8.0))
        # self.lb_scenes removed - no need to update UI
    
    def _on_section_toggled(self, toggled_section, checked):
        """Handle section toggle - accordion behavior with container widgets"""
        # Get container for toggled section
        container = None
        if toggled_section == self.gb_model:
            container = getattr(self, '_model_container', None)
        elif toggled_section == self.gb_products:
            container = getattr(self, '_products_container', None)
        elif toggled_section == self.gb_settings:
            container = getattr(self, '_settings_container', None)
        
        # Show/hide container
        if container:
            container.setVisible(checked)
        
        # Collapse other sections if opening this one
        if checked:
            sections = [
                (self.gb_model, getattr(self, '_model_container', None)),
                (self.gb_products, getattr(self, '_products_container', None)),
                (self.gb_settings, getattr(self, '_settings_container', None))
            ]
            for section, section_container in sections:
                if section != toggled_section and section.isChecked():
                    section.blockSignals(True)
                    section.setChecked(False)
                    section.blockSignals(False)
                    if section_container:
                        section_container.setVisible(False)
    
    def _create_collapsible_group(self, title):
        """Create collapsible group box"""
        gb = QGroupBox(title)
        gb.setFont(QFont("Segoe UI", 11, QFont.Bold))
        gb.setStyleSheet("""
            QGroupBox {
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                background: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 4px 12px;
                background: white;
                border-radius: 4px;
            }
            QGroupBox:checked {
                border: 2px solid #2196F3;
            }
        """)
        return gb

    def _pick_product_images(self):
        """Pick product images"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh sản phẩm", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if not files:
            return

        self.prod_paths = files
        self._refresh_product_thumbnails()

    def _refresh_product_thumbnails(self):
        """Refresh product thumbnails"""
        while self.prod_thumb_container.count():
            item = self.prod_thumb_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        max_show = 5
        for i, path in enumerate(self.prod_paths[:max_show]):
            thumb = QLabel()
            thumb.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
            thumb.setScaledContents(True)
            thumb.setPixmap(
                QPixmap(path).scaled(
                    THUMBNAIL_SIZE, THUMBNAIL_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            thumb.setStyleSheet("border: 1px solid #90CAF9;")
            self.prod_thumb_container.addWidget(thumb)

        if len(self.prod_paths) > max_show:
            extra = QLabel(f"+{len(self.prod_paths) - max_show}")
            extra.setFixedSize(THUMBNAIL_SIZE, THUMBNAIL_SIZE)
            extra.setAlignment(Qt.AlignCenter)
            extra.setStyleSheet("border: 1px dashed #666; font-weight: bold;")
            self.prod_thumb_container.addWidget(extra)

        self.prod_thumb_container.addStretch(1)

    def _collect_cfg(self):
        """Collect configuration"""
        # Get models from ModelSelectorWidget
        models = self.model_selector.get_models()
        model_paths = [m["image_path"] for m in models if m.get("image_path")]

        # For backward compatibility, use first model's JSON if available
        first_model_json = ""
        if models and models[0].get("data"):
            import json

            try:
                first_model_json = json.dumps(models[0]["data"], ensure_ascii=False)
            except:
                first_model_json = str(models[0]["data"])

        return {
            "project_name": (self.ed_name.text() or "").strip() or svc.default_project_name(),
            "idea": self.ed_idea.toPlainText(),
            "product_main": self.ed_product.toPlainText(),
            "script_style": self.cb_style.currentText(),
            "image_style": self.cb_imgstyle.currentText(),
            "script_model": self.cb_script_model.currentText(),
            "image_model": self.cb_image_model.currentText(),
            "voice_id": self.ed_voice.text().strip(),
            "duration_sec": int(self.sp_duration.value()),
            "videos_count": int(self.sp_videos.value()),
            "ratio": self.cb_ratio.currentText(),
            "speech_lang": self.LANGUAGE_MAP.get(
                self.cb_lang.currentText(), "vi"
            ),  # Issue 3: Use mapping to get language code
            "social_platform": self.cb_social.currentText(),
            "first_model_json": first_model_json,
            "product_count": len(self.prod_paths),
            "models": models,
            "model_paths": model_paths,
        }

    def _append_log(self, msg):
        """Append log message"""
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        self.ed_log.appendPlainText(line)

    def _copy_to_clipboard(self, text):
        """Copy to clipboard"""
        from PyQt5.QtWidgets import QApplication

        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        self._append_log("Đã copy vào clipboard")

    def _regenerate_character_bible(self):
        """Regenerate character bible from current script"""
        if not self.cache.get("outline"):
            QMessageBox.warning(self, "Chưa có kịch bản", "Vui lòng viết kịch bản trước.")
            return
        
        self._append_log("🔄 Đang tạo lại Character Bible...")
        
        try:
            from services.google.character_bible import create_character_bible, format_character_bible_for_display
            
            outline = self.cache["outline"]
            script_json = outline.get("script_json", {})
            existing_bible = script_json.get("character_bible", [])
            
            cfg = self._collect_cfg()
            video_concept = f"{cfg.get('idea', '')} {cfg.get('product_main', '')}"
            screenplay = outline.get("screenplay_text", "")
            
            # Create character bible
            bible = create_character_bible(video_concept, screenplay, existing_bible)
            self.character_bible = bible
            self.cache["character_bible"] = bible
            
            # Update display
            bible_text = format_character_bible_for_display(bible)
            self.ed_character_bible.setPlainText(bible_text)
            
            self._append_log("✓ Character Bible đã được tạo lại")
            
        except Exception as e:
            self._append_log(f"❌ Lỗi tạo Character Bible: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể tạo Character Bible: {e}")

    def _copy_character_bible(self):
        """Copy character bible summary to clipboard"""
        text = self.ed_character_bible.toPlainText()
        if text:
            self._copy_to_clipboard(text)
        else:
            self._append_log("⚠ Character Bible trống")

    def _on_auto_workflow(self):
        """PR#5: Auto workflow - runs all 3 steps sequentially"""
        self._append_log("⚡ Bắt đầu quy trình tự động (3 bước)...")

        # Disable auto button during workflow
        self.btn_auto.setEnabled(False)
        self.btn_script.setEnabled(False)
        self.btn_images.setEnabled(False)
        self.btn_video.setEnabled(False)

        # Step 1: Write script
        self._append_log("📝 Bước 1/3: Viết kịch bản...")
        self._on_write_script()

        # Note: Steps 2 and 3 will be triggered automatically via signals
        # when each step completes (script_finished -> generate_images -> generate_video)

    def _on_write_script(self):
        """Write script"""
        cfg = self._collect_cfg()

        self._append_log("Bắt đầu tạo kịch bản...")
        self.btn_script.setEnabled(False)
        self.btn_script.setText("⏳ Đang tạo...")
        self.btn_stop.setEnabled(True)  # PR#4: Enable stop button

        self.script_worker = ScriptWorker(cfg)
        self.script_worker.progress.connect(self._append_log)
        self.script_worker.done.connect(self._on_script_done)
        self.script_worker.error.connect(self._on_script_error)
        self.script_worker.start()

    def _on_script_done(self, outline):
        """Script done - with cache system"""
        try:
            self.last_outline = outline

            # Cache outline
            self.cache["outline"] = outline

            # Cache scene prompts
            for scene in outline.get("scenes", []):
                scene_idx = scene.get("index", 0)
                self.cache["scene_prompts"][scene_idx] = {
                    "video": scene.get("prompt_video"),
                    "image": scene.get("prompt_image"),
                    "speech": scene.get("speech"),
                }

            social_media = outline.get("social_media", {})
            versions = social_media.get("versions", [])

            # Update social tab with separate caption and hashtags - Issue 5
            for i, version in enumerate(versions[:3]):
                if i < len(self.social_version_widgets):
                    widget_data = self.social_version_widgets[i]

                    caption = version.get("caption", "")
                    hashtags = " ".join(version.get("hashtags", []))

                    # Issue 5: Separate fields for better readability
                    widget_data["caption"].setPlainText(caption)
                    widget_data["hashtags"].setPlainText(hashtags)

            self._display_scene_cards(outline.get("scenes", []))

            # Update Character Bible tab
            character_bible = outline.get("character_bible")
            character_bible_text = outline.get("character_bible_text", "")
            if character_bible:
                self.character_bible = character_bible
                self.cache["character_bible"] = character_bible
                self.ed_character_bible.setPlainText(character_bible_text)
                self.btn_regen_bible.setEnabled(True)
                self.btn_copy_bible.setEnabled(True)
                self._append_log(f"✓ Tạo Character Bible với {len(character_bible.characters)} nhân vật")
            else:
                self.ed_character_bible.setPlainText("(Không có Character Bible)")

            self._append_log(f"✓ Tạo kịch bản thành công ({len(outline.get('scenes', []))} cảnh)")
            self._append_log(f"✓ Tạo {len(versions)} phiên bản social media")
            self._append_log(f"✓ Đã cache kịch bản và {len(self.cache['scene_prompts'])} prompts")

            self.btn_images.setEnabled(True)

        except Exception as e:
            self._append_log(f"❌ Lỗi hiển thị: {e}")
        finally:
            self.btn_script.setEnabled(True)
            self.btn_script.setText("📝 Viết kịch bản")
            self.btn_stop.setEnabled(False)  # PR#4: Disable stop button

    def _on_script_error(self, error_msg):
        """Script error"""
        if error_msg.startswith("MissingAPIKey:"):
            QMessageBox.warning(
                self, "Thiếu API Key", "Chưa nhập Google API Key trong tab Cài đặt."
            )
            self._append_log("❌ Thiếu Google API Key")
        else:
            QMessageBox.critical(self, "Lỗi", error_msg)
            self._append_log(f"❌ Lỗi: {error_msg}")
        self.btn_script.setEnabled(True)
        self.btn_script.setText("📝 Viết kịch bản")

    def _display_scene_cards(self, scenes):
        """Display scene cards with SceneResultCard and alternating colors"""
        while self.scenes_layout.count() > 1:
            item = self.scenes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.scene_cards = []
        self.scene_images = {}

        for i, scene in enumerate(scenes):
            scene_idx = scene.get("index", i + 1)

            # Use SceneResultCard with alternating colors
            card = SceneResultCard(scene_idx, scene, alternating_color=(i % 2 == 1))
            self.scenes_layout.insertWidget(i, card)

            self.scene_cards.append(card)
            self.scene_images[scene_idx] = {"card": card, "path": None}

    def _on_generate_images(self):
        """Generate images - with cache validation"""
        # Validate cache
        if not self.cache["outline"]:
            QMessageBox.warning(
                self, "Chưa có kịch bản", "Vui lòng viết kịch bản trước. (Cache rỗng)"
            )
            return

        cfg = self._collect_cfg()
        use_whisk = cfg.get("image_model") == "Whisk"

        # Get model paths from ModelSelectorWidget
        model_paths = cfg.get("model_paths", [])

        self._append_log("Bắt đầu tạo ảnh...")
        self.btn_images.setEnabled(False)
        self.btn_stop.setEnabled(True)  # PR#4: Enable stop button

        # Get character bible from cache
        character_bible = self.cache.get("character_bible")
        
        self.img_worker = ImageGenerationWorker(
            self.cache["outline"], cfg, model_paths, self.prod_paths, use_whisk, character_bible
        )

        self.img_worker.progress.connect(self._append_log)
        self.img_worker.scene_image_ready.connect(self._on_scene_image_ready)
        self.img_worker.thumbnail_ready.connect(self._on_thumbnail_ready)
        self.img_worker.finished.connect(self._on_images_finished)

        self.img_worker.start()

    def _on_scene_image_ready(self, scene_idx, img_data):
        """Scene image ready - with cache"""
        cfg = self._collect_cfg()
        dirs = svc.ensure_project_dirs(cfg["project_name"])
        img_path = dirs["preview"] / f"scene_{scene_idx}.png"

        with open(img_path, "wb") as f:
            f.write(img_data)

        # Cache the image
        self.cache["scene_images"][scene_idx] = str(img_path)

        if scene_idx in self.scene_images:
            card = self.scene_images[scene_idx].get("card")
            if card:
                card.set_image_path(str(img_path))
            self.scene_images[scene_idx]["path"] = str(img_path)

        self._append_log(f"✓ Ảnh cảnh {scene_idx} đã sẵn sàng")

    def _on_thumbnail_ready(self, version_idx, img_data):
        """Thumbnail ready - with cache"""
        cfg = self._collect_cfg()
        dirs = svc.ensure_project_dirs(cfg["project_name"])
        img_path = dirs["preview"] / f"thumbnail_v{version_idx+1}.png"

        with open(img_path, "wb") as f:
            f.write(img_data)

        # Cache the thumbnail
        self.cache["thumbnails"][version_idx] = str(img_path)

        if version_idx < len(self.thumbnail_widgets):
            widget_data = self.thumbnail_widgets[version_idx]
            pixmap = QPixmap(str(img_path))
            widget_data["thumbnail"].setPixmap(
                pixmap.scaled(270, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        self._append_log(f"✓ Thumbnail phiên bản {version_idx+1} đã sẵn sàng")

    def _on_images_finished(self, success):
        """Images finished"""
        if success:
            self._append_log("✓ Hoàn tất tạo ảnh")
            self.btn_video.setEnabled(True)
        else:
            self._append_log("❌ Có lỗi khi tạo ảnh")

        self.btn_images.setEnabled(True)
        self.btn_stop.setEnabled(False)  # PR#4: Disable stop button

    def _on_generate_video(self):
        """Generate video - with cache validation"""
        # Validate cache
        if not self.cache["outline"]:
            QMessageBox.warning(
                self, "Chưa có kịch bản", "Vui lòng viết kịch bản trước. (Cache rỗng)"
            )
            return

        if not self.cache["scene_images"]:
            QMessageBox.warning(
                self, "Chưa có ảnh cảnh", "Vui lòng tạo ảnh trước. (Cache chưa có ảnh)"
            )
            return

        # Get config and log language settings
        cfg = self._collect_cfg()
        speech_lang = cfg.get("speech_lang", "vi")
        voice_id = cfg.get("voice_id", "")
        
        self._append_log("Bắt đầu tạo video...")
        self._append_log(f"✓ Sử dụng cache: {len(self.cache['scene_images'])} ảnh cảnh")
        self._append_log(f"✓ Ngôn ngữ lời thoại: {speech_lang}")
        if voice_id:
            self._append_log(f"✓ Voice ID: {voice_id}")
        
        self.btn_video.setEnabled(False)

        QMessageBox.information(
            self, "Thông báo", "Chức năng tạo video sẽ được triển khai trong phiên bản tiếp theo."
        )

        self.btn_video.setEnabled(True)
        
        # TODO: When video generation is fully implemented (replacing the stub above),
        # integrate auto-download by calling _auto_download_video() with the generated
        # video path. Example:
        # if video_path and self.chk_auto_download.isChecked():
        #     self._auto_download_video(video_path)

    def stop_processing(self):
        """PR#4: Stop all workers"""
        if hasattr(self, "script_worker") and self.script_worker and self.script_worker.isRunning():
            self.script_worker.terminate()
            self._append_log("[INFO] Đã dừng script worker")

        if hasattr(self, "image_worker") and self.image_worker and self.image_worker.isRunning():
            self.image_worker.terminate()
            self._append_log("[INFO] Đã dừng image worker")

        # Re-enable buttons
        self.btn_script.setEnabled(True)
        self.btn_script.setText("📝 Viết kịch bản")
        self.btn_images.setEnabled(True)
        self.btn_images.setText("🎨 Tạo ảnh")
        self.btn_stop.setEnabled(False)

        self._append_log("[INFO] Đã dừng xử lý")

    def _change_download_path(self):
        """Change download folder via file dialog (moved to Settings tab)"""
        if self.ed_download_path is None:
            self._append_log("⚠ Chức năng này đã được chuyển sang tab Cài đặt")
            return
            
        current_path = self.ed_download_path.text()
        
        new_path = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục lưu video",
            current_path,
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if new_path:
            self.ed_download_path.setText(new_path)
            self._append_log(f"✓ Đổi thư mục tải: {new_path}")

    def _auto_download_video(self, source_path):
        """Copy video to download folder and open folder (moved to Settings tab)
        
        Args:
            source_path (str): Path to the source video file to download
        """
        # Default download path if not set via Settings tab
        if self.ed_download_path is None:
            download_dir = Path.home() / "Downloads" / "VideoSuperUltra"
        else:
            try:
                download_dir = Path(self.ed_download_path.text())
            except:
                download_dir = Path.home() / "Downloads" / "VideoSuperUltra"
        
        try:
            download_dir.mkdir(parents=True, exist_ok=True)
            
            source = Path(source_path)
            destination = download_dir / source.name
            
            # Copy file
            shutil.copy2(source, destination)
            
            self._append_log(f"✓ Đã tải về: {destination}")
            
            # Show notification
            reply = QMessageBox.question(
                self,
                "Tải thành công",
                f"Video đã được tải về:\n{destination}\n\nMở thư mục?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._open_folder(download_dir)
                
        except Exception as e:
            self._append_log(f"✗ Lỗi tải video: {e}")
            QMessageBox.warning(self, "Lỗi", f"Không thể tải video:\n{e}")

    def _open_folder(self, folder_path):
        """Open folder in file explorer
        
        Args:
            folder_path (Path): Path object or string path to the folder to open
        """
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['explorer', str(folder_path)])
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(folder_path)])
            else:
                subprocess.Popen(['xdg-open', str(folder_path)])
        except Exception as e:
            self._append_log(f"⚠ Không thể mở thư mục: {e}")


# FIXED: Removed QSS autoload block (lines 1000-1034) to prevent theme conflicts
