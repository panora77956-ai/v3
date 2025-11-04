# Voice Selection + Domain/Topic System Prompts Feature

## Overview

This feature adds professional voice selection and domain-specific system prompts to improve video generation quality on the Text2Video tab.

## Features

### 1. Voice Selection with Dual TTS Provider Support

#### Supported Providers

1. **Google Text-to-Speech** (Free, Multi-language)
   - Vietnamese: 4 voices (Standard & Wavenet)
   - English: 4 voices (Neural2, US & GB)
   - Japanese: 2 voices (Neural2)
   - Korean: 2 voices (Neural2)
   - Chinese: 2 voices (Standard)

2. **ElevenLabs** (Premium Quality, Natural Voices)
   - Adam (Deep & Authoritative)
   - Rachel (Calm Narration)
   - Antoni (Young & Energetic)
   - Bella (Soft & Friendly)
   - Elli (Warm & Professional)
   - Josh (Natural & Conversational)

#### GUI Components

The Voice Settings panel includes:
- TTS Provider dropdown (Google TTS / ElevenLabs)
- Voice selection dropdown (auto-updates based on provider and language)
- Custom Voice input field (optional override with manual voice ID)

#### Behavior

- Voice list automatically updates when:
  - User changes TTS provider
  - User changes output language (for Google TTS only)
- Custom voice input allows advanced users to specify voice IDs not in the preset list
- Voice configuration is saved with the project for consistency across all scenes

### 2. Domain & Topic Based System Prompts

#### Available Domains and Topics

1. **Marketing & Branding**
   - Giới thiệu sản phẩm (Product Introduction)
   - Xây dựng thương hiệu (Brand Building)
   - Quảng cáo sản phẩm (Product Advertising)

2. **Công nghệ & AI (Technology & AI)**
   - Hướng dẫn lập trình (Programming Tutorials)
   - Giải thích AI/ML (AI/ML Explanation)
   - Review công nghệ (Technology Review)

3. **Giáo dục & Đào tạo (Education & Training)**
   - Giảng dạy trực tuyến (Online Teaching)
   - Kỹ năng mềm (Soft Skills)
   - Hướng nghiệp (Career Guidance)

4. **Sức khỏe & Thể hình (Health & Fitness)**
   - Tập luyện tại nhà (Home Workout)
   - Dinh dưỡng (Nutrition)
   - Yoga & Thiền (Yoga & Meditation)

5. **Kinh doanh & Khởi nghiệp (Business & Startup)**
   - Khởi nghiệp từ con số 0 (Starting from Scratch)
   - Quản trị doanh nghiệp (Business Management)
   - Marketing online (Online Marketing)

6. **Du lịch & Ẩm thực (Travel & Food)**
   - Review địa điểm du lịch (Travel Destination Reviews)
   - Hướng dẫn nấu ăn (Cooking Tutorials)
   - Food review (Food Reviews)

#### GUI Components

The Domain & Topic panel includes:
- Domain dropdown (Lĩnh vực)
- Topic dropdown (Chủ đề) - cascades from domain selection
- System Prompt Preview - read-only text area showing the expert prompt

#### Behavior

1. User selects **Domain** → Topic dropdown updates with relevant topics
2. User selects **Topic** → System prompt preview displays
3. When generating script, the expert introduction is prepended:

   ```
   Tôi là chuyên gia [domain] chuyên về [topic]. 
   Tôi đã nhận ý tưởng từ bạn và sẽ biến nó thành 
   kịch bản video [topic] chuyên nghiệp theo yêu cầu của bạn. 
   
   [System Prompt]
   
   Kịch bản như sau:
   ```

#### Bilingual Support

- System prompts available in both Vietnamese (vi) and English (en)
- Automatically selects appropriate language based on output language setting
- Non-English output languages (ja, ko, zh, etc.) use English prompts

## Technical Implementation

### New Files

1. **`services/voice_options.py`**
   - Voice configurations for Google TTS & ElevenLabs
   - Helper functions: `get_voices_for_provider()`, `get_default_voice()`, `get_voice_config()`

2. **`services/domain_prompts.py`**
   - Hardcoded domain/topic/prompt data from Google Sheet
   - Helper functions: `get_all_domains()`, `get_topics_for_domain()`, `get_system_prompt()`, `build_expert_intro()`
   - Future-ready placeholder for Google Sheets API integration

### Modified Files

