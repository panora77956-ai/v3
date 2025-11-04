
import json
import os
import re
import shutil
import subprocess

from PyQt5.QtCore import QObject, pyqtSignal

from services.google.labs_flow_client import DEFAULT_PROJECT_ID, LabsFlowClient
from services.utils.video_downloader import VideoDownloader
from utils import config as cfg

# Backward compatibility
LabsClient = LabsFlowClient

_ASPECT_MAP = {
    "16:9": "VIDEO_ASPECT_RATIO_LANDSCAPE",
    "21:9": "VIDEO_ASPECT_RATIO_LANDSCAPE",
    "9:16": "VIDEO_ASPECT_RATIO_PORTRAIT",
    "4:5": "VIDEO_ASPECT_RATIO_PORTRAIT",
    "1:1": "VIDEO_ASPECT_RATIO_SQUARE",
}

# Location extraction constants
# Regex pattern for parsing screenplay headers: INT./EXT. LOCATION - TIME (duration)
# Example: "INT. HẺM NHỎ - NGÀY (8s)" or "EXT. PARK - DAY"
_SCREENPLAY_LOCATION_PATTERN = re.compile(
    r'(INT\.|EXT\.)\s+(.+?)\s*-\s*(.+?)(?:\s*\(|\s*$)',
    re.IGNORECASE | re.MULTILINE
)

# Time keywords for daytime detection (support Vietnamese and English)
_DAYTIME_KEYWORDS = ["NGÀY", "DAY", "MORNING", "SÁNG", "BUỔI SÁNG"]
_NIGHTTIME_KEYWORDS = ["ĐÊM", "NIGHT", "EVENING", "TỐI", "BUỔI TỐI"]
_LANGS = [
    ("Tiếng Việt","vi"), ("Tiếng Anh","en"), ("Tiếng Nhật","ja"), ("Tiếng Hàn","ko"), ("Tiếng Trung","zh"),
    ("Tiếng Pháp","fr"), ("Tiếng Đức","de"), ("Tiếng Tây Ban Nha","es"), ("Tiếng Nga","ru"), ("Tiếng Thái","th"), ("Tiếng Indonesia","id")
]
_VIDEO_MODELS = [
    "veo_3_1_i2v_s_fast_portrait_ultra",
    "veo_3_1_i2v_s_fast_landscape_ultra",
    "veo_3_1_i2v_s_slow_portrait_ultra",
    "veo_3_1_i2v_s_slow_landscape_ultra",
    "veo_2_general_002",
    "veo_2_i2v_001"
]

# Mapping for display names
_MODEL_DISPLAY_NAMES = {
    "veo_3_1_i2v_s_fast_portrait_ultra": "Veo3.1 i2v Fast Portrait",
    "veo_3_1_i2v_s_fast_landscape_ultra": "Veo3.1 i2v Fast Landscape",
    "veo_3_1_i2v_s_slow_portrait_ultra": "Veo3.1 i2v Slow Portrait",
    "veo_3_1_i2v_s_slow_landscape_ultra": "Veo3.1 i2v Slow Landscape",
    "veo_2_general_002": "Veo2 General",
    "veo_2_i2v_001": "Veo2 i2v"
}

def get_model_key_from_display(display_name):
    """Convert display name back to API key"""
    for key, display in _MODEL_DISPLAY_NAMES.items():
        if display == display_name:
            return key
    return display_name  # Fallback

def extract_location_context(scene_data):
    """
    Extract location context from scene data.
    First tries scene.location field, then falls back to parsing screenplay text.
    
    Args:
        scene_data: Scene dict with potential 'location' field or 'screenplay_vi' text
    
    Returns:
        Formatted location context string or None
    """
    # First try: direct location field from LLM-generated scene
    location = scene_data.get("location", "").strip()
    if location:
        return location
    
    # Second try: parse scene header from screenplay text (if available)
    screenplay = scene_data.get("screenplay_vi", "") or scene_data.get("screenplay_tgt", "")
    if screenplay:
        match = _SCREENPLAY_LOCATION_PATTERN.search(screenplay)
        if match:
            int_ext = match.group(1).strip()  # INT. or EXT.
            location_name = match.group(2).strip()  # e.g., HẺM NHỎ
            time = match.group(3).strip()  # e.g., NGÀY
            
            # Build descriptive context
            setting_type = "Interior" if "INT" in int_ext.upper() else "Exterior"
            # Check for daytime keywords
            time_upper = time.upper()
            is_daytime = any(keyword in time_upper for keyword in _DAYTIME_KEYWORDS)
            time_desc = "daytime" if is_daytime else "nighttime"
            
            return f"{setting_type} setting: {location_name}, {time_desc} lighting"
    
    return None

