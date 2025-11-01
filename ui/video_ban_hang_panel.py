# -*- coding: utf-8 -*-
"""
Video Bán Hàng Panel - Redesigned with 3-step workflow
FIXED: Removed QSS autoload block to prevent theme conflicts
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel, 
    QLineEdit, QPlainTextEdit, QPushButton, QFileDialog, QComboBox, 
    QSpinBox, QScrollArea, QToolButton, QMessageBox, QFrame, QSizePolicy,
    QTabWidget, QTextEdit, QDialog, QApplication
)
from PyQt5.QtGui import QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
import os
import math
import datetime
import time
from pathlib import Path

from services import sales_video_service as svc
from services import sales_script_service as sscript
from services import image_gen_service
from services.gemini_client import MissingAPIKey
from ui.widgets.scene_result_card import SceneResultCard
from ui.widgets.model_selector import ModelSelectorWidget
from ui.workers.script_worker import ScriptWorker

# Fonts
FONT_LABEL = QFont()
FONT_LABEL.setPixelSize(13)
FONT_INPUT = QFont()
FONT_INPUT.setPixelSize(12)

# Sizes
THUMBNAIL_SIZE = 60
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
        desc_text = self.scene_data.get('desc', '')
        if len(desc_text) > 150:
            desc_text = desc_text[:150] + "..."
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        info_layout.addWidget(desc)
        
        # Speech text
        speech_text = self.scene_data.get('speech', '')
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
        btn_prompt.setObjectName('btn_info_prompt')
        btn_prompt.clicked.connect(self._show_prompts)
        btn_layout.addWidget(btn_prompt)
        
        # Regenerate button
        btn_regen = QPushButton("🔄 Tạo lại")
        btn_regen.setObjectName('btn_warning_regen')
        btn_layout.addWidget(btn_regen)
        
        # Video button
        btn_video = QPushButton("🎬 Video")
        btn_video.setObjectName('btn_primary_video')
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
        ed_img_prompt.setPlainText(self.scene_data.get('prompt_image', ''))
        ed_img_prompt.setMaximumHeight(180)
        layout.addWidget(ed_img_prompt)
        
        btn_copy_img = QPushButton("📋 Copy Prompt Ảnh")
        btn_copy_img.setObjectName('btn_info_copy')
        btn_copy_img.clicked.connect(lambda: self._copy_to_clipboard(self.scene_data.get('prompt_image', '')))
        layout.addWidget(btn_copy_img)
        
        # Video prompt section
        lbl_vid = QLabel("🎬 Prompt Video:")
        layout.addWidget(lbl_vid)
        
        ed_vid_prompt = QTextEdit()
        ed_vid_prompt.setReadOnly(True)
        ed_vid_prompt.setPlainText(self.scene_data.get('prompt_video', ''))
        ed_vid_prompt.setMaximumHeight(180)
        layout.addWidget(ed_vid_prompt)
        
        btn_copy_vid = QPushButton("📋 Copy Prompt Video")
        btn_copy_vid.setObjectName('btn_info_copy_vid')
        btn_copy_vid.clicked.connect(lambda: self._copy_to_clipboard(self.scene_data.get('prompt_video', '')))
        layout.addWidget(btn_copy_vid)
        
        # Close button
        btn_close = QPushButton("✖ Đóng")
        btn_close.setObjectName('btn_primary_close')
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
            self.image_label.setPixmap(pixmap.scaled(320, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))


class ImageGenerationWorker(QThread):
    """Worker thread for generating images (scenes + thumbnails)"""
    progress = pyqtSignal(str)
    scene_image_ready = pyqtSignal(int, bytes)
    thumbnail_ready = pyqtSignal(int, bytes)
    finished = pyqtSignal(bool)
    
    def __init__(self, outline, cfg, model_paths, prod_paths, use_whisk=False):
        super().__init__()
        self.outline = outline
        self.cfg = cfg
        self.model_paths = model_paths
        self.prod_paths = prod_paths
        self.use_whisk = use_whisk
        self.should_stop = False
    
    def run(self):
        try:
            # Generate scene images
            scenes = self.outline.get("scenes", [])
            for i, scene in enumerate(scenes):
                if self.should_stop:
                    break
                
                # CRITICAL FIX: Add mandatory delay BEFORE every request (except first)
                # This prevents rate limiting regardless of which key is used
                if i > 0:
                    self.progress.emit(f"[RATE LIMIT] Chờ {RATE_LIMIT_DELAY_SEC}s trước khi tạo ảnh cảnh {scene.get('index')}...")
                    time.sleep(RATE_LIMIT_DELAY_SEC)
                
                self.progress.emit(f"Tạo ảnh cảnh {scene.get('index')}...")
                
                # Get prompt
                prompt = scene.get("prompt_image", "")
                
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
                            debug_callback=self.progress.emit
                        )
                        if img_data:
                            self.progress.emit(f"Cảnh {scene.get('index')}: Whisk ✓")
                    except Exception as e:
                        self.progress.emit(f"Whisk failed: {str(e)[:100]}")
                        img_data = None
                
                # Fallback to Gemini
                if img_data is None:
                    try:
                        self.progress.emit(f"Cảnh {scene.get('index')}: Dùng Gemini...")
                        
                        # No additional delay needed - we already waited above
                        img_data = image_gen_service.generate_image_with_rate_limit(
                            prompt, 
                            delay_before=0,  # Explicitly no extra delay
                            log_callback=lambda msg: self.progress.emit(msg)
                        )
                        
                        if img_data:
                            self.progress.emit(f"Cảnh {scene.get('index')}: Gemini ✓")
                        else:
                            self.progress.emit(f"Cảnh {scene.get('index')}: Không tạo được ảnh")
                    except Exception as e:
                        self.progress.emit(f"Gemini failed for scene {scene.get('index')}: {e}")
                
                if img_data:
                    self.scene_image_ready.emit(scene.get('index'), img_data)
            
            # Generate social media thumbnails
            social_media = self.outline.get("social_media", {})
            versions = social_media.get("versions", [])
            
            for i, version in enumerate(versions):
                if self.should_stop:
                    break
                
                # CRITICAL FIX: Delay before thumbnails too
                # First thumbnail comes after all scene images, so always delay
                self.progress.emit(f"[RATE LIMIT] Chờ {RATE_LIMIT_DELAY_SEC}s trước thumbnail {i+1}...")
                time.sleep(RATE_LIMIT_DELAY_SEC)
                
                self.progress.emit(f"Tạo thumbnail phiên bản {i+1}...")
                
                prompt = version.get("thumbnail_prompt", "")
                text_overlay = version.get("thumbnail_text_overlay", "")
                
                try:
                    # No additional delay - we already waited above
                    thumb_data = image_gen_service.generate_image_with_rate_limit(
                        prompt, 
                        delay_before=0,
                        log_callback=lambda msg: self.progress.emit(msg)
                    )
                    
                    if thumb_data:
                        import tempfile
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            tmp.write(thumb_data)
                            tmp_path = tmp.name
                        
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_out:
                            out_path = tmp_out.name
                        
                        sscript.generate_thumbnail_with_text(tmp_path, text_overlay, out_path)
                        
                        with open(out_path, 'rb') as f:
                            final_thumb = f.read()
                        
                        os.unlink(tmp_path)
                        os.unlink(out_path)
                        
                        self.thumbnail_ready.emit(i, final_thumb)
                        self.progress.emit(f"Thumbnail {i+1}: ✓")
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
        
        # Cache system to persist data across workflow steps
        self.cache = {
            'outline': None,
            'scene_images': {},
            'scene_prompts': {},
            'thumbnails': {},
        }
        
        self._build_ui()
    
    def _build_ui(self):
        """Build the 2-column UI"""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        # Main horizontal layout
        main = QHBoxLayout()
        main.setSpacing(0)
        main.setContentsMargins(0, 0, 0, 0)
        
        # Left column (380px fixed)
        self.left_widget = QWidget()
        self.left_widget.setFixedWidth(380)
        left_layout = QVBoxLayout(self.left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)
        
        self._build_left_column(left_layout)
        
        # Right column (flexible)
        self.right_widget = QWidget()
        right_layout = QVBoxLayout(self.right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)
        
        self._build_right_column(right_layout)
        
        main.addWidget(self.left_widget)
        main.addWidget(self.right_widget, 1)
        
        root.addLayout(main)
    
    def _build_left_column(self, layout):
        """Build left column with project settings"""
        
        # Project info
        gb_proj = self._create_group("Dự án")
        g = QGridLayout(gb_proj)
        g.setVerticalSpacing(6)
        
        self.ed_name = QLineEdit()
        self.ed_name.setFont(FONT_INPUT)
        self.ed_name.setPlaceholderText("Tự tạo nếu để trống")
        self.ed_name.setText(svc.default_project_name())
        
        self.ed_idea = QPlainTextEdit()
        self.ed_idea.setFont(FONT_INPUT)
        self.ed_idea.setMinimumHeight(60)
        self.ed_idea.setPlaceholderText("Ý tưởng (2–3 dòng)")
        
        self.ed_product = QPlainTextEdit()
        self.ed_product.setFont(FONT_INPUT)
        self.ed_product.setMinimumHeight(100)
        self.ed_product.setPlaceholderText("Nội dung chính / Đặc điểm sản phẩm")
        
        g.addWidget(QLabel("Tên dự án:"), 0, 0)
        g.addWidget(self.ed_name, 1, 0)
        g.addWidget(QLabel("Ý tưởng:"), 2, 0)
        g.addWidget(self.ed_idea, 3, 0)
        g.addWidget(QLabel("Nội dung:"), 4, 0)
        g.addWidget(self.ed_product, 5, 0)
        
        for w in gb_proj.findChildren(QLabel):
            w.setFont(FONT_LABEL)
        
        layout.addWidget(gb_proj)
        
        # Model selector widget (0-5 models with image + JSON)
        self.model_selector = ModelSelectorWidget("Thông tin người mẫu")
        layout.addWidget(self.model_selector)
        
        # Product images
        gb_prod = self._create_group("Ảnh sản phẩm")
        pv = QVBoxLayout(gb_prod)
        
        btn_prod = QPushButton("📁 Chọn ảnh sản phẩm")
        btn_prod.setObjectName('btn_import_nhap_product')
        btn_prod.clicked.connect(self._pick_product_images)
        pv.addWidget(btn_prod)
        
        self.prod_thumb_container = QHBoxLayout()
        self.prod_thumb_container.setSpacing(4)
        pv.addLayout(self.prod_thumb_container)
        
        layout.addWidget(gb_prod)
        
        # Video settings (Grid 2x5)
        gb_cfg = self._create_group("Cài đặt video")
        s = QGridLayout(gb_cfg)
        s.setVerticalSpacing(8)
        s.setHorizontalSpacing(10)
        
        def make_widget(widget_class, **kwargs):
            w = widget_class()
            w.setMinimumHeight(32)
            for k, v in kwargs.items():
                if hasattr(w, k):
                    getattr(w, k)(v) if callable(getattr(w, k)) else setattr(w, k, v)
            return w
        
        self.cb_style = make_widget(QComboBox)
        self.cb_style.addItems(["Viral", "KOC Review", "Kể chuyện"])
        
        self.cb_imgstyle = make_widget(QComboBox)
        self.cb_imgstyle.addItems(["Điện ảnh", "Hiện đại/Trendy", "Anime", "Hoạt hình 3D"])
        
        self.cb_script_model = make_widget(QComboBox)
        self.cb_script_model.addItems(["Gemini 2.5 Flash (mặc định)", "ChatGPT4 Turbo (tuỳ chọn)"])
        
        self.cb_image_model = make_widget(QComboBox)
        self.cb_image_model.addItems(["Gemini", "Whisk"])
        
        self.ed_voice = make_widget(QLineEdit)
        self.ed_voice.setPlaceholderText("ElevenLabs VoiceID")
        
        self.cb_lang = make_widget(QComboBox)
        self.cb_lang.addItems(["vi", "en"])
        
        self.sp_duration = make_widget(QSpinBox)
        self.sp_duration.setRange(8, 1200)
        self.sp_duration.setSingleStep(8)
        self.sp_duration.setValue(32)
        self.sp_duration.valueChanged.connect(self._update_scenes)
        
        self.sp_videos = make_widget(QSpinBox)
        self.sp_videos.setRange(1, 4)
        self.sp_videos.setValue(1)
        
        self.cb_ratio = make_widget(QComboBox)
        self.cb_ratio.addItems(["9:16", "16:9", "1:1", "4:5"])
        
        self.cb_social = make_widget(QComboBox)
        self.cb_social.addItems(['TikTok', 'Facebook', 'YouTube'])
        
        self.lb_scenes = QLabel("Số cảnh: 4")
        self.lb_scenes.setFont(FONT_LABEL)
        
        # Grid layout
        row = 0
        s.addWidget(QLabel("Phong cách KB:"), row, 0)
        s.addWidget(self.cb_style, row, 1)
        s.addWidget(QLabel("Phong cách HA:"), row, 2)
        s.addWidget(self.cb_imgstyle, row, 3)
        
        row += 1
        s.addWidget(QLabel("Model KB:"), row, 0)
        s.addWidget(self.cb_script_model, row, 1)
        s.addWidget(QLabel("Model tạo ảnh:"), row, 2)
        s.addWidget(self.cb_image_model, row, 3)
        
        row += 1
        s.addWidget(QLabel("Lời thoại:"), row, 0)
        s.addWidget(self.ed_voice, row, 1)
        s.addWidget(QLabel("Ngôn ngữ:"), row, 2)
        s.addWidget(self.cb_lang, row, 3)
        
        row += 1
        s.addWidget(QLabel("Thời lượng (s):"), row, 0)
        s.addWidget(self.sp_duration, row, 1)
        s.addWidget(QLabel("Số video/cảnh:"), row, 2)
        s.addWidget(self.sp_videos, row, 3)
        
        row += 1
        s.addWidget(QLabel("Tỉ lệ:"), row, 0)
        s.addWidget(self.cb_ratio, row, 1)
        s.addWidget(QLabel("Nền tảng:"), row, 2)
        s.addWidget(self.cb_social, row, 3)
        
        row += 1
        s.addWidget(self.lb_scenes, row, 0, 1, 4)
        
        for w in gb_cfg.findChildren(QLabel):
            w.setFont(FONT_LABEL)
        
        layout.addWidget(gb_cfg)
        layout.addStretch(1)
        
        self._update_scenes()
    
    def _build_right_column(self, layout):
        """Build right column with results and logs"""
        
        # Tab widget
        self.results_tabs = QTabWidget()
        
        # Tab 1: Scenes
        scenes_tab = self._build_scenes_tab()
        self.results_tabs.addTab(scenes_tab, "🎬 Cảnh")
        
        # Tab 2: Thumbnail
        thumbnail_tab = self._build_thumbnail_tab()
        self.results_tabs.addTab(thumbnail_tab, "📺 Thumbnail")
        
        # Tab 3: Social
        social_tab = self._build_social_tab()
        self.results_tabs.addTab(social_tab, "📱 Social")
        
        layout.addWidget(self.results_tabs, 3)
        
        # Log area (reduced to 75px - 50% of original)
        gb_log = QGroupBox("Nhật ký xử lý")
        
        lv = QVBoxLayout(gb_log)
        self.ed_log = QPlainTextEdit()
        self.ed_log.setFont(FONT_INPUT)
        self.ed_log.setReadOnly(True)
        self.ed_log.setMaximumHeight(75)
        lv.addWidget(self.ed_log)
        
        layout.addWidget(gb_log, 1)
        
        # 3 buttons at bottom
        btn_layout = QHBoxLayout()
        
        self.btn_script = QPushButton("📝 Viết kịch bản")
        self.btn_script.setObjectName('btn_primary_script')
        self.btn_script.setMinimumHeight(40)
        self.btn_script.clicked.connect(self._on_write_script)
        
        self.btn_images = QPushButton("🎨 Tạo ảnh")
        self.btn_images.setObjectName('btn_warning_images')
        self.btn_images.setMinimumHeight(40)
        self.btn_images.clicked.connect(self._on_generate_images)
        self.btn_images.setEnabled(False)
        
        self.btn_video = QPushButton("🎬 Tạo video")
        self.btn_video.setObjectName('btn_success_video')
        self.btn_video.setMinimumHeight(40)
        self.btn_video.clicked.connect(self._on_generate_video)
        self.btn_video.setEnabled(False)
        
        # PR#4: Add stop button
        self.btn_stop = QPushButton("⏹ Dừng")
        self.btn_stop.setObjectName("btn_danger")
        self.btn_stop.setMaximumWidth(80)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_processing)
        
        btn_layout.addWidget(self.btn_script)
        btn_layout.addWidget(self.btn_images)
        btn_layout.addWidget(self.btn_video)
        btn_layout.addWidget(self.btn_stop)
        
        layout.addLayout(btn_layout)
    
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
            
            self.thumbnail_widgets.append({'thumbnail': img_thumb})
            layout.addWidget(version_card)
        
        layout.addStretch()
        scroll.setWidget(container)
        return scroll
    
    def _build_social_tab(self):
        """Build social media tab with combined caption + hashtags"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        self.social_version_widgets = []
        for i in range(3):
            version_card = QGroupBox(f"=== Phiên bản {i+1} ===")
            
            card_layout = QVBoxLayout(version_card)
            
            # Combined text area for caption + hashtags
            ed_combined = QTextEdit()
            ed_combined.setReadOnly(True)
            ed_combined.setMinimumHeight(120)
            ed_combined.setPlaceholderText("Caption và hashtags sẽ hiển thị ở đây sau khi tạo kịch bản")
            card_layout.addWidget(ed_combined)
            
            btn_copy = QPushButton("📋 Copy toàn bộ")
            btn_copy.setObjectName('btn_info_copy_caption')
            btn_copy.clicked.connect(lambda _, e=ed_combined: self._copy_to_clipboard(e.toPlainText()))
            card_layout.addWidget(btn_copy)
            
            self.social_version_widgets.append({
                'widget': version_card,
                'combined': ed_combined
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
        """Update scene count label"""
        n = max(1, math.ceil(self.sp_duration.value() / 8.0))
        self.lb_scenes.setText(f"Số cảnh: {n}")
    

    
    def _pick_product_images(self):
        """Pick product images"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn ảnh sản phẩm", "", 
            "Images (*.png *.jpg *.jpeg *.webp)"
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
            thumb.setPixmap(QPixmap(path).scaled(
                THUMBNAIL_SIZE, THUMBNAIL_SIZE, 
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
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
        model_paths = [m['image_path'] for m in models if m.get('image_path')]
        
        # For backward compatibility, use first model's JSON if available
        first_model_json = ""
        if models and models[0].get('data'):
            import json
            try:
                first_model_json = json.dumps(models[0]['data'], ensure_ascii=False)
            except:
                first_model_json = str(models[0]['data'])
        
        return {
            "project_name": (self.ed_name.text() or '').strip() or svc.default_project_name(),
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
            "speech_lang": self.cb_lang.currentText(),
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
            self.cache['outline'] = outline
            
            # Cache scene prompts
            for scene in outline.get('scenes', []):
                scene_idx = scene.get('index', 0)
                self.cache['scene_prompts'][scene_idx] = {
                    'video': scene.get('prompt_video'),
                    'image': scene.get('prompt_image'),
                    'speech': scene.get('speech')
                }
            
            social_media = outline.get("social_media", {})
            versions = social_media.get("versions", [])
            
            # Update social tab with combined format
            for i, version in enumerate(versions[:3]):
                if i < len(self.social_version_widgets):
                    widget_data = self.social_version_widgets[i]
                    
                    caption = version.get("caption", "")
                    hashtags = " ".join(version.get("hashtags", []))
                    
                    # Combined format
                    combined_text = f"=== Phiên bản {i+1} ===\n\n{caption}\n\n{hashtags}\n\n{'=' * 40}"
                    widget_data['combined'].setPlainText(combined_text)
            
            self._display_scene_cards(outline.get("scenes", []))
            
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
            QMessageBox.warning(self, "Thiếu API Key", 
                              "Chưa nhập Google API Key trong tab Cài đặt.")
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
            scene_idx = scene.get('index', i + 1)
            
            # Use SceneResultCard with alternating colors
            card = SceneResultCard(scene_idx, scene, alternating_color=(i % 2 == 1))
            self.scenes_layout.insertWidget(i, card)
            
            self.scene_cards.append(card)
            self.scene_images[scene_idx] = {'card': card, 'path': None}
    
    def _on_generate_images(self):
        """Generate images - with cache validation"""
        # Validate cache
        if not self.cache['outline']:
            QMessageBox.warning(self, "Chưa có kịch bản", 
                              "Vui lòng viết kịch bản trước. (Cache rỗng)")
            return
        
        cfg = self._collect_cfg()
        use_whisk = (cfg.get("image_model") == "Whisk")
        
        # Get model paths from ModelSelectorWidget
        model_paths = cfg.get("model_paths", [])
        
        self._append_log("Bắt đầu tạo ảnh...")
        self.btn_images.setEnabled(False)
        self.btn_stop.setEnabled(True)  # PR#4: Enable stop button
        
        self.img_worker = ImageGenerationWorker(
            self.cache['outline'], cfg, 
            model_paths, self.prod_paths,
            use_whisk
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
        
        with open(img_path, 'wb') as f:
            f.write(img_data)
        
        # Cache the image
        self.cache['scene_images'][scene_idx] = str(img_path)
        
        if scene_idx in self.scene_images:
            card = self.scene_images[scene_idx].get('card')
            if card:
                card.set_image_path(str(img_path))
            self.scene_images[scene_idx]['path'] = str(img_path)
        
        self._append_log(f"✓ Ảnh cảnh {scene_idx} đã sẵn sàng")
    
    def _on_thumbnail_ready(self, version_idx, img_data):
        """Thumbnail ready - with cache"""
        cfg = self._collect_cfg()
        dirs = svc.ensure_project_dirs(cfg["project_name"])
        img_path = dirs["preview"] / f"thumbnail_v{version_idx+1}.png"
        
        with open(img_path, 'wb') as f:
            f.write(img_data)
        
        # Cache the thumbnail
        self.cache['thumbnails'][version_idx] = str(img_path)
        
        if version_idx < len(self.thumbnail_widgets):
            widget_data = self.thumbnail_widgets[version_idx]
            pixmap = QPixmap(str(img_path))
            widget_data['thumbnail'].setPixmap(
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
        if not self.cache['outline']:
            QMessageBox.warning(self, "Chưa có kịch bản", 
                              "Vui lòng viết kịch bản trước. (Cache rỗng)")
            return
        
        if not self.cache['scene_images']:
            QMessageBox.warning(self, "Chưa có ảnh cảnh", 
                              "Vui lòng tạo ảnh trước. (Cache chưa có ảnh)")
            return
        
        self._append_log("Bắt đầu tạo video...")
        self._append_log(f"✓ Sử dụng cache: {len(self.cache['scene_images'])} ảnh cảnh")
        self.btn_video.setEnabled(False)
        
        QMessageBox.information(self, "Thông báo", 
                              "Chức năng tạo video sẽ được triển khai trong phiên bản tiếp theo.")
        
        self.btn_video.setEnabled(True)
    
    def stop_processing(self):
        """PR#4: Stop all workers"""
        if hasattr(self, 'script_worker') and self.script_worker and self.script_worker.isRunning():
            self.script_worker.terminate()
            self._append_log("[INFO] Đã dừng script worker")
        
        if hasattr(self, 'image_worker') and self.image_worker and self.image_worker.isRunning():
            self.image_worker.terminate()
            self._append_log("[INFO] Đã dừng image worker")
        
        # Re-enable buttons
        self.btn_script.setEnabled(True)
        self.btn_script.setText("📝 Viết kịch bản")
        self.btn_images.setEnabled(True)
        self.btn_images.setText("🎨 Tạo ảnh")
        self.btn_stop.setEnabled(False)
        
        self._append_log("[INFO] Đã dừng xử lý")

# FIXED: Removed QSS autoload block (lines 1000-1034) to prevent theme conflicts