1. **`ui/text2video_panel.py`**
   - Added Voice Settings group box
   - Added Domain & Topic group box
   - Added signal handlers for cascading updates
   - Added methods: `_on_tts_provider_changed()`, `_on_language_changed()`, `_on_domain_changed()`, `_on_topic_changed()`, `_update_voice_list()`

2. **`services/llm_story_service.py`**
   - Updated `generate_script()` to accept `domain`, `topic`, and `voice_config` parameters
   - Prepends expert intro to LLM prompt when domain/topic selected
   - Stores voice config in result data

3. **`ui/text2video_panel_impl.py`**
   - Updated `_run_script()` to build voice config and pass domain/topic to script generation
   - Saves voice config and domain/topic info to project files (`voice_config.json`, `domain_topic.json`)

## Usage

### Basic Workflow

1. Open the Text2Video tab
2. Enter your project name and video idea
3. **Select Voice Settings:**
   - Choose TTS Provider (Google TTS or ElevenLabs)
   - Select voice from dropdown (updates based on output language)
   - Optionally enter custom voice ID
4. **Select Domain & Topic (Optional):**
   - Choose domain from dropdown
   - Choose topic from dropdown (activates after domain selection)
   - Review system prompt in preview area
5. Click "Tạo video tự động" to generate script and videos

### Voice Consistency

- Voice configuration is saved with the project
- All scenes in the video use the same voice for consistency
- Voice settings are stored in `01_KichBan/voice_config.json`

### Domain/Topic Integration

- Domain/topic selection is optional
- When selected, expert introduction is added to script prompt
- Improves script quality with domain-specific expertise
- Domain/topic settings stored in `01_KichBan/domain_topic.json`

## Data Source

Domain/topic data is currently hardcoded from Google Sheet:
https://docs.google.com/spreadsheets/d/1ohiL6xOBbjC7La2iUdkjrVjG4IEUnVWhI0fRoarD6P0/edit?gid=1507296519#gid=1507296519

### Future Enhancement

The code includes a placeholder function `load_domain_topics_from_source()` for future dynamic loading:
- Connect to Google Sheets API
- Fetch latest data automatically
- Cache data locally
- Handle API errors gracefully

## Testing

### Module Tests

Run the integration test:
```bash
python3 /tmp/test_voice_domain_integration.py
```

Tests verify:
- Voice options module functionality
- Domain prompts module functionality
- Integration between voice selection and domain/topic
- Configuration generation

### Manual GUI Testing

1. Launch the application
2. Navigate to Text2Video tab
3. Verify Voice Settings controls appear
4. Verify Domain & Topic controls appear
5. Test TTS provider switching
6. Test voice list updates on language change
7. Test domain selection → topic list updates
8. Test topic selection → prompt preview updates
9. Generate a test video and verify voice/domain settings are saved

## Files Structure

```
project_root/
├── services/
│   ├── voice_options.py          # NEW - Voice configurations
│   ├── domain_prompts.py         # NEW - Domain/topic prompts
│   └── llm_story_service.py      # MODIFIED - Script generation
├── ui/
│   ├── text2video_panel.py       # MODIFIED - GUI components
│   └── text2video_panel_impl.py  # MODIFIED - Worker logic
└── [Project]/
    └── 01_KichBan/
        ├── voice_config.json     # Voice settings
        └── domain_topic.json     # Domain/topic selection
```

## Benefits

✅ **Consistent Voice** - Same voice across all scenes in a video
✅ **Professional Narration** - Domain-specific expertise in scripts
✅ **Automatic Expert Intro** - Contextual introduction based on domain/topic
✅ **Bilingual Support** - Vietnamese and English prompts
✅ **Easy to Extend** - Ready for Google Sheets API integration
✅ **Dual TTS Support** - Free (Google) and premium (ElevenLabs) options
✅ **Flexible Configuration** - Custom voice ID override available

## Known Limitations

- Domain/topic data is currently hardcoded (will be dynamic in future)
- ElevenLabs voices are not filtered by language (language-agnostic)
- Line length linting warnings for long Vietnamese/English prompts (acceptable)

## Future Enhancements

1. **Dynamic Data Loading**: Implement Google Sheets API integration
2. **More Domains/Topics**: Expand coverage based on user needs
3. **Voice Preview**: Add audio preview for selected voice
4. **Voice Speed/Pitch**: Add controls for voice customization
5. **Domain Recommendations**: AI-powered domain/topic suggestions based on video idea