def _build_setting_details(location_context):
    """
    Build setting_details string with optional location context.
    
    Args:
        location_context: Optional location context string
    
    Returns:
        Formatted setting_details string
    """
    base_details = "Clean composition, minimal props, no clutter; coherent lighting per scene style."
    if location_context:
        return f"{location_context}. {base_details}"
    return base_details

def build_prompt_json(scene_index:int, desc_vi:str, desc_tgt:str, lang_code:str, ratio_str:str, style:str, seconds:int=8, copies:int=1, resolution_hint:str=None, character_bible=None, enhanced_bible=None, voice_settings=None, location_context:str=None):
    """
    Strict prompt JSON schema:
    - objective/persona/constraints/assets/hard_locks/character_details/setting_details/key_action/camera_direction/audio/graphics/negatives/generation
    - bilingual localization (vi + target)
    
    Part D: Now supports enhanced_bible (CharacterBible object) for detailed character consistency
    Part E: Now supports location_context for maintaining consistent backgrounds across scenes
    """
    ratio_map = {
        '16:9': ('1920x1080', 'VIDEO_ASPECT_RATIO_LANDSCAPE'),
        '21:9': ('2560x1080', 'VIDEO_ASPECT_RATIO_LANDSCAPE'),
        '9:16': ('1080x1920', 'VIDEO_ASPECT_RATIO_PORTRAIT'),
        '4:5' : ('1080x1350', 'VIDEO_ASPECT_RATIO_PORTRAIT'),
        '1:1' : ('1080x1080', 'VIDEO_ASPECT_RATIO_SQUARE'),
    }
    res_default, _ = ratio_map.get(ratio_str, ('1920x1080', 'VIDEO_ASPECT_RATIO_LANDSCAPE'))
    resolution = resolution_hint or res_default
    seconds = max(3, int(seconds or 8))
    copies = max(1, int(copies or 1))

    b1 = round(seconds * 0.25, 2)
    b2 = round(seconds * 0.55, 2)
    b3 = round(seconds * 0.80, 2)
    segments = [
        {"t": f"0.0-{b1}s", "shot": "Establish subject & scene; clean composition; slow, steady motion."},
        {"t": f"{b1}-{b2}s", "shot": "Key action / gesture; maintain framing consistency; avoid jump cuts."},
        {"t": f"{b2}-{b3}s", "shot": "Detail emphasis; micro-movements; texture & highlights."},
        {"t": f"{b3}-{seconds:.1f}s", "shot": "Clear end beat; micro push-in or hold; leave space for on-screen text."},
    ]

    style_tags = []
    sl = (style or "").lower()
    if "điện ảnh" in sl or "cinematic" in sl: style_tags += ["cinematic","natural light","soft shadows"]
    if "anime" in sl or "hoạt hình" in sl: style_tags += ["anime","flat colors","outlined"]
    if "tài liệu" in sl or "documentary" in sl: style_tags += ["documentary","handheld feel"]
    if not style_tags: style_tags = ["modern","clean"]

    # Part E: Enhanced location consistency with specific location context
    location_lock = "Keep to single coherent environment; no random background swaps."
    if location_context:
        location_lock = f"CRITICAL: All scenes must be in {location_context}. Do NOT change background, setting, or environment. Maintain exact location consistency across all scenes."
    
    hard_locks = {
        "identity": "Keep the same face, body, and identity across scenes.",
        "wardrobe": "Outfit consistency is required. Do NOT change outfit, color, or add accessories without instruction.",
        "hair_makeup": "Keep hair and makeup consistent; do NOT change length or color unless explicitly instructed.",
        "location": location_lock
    }

    # Part D: Enhanced character details with detailed bible
    character_details = "Primary talent remains visually consistent across all scenes."
    if enhanced_bible and hasattr(enhanced_bible, 'characters'):
        # Use detailed character bible
        try:
            from services.google.character_bible import inject_character_consistency
            # Inject character details into the description
            desc_with_char = inject_character_consistency(desc_tgt or desc_vi, enhanced_bible)
            # Extract just the character block for character_details field
            if '\n\n' in desc_with_char:
                char_block = desc_with_char.split('\n\n')[0]
                character_details = char_block
        except Exception as e:
            # Log the error for debugging but continue with fallback
            import sys
            print(f"[WARN] Character bible injection failed: {e}", file=sys.stderr)
            # Intentional fallback to basic character_details - continue processing
    elif character_bible and isinstance(character_bible, list) and len(character_bible)>0:
        # Use basic character bible
        main = character_bible[0]
        nm = main.get("name",""); role = main.get("role",""); key = main.get("key_trait",""); mot = main.get("motivation","")
        character_details = f"{nm} ({role}) — trait: {key}; motivation: {mot}. Keep appearance and demeanor consistent."

    vo_text = (desc_tgt or desc_vi or "").strip()
    # Part D: NEVER truncate voiceover - prompt optimizer will handle this
    # if len(vo_text)>240: vo_text = vo_text[:240] + "…"

    # Build voiceover config with prosody settings
    voiceover_config = {
        "language": lang_code or "vi",
        "voice_hint": "neutral_narrative",
        "pace": 1.0,
        "text": vo_text
    }
    
    # Add voice prosody settings if provided
    if voice_settings:
        voiceover_config.update({
            "speaking_style": voice_settings.get("speaking_style", "storytelling"),
            "rate_multiplier": voice_settings.get("rate_multiplier", 1.0),
            "pitch_adjust": voice_settings.get("pitch_adjust", 0),
            "expressiveness": voice_settings.get("expressiveness", 0.5)
        })

    data = {
        "scene_id": f"s{scene_index:02d}",
        "objective": "Generate a short video clip for this scene based on screenplay and prompts.",
        "persona": {
            "role": "Creative Video Director",
            "tone": "Cinematic and evocative",
            "knowledge_level": "Expert in visual storytelling"
        },
        "constraints": {
            "duration_seconds": seconds,
            "aspect_ratio": ratio_str,
            "resolution": resolution,
            "visual_style_tags": style_tags,
            "camera": { "fps": 24, "lens_hint": "50mm look", "stabilization": "steady tripod-like" }
        },
        "assets": { "images": {} },
        "hard_locks": hard_locks,
        "character_details": character_details,
        "setting_details": _build_setting_details(location_context),
        "key_action": (desc_tgt or desc_vi or "").strip(),
        "camera_direction": segments,
        "audio": {
            "voiceover": voiceover_config,
            "music_bed": "subtle, minimal, non-intrusive"
        },
        "graphics": {
            "subtitles": { "enabled": True, "language": lang_code or "vi", "style": "clean small caps, bottom-safe" },
            "on_screen_text": []
        },
        "negatives": [
            "Do NOT change character identity, outfit, or location without instruction.",
            "Avoid jarring cuts or random background swaps.",
            "No brand logos unless present in references.",
            "No unrealistic X-ray views; use graphic overlays only."
        ],
        "generation": { "seed": __import__("random").randint(0, 2**31-1), "copies": copies },
        "localization": { "vi": {"prompt": (desc_vi or '').strip()}, "tgt": {"lang": lang_code, "prompt": (desc_tgt or desc_vi or '').strip()} }
    }
    return data

