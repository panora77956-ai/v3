# -*- coding: utf-8 -*-
import os, json, requests
from services.core.key_manager import get_key

def _load_keys():
    """Load keys using unified key manager"""
    gk = get_key('google')
    ok = get_key('openai')
    return gk, ok

def _n_scenes(total_seconds:int):
    total=max(3, int(total_seconds or 30))
    n=max(1, (total+7)//8)
    per=[8]*(n-1)+[max(1,total-8*(n-1))]
    return n, per

def _mode_from_duration(total_seconds:int):
    return "SHORT" if int(total_seconds) <= 7*60 else "LONG"

def _schema_prompt(idea, style_vi, out_lang, n, per, mode):
    base_rules = f"""
Bạn là **Biên kịch Đa năng AI**. Nhận **ý tưởng thô sơ (<10 từ)** và phát triển thành **kịch bản phim/video chuyên nghiệp**.
Bạn phải **linh hoạt chuyển đổi phong cách** theo độ dài yêu cầu.

QUÁN TRIỆT 1 — **Định danh CỐ ĐỊNH nhân vật (Character Bible)**: (2–4 nhân vật)
Mỗi nhân vật cần:
- key_trait (1–2 từ): tính cách cốt lõi không đổi
- motivation: động lực sâu thẳm
- default_behavior: hành vi mặc định khi căng thẳng/suy nghĩ
- visual_identity: đặc trưng nhận diện nhất quán
- archetype: nguyên mẫu kể chuyện (ví dụ: Anh hùng, Người dẫn đường…)
- fatal_flaw: khuyết điểm chí mạng
- goal_external: mục tiêu bên ngoài
- goal_internal: mục tiêu nội tâm

QUÁN TRIỆT 2 — **Đồng nhất tuyến nhân vật**: hành động/lời thoại là hệ quả trực tiếp từ key_trait & motivation; thay đổi chỉ dần dần (Act II–III).

PHONG CÁCH:
- **SHORT** (≤7'): 3–5 phân đoạn, nhịp nhanh/viral.
- **LONG**  (>7'): 3 Hồi đầy đủ + **Midpoint**; độ dài gợi ý 2500–3500 từ.

Luôn có **Hook mạnh** ở đầu và **Twist/Thông điệp mạnh** ở cuối.
""".strip()

    schema = f"""
Trả về **JSON hợp lệ** theo schema EXACT (không thêm ký tự ngoài JSON):

{{
  "title_vi": "Tiêu đề ngắn (VI)",
  "title_tgt": "Title in {out_lang}",
  "character_bible": [{{"name":"","role":"","key_trait":"","motivation":"","default_behavior":"","visual_identity":"","archetype":"","fatal_flaw":"","goal_external":"","goal_internal":""}}],
  "character_bible_tgt": [{{"name":"","role":"","key_trait":"","motivation":"","default_behavior":"","visual_identity":"","archetype":"","fatal_flaw":"","goal_external":"","goal_internal":""}}],
  "outline_vi": "Dàn ý tóm tắt (nêu rõ chế độ {mode}, sự kiện chính theo Hồi/Phân đoạn)",
  "outline_tgt": "Outline in {out_lang}",
  "screenplay_vi": "Screenplay (SCENE/ACTION/DIALOGUE) — tuân thủ Character Bible & chế độ {mode}, có Hook & Twist",
  "screenplay_tgt": "Screenplay in {out_lang}",
  "scenes": [
    {{
      "prompt_vi":"Mô tả ngắn (1–2 câu) bám Character Bible cho cảnh",
      "prompt_tgt":"{out_lang} version",
      "duration": 8,
      "characters": ["Tên nhân vật xuất hiện"],
      "location": "Địa điểm",
      "dialogues": [
        {{"speaker":"Tên","text_vi":"Câu thoại VI","text_tgt":"Line in {out_lang}"}}
      ]
    }}
  ]
}}
""".strip()

    return f"""{base_rules}

ĐẦU VÀO:
- Ý tưởng thô: "{idea}"
- Phong cách: "{style_vi}"
- Chế độ: {mode}
- Số cảnh kỹ thuật: {n} (mỗi cảnh 8s; cảnh cuối {per[-1]}s)
- Ngôn ngữ đích: {out_lang}

{schema}
"""

def _call_openai(prompt, api_key, model="gpt-4-turbo"):
    """FIXED: Changed from gpt-5 to gpt-4-turbo"""
    url="https://api.openai.com/v1/chat/completions"
    headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"}
    data={
        "model": model,
        "messages":[
            {"role":"system","content":"You output strictly JSON when asked."},
            {"role":"user","content": prompt}
        ],
        "response_format":{"type":"json_object"},
        "temperature":0.9
    }
    r=requests.post(url,headers=headers,json=data,timeout=240); r.raise_for_status()
    txt=r.json()["choices"][0]["message"]["content"]
    return json.loads(txt)

def _call_gemini(prompt, api_key, model="gemini-2.5-flash"):
    """
    Call Gemini API with retry logic for 503 errors
    
    Strategy:
    1. Try primary API key
    2. If 503 error, try up to 2 additional keys from config
    3. Add exponential backoff (1s, 2s, 4s)
    """
    from services.core.api_config import gemini_text_endpoint
    from services.core.key_manager import get_all_keys
    import time
    
    # Build key rotation list
    keys = [api_key]
    all_keys = get_all_keys('google')
    keys.extend([k for k in all_keys if k != api_key])
    
    last_error = None
    
    for attempt, key in enumerate(keys[:3]):  # Try up to 3 keys
        try:
            # Build endpoint
            url = gemini_text_endpoint(key) if model == "gemini-2.5-flash" else \
                  f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            
            headers = {"Content-Type": "application/json"}
            data = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.9, "response_mime_type": "application/json"}
            }
            
            # Make request
            r = requests.post(url, headers=headers, json=data, timeout=240)
            
            # Check for 503 specifically
            if r.status_code == 503:
                last_error = requests.HTTPError(f"503 Service Unavailable (Key attempt {attempt+1})", response=r)
                if attempt < 2:  # Don't sleep on last attempt
                    backoff = 2 ** attempt  # 1s, 2s, 4s
                    print(f"[WARN] Gemini 503 error, retrying in {backoff}s with next key...")
                    time.sleep(backoff)
                continue  # Try next key
            
            # Raise for other HTTP errors
            r.raise_for_status()
            
            # Parse response
            out = r.json()
            txt = out["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(txt)
            
        except requests.exceptions.HTTPError as e:
            # Only retry 503 errors
            if hasattr(e, 'response') and e.response.status_code == 503:
                last_error = e
                if attempt < 2:
                    backoff = 2 ** attempt
                    print(f"[WARN] HTTP 503, trying key {attempt+2}/{min(3, len(keys))} in {backoff}s...")
                    time.sleep(backoff)
                continue
            else:
                # Other HTTP errors (429, 400, 401, etc.) - raise immediately
                raise
                
        except Exception as e:
            # Non-HTTP errors - raise immediately
            last_error = e
            raise
    
    # All retries exhausted
    if last_error:
        raise RuntimeError(f"Gemini API failed after {min(3, len(keys))} attempts: {last_error}")
    else:
        raise RuntimeError("Gemini API failed with unknown error")

def generate_script(idea, style, duration_seconds, provider='Gemini 2.5', api_key=None, output_lang='vi'):
    gk, ok=_load_keys()
    n, per = _n_scenes(duration_seconds)
    mode = _mode_from_duration(duration_seconds)
    prompt=_schema_prompt(idea=idea, style_vi=style, out_lang=output_lang, n=n, per=per, mode=mode)
    if provider.lower().startswith("gemini"):
        key=api_key or gk
        if not key: raise RuntimeError("Chưa cấu hình Google API Key cho Gemini.")
        res=_call_gemini(prompt,key,"gemini-2.5-flash")
    else:
        key=api_key or ok
        if not key: raise RuntimeError("Chưa cấu hình OpenAI API Key cho GPT-4 Turbo.")
        # FIXED: Use gpt-4-turbo instead of gpt-5
        res=_call_openai(prompt,key,"gpt-4-turbo")
    if "scenes" not in res: raise RuntimeError("LLM không trả về đúng schema.")
    # ép durations
    for i,d in enumerate(per):
        if i < len(res["scenes"]): res["scenes"][i]["duration"]=int(d)
    return res