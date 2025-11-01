
import json
import os
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
_LANGS = [
    ("Tiếng Việt","vi"), ("Tiếng Anh","en"), ("Tiếng Nhật","ja"), ("Tiếng Hàn","ko"), ("Tiếng Trung","zh"),
    ("Tiếng Pháp","fr"), ("Tiếng Đức","de"), ("Tiếng Tây Ban Nha","es"), ("Tiếng Nga","ru"), ("Tiếng Thái","th"), ("Tiếng Indonesia","id")
]
_VIDEO_MODELS = [
    "veo_3_1_i2v_s_fast_portrait_ultra",
    "veo_3_1_i2v_s_fast_landscape_ultra",
    "veo_3_1_i2v_xl_portrait",
    "veo_3_1_i2v_xl_landscape",
]

def build_prompt_json(scene_index:int, desc_vi:str, desc_tgt:str, lang_code:str, ratio_str:str, style:str, seconds:int=8, copies:int=1, resolution_hint:str=None, character_bible=None, enhanced_bible=None):
    """
    Strict prompt JSON schema:
    - objective/persona/constraints/assets/hard_locks/character_details/setting_details/key_action/camera_direction/audio/graphics/negatives/generation
    - bilingual localization (vi + target)
    
    Part D: Now supports enhanced_bible (CharacterBible object) for detailed character consistency
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

    hard_locks = {
        "identity": "Keep the same face, body, and identity across scenes.",
        "wardrobe": "Outfit consistency is required. Do NOT change outfit, color, or add accessories without instruction.",
        "hair_makeup": "Keep hair and makeup consistent; do NOT change length or color unless explicitly instructed.",
        "location": "Keep to single coherent environment; no random background swaps."
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
        "setting_details": "Clean composition, minimal props, no clutter; coherent lighting per scene style.",
        "key_action": (desc_tgt or desc_vi or "").strip(),
        "camera_direction": segments,
        "audio": {
            "voiceover": { "language": lang_code or "vi", "voice_hint": "neutral_narrative", "pace": 1.0, "text": vo_text },
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
        data = generate_script(
            idea=p["idea"], style=p["style"], duration_seconds=p["duration"],
            provider=p["provider"], output_lang=p["out_lang_code"]
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
                # Create cards for each expected copy
                for copy_idx in range(1, copies+1):
                    card={"scene":scene_idx,"copy":copy_idx,"status":"PROCESSING","json":scene["prompt"],"url":"","path":"","thumb":"","dir":dir_videos}
                    self.job_card.emit(card)

                    # Store card data separately to avoid unhashable dict issues
                    job_info = {
                        'card': card,
                        'body': body,
                        'scene': scene_idx,
                        'copy': copy_idx
                    }
                    jobs.append(job_info)
            else:
                # All copies failed to start
                for copy_idx in range(1, copies+1):
                    card={"scene":scene_idx,"copy":copy_idx,"status":"FAILED_START","json":scene["prompt"],"url":"","path":"","thumb":"","dir":dir_videos}
                    self.job_card.emit(card)

        # polling with improved error handling
        retry_count = {}  # Track retry attempts per operation
        max_retries = 3

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
                # Get the first operation name for this job
                op_names = job_dict.get("operation_names", [])
                if not op_names:
                    # No operation name - skip this job
                    sc = card['scene']
                    cp = card['copy']
                    self.log.emit(f"[WARN] Cảnh {sc} video {cp}: không có operation name")
                    continue

                # Check status of first operation (for single copy jobs, there's only one)
                op_name = op_names[0]
                v = rs.get(op_name) or {}
                stt = v.get('status') or 'PROCESSING'

                # Update card status
                card['status']=stt
                self.job_card.emit(card)

                if stt in ('COMPLETED','DONE'):
                    # Success - try to download if auto_download enabled
                    url = (v.get('video_urls') or [None])[0]
                    if url and auto_download:
                        fn=f"{title}_canh_{card['scene']}_video_{card['copy']}_{quality}.mp4"
                        fp=os.path.join(dir_videos, fn)
                        try:
                            if self._download(url, fp):
                                card['path']=fp
                                card['status']='DOWNLOADED'
                                th=self._make_thumb(fp, thumbs_dir, card['scene'], card['copy'])
                                if th:
                                    card['thumb']=th
                                self.job_card.emit(card)
                                sc = card['scene']
                                cp = card['copy']
                                self.log.emit(f"[INFO] Đã tải video cảnh {sc} copy {cp}")
                            else:
                                scene_id = card['scene']
                                copy_id = card['copy']
                                msg = f"[WARN] Tải video thất bại: cảnh {scene_id} copy {copy_id}"
                                self.log.emit(msg)
                                card['status']='DOWNLOAD_FAILED'
                                card['url']=url
                                self.job_card.emit(card)
                        except Exception as e:
                            self.log.emit(f"[ERR] Lỗi tải video cảnh {card['scene']}: {e}")
                            card['status']='DOWNLOAD_FAILED'
                            card['url']=url
                            self.job_card.emit(card)
                    elif url:
                        # Not auto-downloading, just store URL
                        card['url']=url
                        card['status']='READY'
                        self.job_card.emit(card)
                    else:
                        scene_id = card['scene']
                        self.log.emit(f"[WARN] Video hoàn tất nhưng không có URL: cảnh {scene_id}")
                        card['status']='DONE_NO_URL'
                        self.job_card.emit(card)
                elif stt == 'FAILED':
                    # Failed - check if we should retry
                    retries = retry_count.get(op_name, 0)
                    if retries < max_retries:
                        retry_count[op_name] = retries + 1
                        scene_id = card['scene']
                        retry_info = f"lần {retries + 1}/{max_retries}"
                        self.log.emit(f"[INFO] Thử lại cảnh {scene_id} ({retry_info})...")
                        # Keep in job queue for retry
                        new_jobs.append(job_info)
                    else:
                        scene_id = card['scene']
                        copy_id = card['copy']
                        msg = f"[ERR] Cảnh {scene_id} video {copy_id} thất bại sau {max_retries} lần thử"
                        self.log.emit(msg)
                        card['status']='FAILED'
                        self.job_card.emit(card)
                else:
                    # Still processing
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
