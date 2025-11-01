
import os, json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QComboBox, QSpinBox, QLineEdit,
    QTableWidget, QTableWidgetItem, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QLocale, QThread, pyqtSignal, QObject, QUrl, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.Qt import QDesktopServices
from utils import config as cfg
from .text2video_panel_impl import _Worker, _ASPECT_MAP, _LANGS, _VIDEO_MODELS, build_prompt_json

class Text2VideoPane(QWidget):
    def __init__(self, parent=None):
        self._cards_state = {}  # scene->data
        super().__init__(parent)
        self._ctx = {}
        self._title = "Project"
        self._build_ui()
        self._apply_styles()

    def _build_ui(self):
        root = QHBoxLayout(self); root.setSpacing(12); root.setContentsMargins(8,8,8,8)

        # LEFT (1/3) - PR#4: 6-row redesigned layout
        colL = QVBoxLayout(); colL.setSpacing(8)
        
        # Project name row
        rowp = QHBoxLayout(); rowp.addWidget(QLabel("<b>Tên dự án:</b>"))
        self.ed_project = QLineEdit(); self.ed_project.setPlaceholderText("Nhập tên dự án (để trống sẽ tự tạo)")
        rowp.addWidget(self.ed_project,1); colL.addLayout(rowp)

        # Idea text area
        colL.addWidget(QLabel("<b>Ý tưởng (đoạn văn):</b>"))
        self.ed_idea = QTextEdit(); self.ed_idea.setAcceptRichText(False)
        self.ed_idea.setLocale(QLocale(QLocale.Vietnamese, QLocale.Vietnam))
        self.ed_idea.setPlaceholderText("Nhập ý tưởng thô (<10 từ)…")
        self.ed_idea.setMaximumHeight(100)
        colL.addWidget(self.ed_idea)

        # Row 1: Video style + Script style
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("<b>Phong cách video:</b>"))
        self.cb_style = QComboBox()
        self.cb_style.addItems(["Điện ảnh (Cinematic)","Hoạt hình Nhật (Anime)","Tài liệu","Quay thực","3D/CGI","Stop‑motion","Màu nước","Cyberpunk","Noir","Fantasy","Sci‑Fi","Tối giản","Vlog","Doanh nghiệp","Trưng bày sản phẩm","Lifestyle","Thể thao","Du lịch"])
        row1.addWidget(self.cb_style,1)
        colL.addLayout(row1)

        # Row 2: Duration + Language
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("<b>Thời lượng (s):</b>"))
        self.sp_duration = QSpinBox(); self.sp_duration.setRange(3, 3600); self.sp_duration.setValue(100)
        row2.addWidget(self.sp_duration,1)
        row2.addWidget(QLabel("<b>Ngôn ngữ:</b>"))
        self.cb_out_lang = QComboBox()
        for name, code in _LANGS: self.cb_out_lang.addItem(name, code)
        row2.addWidget(self.cb_out_lang,1)
        colL.addLayout(row2)

        # Row 3: Aspect ratio + Videos per scene
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("<b>Tỉ lệ:</b>"))
        self.cb_ratio = QComboBox(); self.cb_ratio.addItems(["16:9","9:16","1:1","4:5","21:9"])
        row3.addWidget(self.cb_ratio,1)
        row3.addWidget(QLabel("<b>Số video/cảnh:</b>"))
        self.sp_copies = QSpinBox(); self.sp_copies.setRange(1, 5); self.sp_copies.setValue(1)
        row3.addWidget(self.sp_copies,1)
        colL.addLayout(row3)

        # Row 4: Video model
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("<b>Model tạo video:</b>"))
        self.cb_model = QComboBox(); self.cb_model.addItems(_VIDEO_MODELS)
        row4.addWidget(self.cb_model,1)
        colL.addLayout(row4)

        # Row 5: Up Scale 4K checkbox (PR#4: Added as checkbox)
        from PyQt5.QtWidgets import QCheckBox
        self.cb_upscale = QCheckBox("Up Scale 4K")
        self.cb_upscale.setStyleSheet("font-size: 14px; font-weight: 700;")
        colL.addWidget(self.cb_upscale)

        # Row 6: Single auto button + Stop button (PR#4)
        hb = QHBoxLayout()
        self.btn_auto = QPushButton("▶ Tạo video tự động (3 bước)")
        self.btn_auto.setObjectName("btn_success")
        self.btn_auto.setMinimumHeight(44)
        self.btn_stop = QPushButton("⏹ Dừng")
        self.btn_stop.setObjectName("btn_danger")
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

        # RIGHT (2/3)
        colR = QVBoxLayout(); colR.setSpacing(8)
        colR.addWidget(QLabel("Kịch bản chi tiết (Bible + Outline + Screenplay)"))
        self.view_story = QTextEdit(); self.view_story.setReadOnly(True); self.view_story.setMinimumHeight(200)
        colR.addWidget(self.view_story,0)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalHeaderLabels(["Cảnh","Prompt (VI)","Prompt (Đích)","Tỉ lệ","Thời lượng (s)","Xem"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setHidden(True); colR.addWidget(self.table, 0)

        colR.addWidget(QLabel("Cảnh + Prompt + Kết quả (CardList)"))
        self.cards = QListWidget()

        # Apply dark theme & spacing
        self.setObjectName("Text2VideoRoot")
        self.setStyleSheet("QListWidget::item{margin-bottom:3px;}")

        self.cards.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cards.setIconSize(QSize(288,162))
        self.cards.setIconSize(QSize(240, 135))  # bigger thumbnails
        colR.addWidget(self.cards,1)

        root.addLayout(colL,1); root.addLayout(colR,2)

        # Wire up (PR#4: Updated for new auto button + stop button)
        self.btn_auto.clicked.connect(self._on_auto_generate)
        self.btn_stop.clicked.connect(self.stop_processing)
        self.table.cellDoubleClicked.connect(self._open_prompt_view)
        self.cards.itemDoubleClicked.connect(self._open_card_prompt)
        self.btn_open_folder.clicked.connect(self._open_project_dir)
        
        # Keep worker reference
        self.worker = None
        self.thread = None


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
        # Unified theme v2 handles all styling
        pass

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
        payload = dict(
            project=self.ed_project.text().strip(),
            idea=idea,
            style=self.cb_style.currentText(),
            duration=int(self.sp_duration.value()),
            provider="Gemini 2.5",
            out_lang_code=self.cb_out_lang.currentData()
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
        for r in range(self.table.rowCount()):
            vi = self.table.item(r,1).text() if self.table.item(r,1) else ""
            tgt= self.table.item(r,2).text() if self.table.item(r,2) else vi
            j=build_prompt_json(r+1, vi, tgt, lang_code, ratio_key, style)
            scenes.append({"prompt": json.dumps(j, ensure_ascii=False, indent=2), "aspect": ratio})
        payload=dict(
            scenes=scenes, copies=self._t2v_get_copies(), model_key=self.cb_model.currentText(),
            title=self._title, dir_videos=self._ctx.get("dir_videos",""),
            upscale_4k=self.cb_upscale.isChecked()  # PR#4: Use checkbox instead of button
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
                j=build_prompt_json(i, sc.get("prompt_vi","" ), sc.get("prompt_tgt","" ), lang_code, self.cb_ratio.currentText(), self.cb_style.currentText())
                if prdir:
                    with open(os.path.join(prdir, f"scene_{i:02d}.json"), "w", encoding="utf-8") as f:
                        json.dump(j, f, ensure_ascii=False, indent=2)
            except Exception: pass
        self._append_log("[INFO] Kịch bản đã hiển thị & lưu file.")
        
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
        j=build_prompt_json(row+1, vi, tgt, lang_code, self.cb_ratio.currentText(), self.cb_style.currentText())
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