class _Worker(QObject):
    log = pyqtSignal(str)
    story_done = pyqtSignal(dict, dict)   # data, context (paths)
    job_card = pyqtSignal(dict)
    job_finished = pyqtSignal()

    def __init__(self, task, payload):
        super().__init__()
        self.task = task
        self.payload = payload
        self.should_stop = False  # PR#4: Add stop flag
        self.video_downloader = VideoDownloader(log_callback=lambda msg: self.log.emit(msg))

    def run(self):
        try:
            if self.task == "script":
                self._run_script()
            elif self.task == "video":
                self._run_video()
        except Exception as e:
            self.log.emit(f"[ERR] {e}")
        finally:
            if self.task == "video":
                self.job_finished.emit()

    def _run_script(self):
        p = self.payload
        self.log.emit("[INFO] Gọi LLM sinh kịch bản...")
        try:
            from services.llm_story_service import generate_script
        except Exception:
            from llm_story_service import generate_script
        
        # Build voice config if provided
        voice_config = None
        if p.get("tts_provider") and p.get("voice_id"):
            from services.voice_options import get_voice_config
            voice_config = get_voice_config(
                provider=p["tts_provider"],
                voice_id=p["voice_id"],
                language_code=p["out_lang_code"]
            )
        
        # Generate script with voice and domain/topic settings
        data = generate_script(
            idea=p["idea"], 
            style=p["style"], 
            duration_seconds=p["duration"],
            provider=p["provider"], 
            output_lang=p["out_lang_code"],
            domain=p.get("domain"),
            topic=p.get("topic"),
            voice_config=voice_config
        )
        # auto-save to folders
        st = cfg.load()
        root = st.get("download_root") or ""
        if not root:
            root = os.path.join(os.path.expanduser("~"), "Downloads")
            self.log.emit("[WARN] Chưa cấu hình thư mục tải về trong Cài đặt, dùng Downloads mặc định.")
        title = p["project"] or data.get("title_vi") or data.get("title_tgt") or "Project"
        os.makedirs(root, exist_ok=True)
        prj_dir = os.path.join(root, title); os.makedirs(prj_dir, exist_ok=True)
        dir_script = os.path.join(prj_dir, "01_KichBan"); os.makedirs(dir_script, exist_ok=True)
        dir_prompts= os.path.join(prj_dir, "02_Prompts"); os.makedirs(dir_prompts, exist_ok=True)
        dir_videos = os.path.join(prj_dir, "03_Videos"); os.makedirs(dir_videos, exist_ok=True)

        try:
            with open(os.path.join(dir_script, "screenplay_vi.txt"), "w", encoding="utf-8") as f:
                f.write(data.get("screenplay_vi",""))
            with open(os.path.join(dir_script, "screenplay_tgt.txt"), "w", encoding="utf-8") as f:
                f.write(data.get("screenplay_tgt",""))
            with open(os.path.join(dir_script, "outline_vi.txt"), "w", encoding="utf-8") as f:
                f.write(data.get("outline_vi",""))
            with open(os.path.join(dir_script, "character_bible.json"), "w", encoding="utf-8") as f:
                json.dump(data.get("character_bible",[]), f, ensure_ascii=False, indent=2)
            # Save voice config and domain/topic if present
            if data.get("voice_config"):
                with open(os.path.join(dir_script, "voice_config.json"), "w", encoding="utf-8") as f:
                    json.dump(data["voice_config"], f, ensure_ascii=False, indent=2)
            if p.get("domain") and p.get("topic"):
                domain_info = {
                    "domain": p["domain"],
                    "topic": p["topic"],
                    "language": p["out_lang_code"]
                }
                with open(os.path.join(dir_script, "domain_topic.json"), "w", encoding="utf-8") as f:
                    json.dump(domain_info, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log.emit(f"[WARN] Lưu kịch bản thất bại: {e}")

        ctx = {"title": title, "prj_dir": prj_dir, "dir_script": dir_script, "dir_prompts": dir_prompts, "dir_videos": dir_videos, "scenes": data.get("scenes",[])}
        self.log.emit("[INFO] Hoàn tất sinh kịch bản & lưu file.")
        self.story_done.emit(data, ctx)

    def _download(self, url, dst_path):
        try:
            self.video_downloader.download(url, dst_path)
            return True
        except Exception as e:
            self.log.emit(f"[ERR] Download fail: {e}")
            return False

    def _make_thumb(self, video_path, out_dir, scene, copy):
        try:
            os.makedirs(out_dir, exist_ok=True)
            thumb = os.path.join(out_dir, f"thumb_c{scene}_v{copy}.jpg")
            if shutil.which("ffmpeg"):
                cmd=["ffmpeg","-y","-ss","00:00:00","-i",video_path,"-frames:v","1","-q:v","3",thumb]
                subprocess.run(cmd, check=True)
                return thumb
        except Exception as e:
            self.log.emit(f"[WARN] Tạo thumbnail lỗi: {e}")
        return ""

    def _run_video(self):
        p = self.payload
        st = cfg.load()
        tokens = st.get("tokens") or []
        project_id = st.get("default_project_id") or DEFAULT_PROJECT_ID
        client = LabsClient(tokens, on_event=None)
        copies = p["copies"]
        title = p["title"]
        dir_videos = p["dir_videos"]
        up4k = p.get("upscale_4k", False)
        quality = p.get("quality", "1080p")  # Get quality setting
        auto_download = p.get("auto_download", True)  # Get auto-download setting
        thumbs_dir = os.path.join(dir_videos, "thumbs")

        jobs = []
        # PR#5: Batch generation - make one call per scene with copies parameter (not N calls)
        for scene_idx, scene in enumerate(p["scenes"], start=1):
            ratio = scene["aspect"]
            model_key = p.get("model_key","")

            # Single API call with copies parameter (instead of N calls)
            body = {"prompt": scene["prompt"], "copies": copies, "model": model_key, "aspect_ratio": ratio}
            self.log.emit(f"[INFO] Start scene {scene_idx} with {copies} copies in one batch…")
            rc = client.start_one(body, model_key, ratio, scene["prompt"], copies=copies, project_id=project_id)

            if rc > 0:
                # Only create cards for operations that actually exist in the API response
                # The body dict is updated by client.start_one() with operation_names list
                actual_count = len(body.get("operation_names", []))
                
                if actual_count < copies:
                    self.log.emit(f"[WARN] Scene {scene_idx}: API returned {actual_count} operations but {copies} copies were requested")
                
                # Create cards only for videos that actually exist
                for copy_idx in range(1, actual_count + 1):
                    card={"scene":scene_idx,"copy":copy_idx,"status":"PROCESSING","json":scene["prompt"],"url":"","path":"","thumb":"","dir":dir_videos}
                    self.job_card.emit(card)

                    # Store card data with copy index for operation name mapping
                    # copy_idx is 1-based, so we'll use copy_idx-1 to index into operation_names (0-based)
                    job_info = {
                        'card': card,
                        'body': body,
                        'scene': scene_idx,
                        'copy': copy_idx  # 1-based index
                    }
                    jobs.append(job_info)
            else:
                # All copies failed to start
                for copy_idx in range(1, copies+1):
                    card={"scene":scene_idx,"copy":copy_idx,"status":"FAILED_START","json":scene["prompt"],"url":"","path":"","thumb":"","dir":dir_videos}
                    self.job_card.emit(card)

        # polling with improved error handling
        retry_count = {}  # Track retry attempts per operation
        download_retry_count = {}  # Track download retry attempts
        max_retries = 3
        max_download_retries = 5

        for poll_round in range(120):
            # PR#4: Check stop flag
            if self.should_stop:
                self.log.emit("[INFO] Đã dừng xử lý theo yêu cầu người dùng.")
                break

            if not jobs:
                self.log.emit("[INFO] Tất cả video đã hoàn tất hoặc thất bại.")
                break

            # Extract all operation names from all jobs
            names = []
            for job_info in jobs:
                job_dict = job_info['body']
                names.extend(job_dict.get("operation_names", []))

            # Batch check with error handling
            try:
                rs = client.batch_check_operations(names)
            except Exception as e:
                self.log.emit(f"[WARN] Lỗi kiểm tra trạng thái (vòng {poll_round + 1}): {e}")
                import time
                time.sleep(10)  # Wait longer on error before retry
                continue

            new_jobs=[]
            for job_info in jobs:
                card = job_info['card']
                job_dict = job_info['body']
                copy_idx = job_info['copy']  # 1-based copy index
                
                # Get operation names list and map this copy to its operation
                op_names = job_dict.get("operation_names", [])
                if not op_names:
                    # No operation name - keep in queue for one more iteration in case it appears
                    # Initialize skip counter if not present
                    if 'no_op_count' not in job_info:
                        job_info['no_op_count'] = 0
                    job_info['no_op_count'] += 1
                    
                    # Only skip after multiple attempts
                    if job_info['no_op_count'] > 3:
                        sc = card['scene']
                        cp = card['copy']
                        self.log.emit(f"[WARN] Cảnh {sc} video {cp}: không có operation name sau 3 lần thử")
                    else:
                        new_jobs.append(job_info)
                    continue

                # Map copy index to the correct operation name (copy_idx is 1-based, array is 0-based)
                op_index = copy_idx - 1
                if op_index >= len(op_names):
                    # This copy's operation doesn't exist - should not happen due to earlier check
                    sc = card['scene']
                    cp = card['copy']
                    self.log.emit(f"[ERR] Cảnh {sc} video {cp}: operation index {op_index} out of bounds (only {len(op_names)} operations)")
                    card["status"] = "FAILED"
                    self.job_card.emit(card)
                    continue
                
                op_name = op_names[op_index]
                op_result = rs.get(op_name) or {}
                
                # VEO3 WORKING STRUCTURE: Check raw API response
                raw_response = op_result.get('raw', {})
                status = raw_response.get('status', '')
                
                scene = card["scene"]
                copy_num = card["copy"]

                if status == 'MEDIA_GENERATION_STATUS_SUCCESSFUL':
                    # Extract video URL from correct path
                    op_metadata = raw_response.get('operation', {}).get('metadata', {})
                    video_info = op_metadata.get('video', {})
                    video_url = video_info.get('fifeUrl', '')
                    
                    if video_url:
                        card["status"] = "READY"
                        card["url"] = video_url
                        
                        self.log.emit(f"[SUCCESS] Scene {scene} Copy {copy_num}: Video ready!")
                        
                        # Download logic
                        if auto_download:
                            fn = f"{title}_scene{scene}_copy{copy_num}.mp4"
                            fp = os.path.join(dir_videos, fn)
                            
                            self.log.emit(f"[INFO] Downloading scene {scene} copy {copy_num}...")
                            
                            try:
                                if self._download(video_url, fp):
                                    card["status"] = "DOWNLOADED"
                                    card["path"] = fp
                                    
                                    thumb = self._make_thumb(fp, thumbs_dir, scene, copy_num)
                                    card["thumb"] = thumb
                                    
                                    self.log.emit(f"[SUCCESS] ✓ Downloaded: {os.path.basename(fp)}")
                                else:
                                    # Track download retries
                                    download_key = f"{scene}_{copy_num}"
                                    retries = download_retry_count.get(download_key, 0)
                                    if retries < max_download_retries:
                                        download_retry_count[download_key] = retries + 1
                                        self.log.emit(f"[WARN] Download failed, will retry ({retries + 1}/{max_download_retries})")
                                        card["status"] = "DOWNLOAD_FAILED"
                                        card["url"] = video_url
                                        self.job_card.emit(card)
                                        new_jobs.append(job_info)
                                    else:
                                        self.log.emit(f"[ERR] Download failed after {max_download_retries} attempts")
                                        card["status"] = "DOWNLOAD_FAILED"
                                        card["url"] = video_url
                                        self.job_card.emit(card)
                            except Exception as e:
                                # Track download retries for exceptions
                                download_key = f"{scene}_{copy_num}"
                                retries = download_retry_count.get(download_key, 0)
                                if retries < max_download_retries:
                                    download_retry_count[download_key] = retries + 1
                                    self.log.emit(f"[ERR] Download error: {e} - will retry ({retries + 1}/{max_download_retries})")
                                    card["status"] = "DOWNLOAD_FAILED"
                                    card["url"] = video_url
                                    self.job_card.emit(card)
                                    new_jobs.append(job_info)
                                else:
                                    self.log.emit(f"[ERR] Download error after {max_download_retries} attempts: {e}")
                                    card["status"] = "DOWNLOAD_FAILED"
                                    card["url"] = video_url
                                    self.job_card.emit(card)
                        
                        self.job_card.emit(card)
                    else:
                        # Video marked successful but no URL - this is an error state
                        self.log.emit(f"[ERR] Scene {scene} Copy {copy_num}: No video URL in response")
                        card["status"] = "DONE_NO_URL"
                        self.job_card.emit(card)
                
                elif status == 'MEDIA_GENERATION_STATUS_FAILED':
                    card["status"] = "FAILED"
                    self.log.emit(f"[ERR] Scene {scene} Copy {copy_num} FAILED")
                    self.job_card.emit(card)
                
                else:
                    # Still processing (PENDING, ACTIVE, or other states)
                    card["status"] = "PROCESSING"
                    self.job_card.emit(card)
                    new_jobs.append(job_info)

            jobs=new_jobs

            if jobs:
                poll_info = f"vòng {poll_round + 1}/120"
                self.log.emit(f"[INFO] Đang chờ {len(jobs)} video ({poll_info})...")
                try:
                    import time
                    time.sleep(5)
                except Exception:
                    pass

        # 4K upscale

        if up4k:
            has_ffmpeg = shutil.which("ffmpeg") is not None
            if not has_ffmpeg:
                self.log.emit("[WARN] Không tìm thấy ffmpeg trong PATH — bỏ qua upscale 4K.")
            else:
                for job_info in jobs:
                    card = job_info['card']
                    if card.get("path"):
                        src=card["path"]
                        dst=src.replace(".mp4","_4k.mp4")
                        cmd=["ffmpeg","-y","-i",src,"-vf","scale=3840:-2","-c:v","libx264","-preset","fast",dst]
                        try:
                            subprocess.run(cmd, check=True)
                            card["path"]=dst
                            card["status"]="UPSCALED_4K"
                            self.job_card.emit(card)
                        except Exception as e:
                            self.log.emit(f"[ERR] 4K upscale fail: {e}")
