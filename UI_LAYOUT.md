# Text2Video Panel UI Layout

## Updated Layout with Voice Selection + Domain/Topic Features

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Text2Video Panel                                       │
├──────────────────────────────┬──────────────────────────────────────────────────┤
│ LEFT COLUMN (1/3)            │ RIGHT COLUMN (2/3)                               │
│                              │                                                  │
│ ┌──────────────────────────┐ │ ┌────────────────────────────────────────────┐  │
│ │ Tên dự án:               │ │ │  Tabs:                                     │  │
│ │ [_____________________]  │ │ │  📝 Chi tiết kịch bản | 📖 Character Bible │  │
│ └──────────────────────────┘ │ │  🎬 Kết quả cảnh | 📺 Thumbnail | 📱 Social │  │
│                              │ │                                             │  │
│ ┌──────────────────────────┐ │ │  [Content area for selected tab]           │  │
│ │ Ý tưởng (đoạn văn):      │ │ │                                             │  │
│ │ ┌──────────────────────┐ │ │ │                                             │  │
│ │ │                      │ │ │ │                                             │  │
│ │ │  [Text input area]   │ │ │ │                                             │  │
│ │ │                      │ │ │ │                                             │  │
│ │ └──────────────────────┘ │ │ │                                             │  │
│ └──────────────────────────┘ │ │                                             │  │
│                              │ │                                             │  │
│ Phong cách video: [Điện ảnh▼]│ │                                             │  │
│                              │ │                                             │  │
│ Thời lượng (s): [100]        │ │                                             │  │
│ Ngôn ngữ: [Tiếng Việt ▼]    │ │                                             │  │
│                              │ │                                             │  │
│ Tỉ lệ: [16:9 ▼]             │ │                                             │  │
│ Số video/cảnh: [1]           │ │                                             │  │
│                              │ │                                             │  │
│ Model tạo video: [veo_3_1...▼]│ │                                            │  │
│                              │ │                                             │  │
│ ☑ Up Scale 4K                │ │                                             │  │
│                              │ │                                             │  │
│ ┌──────────────────────────┐ │ │                                             │  │
│ │ 🎙️ Voice Settings        │ │ │                                             │  │
│ ├──────────────────────────┤ │ │                                             │  │
│ │ TTS Provider:            │ │ │                                             │  │
│ │ [Google TTS           ▼] │ │ │                                             │  │
│ │                          │ │ │                                             │  │
│ │ Voice:                   │ │ │                                             │  │
│ │ [🇻🇳 Nam Miền Bắc (Std)▼] │ │ │                                             │  │
│ │                          │ │ │                                             │  │
│ │ Custom Voice:            │ │ │                                             │  │
│ │ [__________________]     │ │ │                                             │  │
│ └──────────────────────────┘ │ │                                             │  │
│                              │ │                                             │  │
│ ┌──────────────────────────┐ │ │                                             │  │
│ │ 🎯 Lĩnh vực & Chủ đề     │ │ │                                             │  │
│ ├──────────────────────────┤ │ │                                             │  │
│ │ Lĩnh vực:                │ │ │                                             │  │
│ │ [Marketing & Branding ▼] │ │ │                                             │  │
│ │                          │ │ │                                             │  │
│ │ Chủ đề:                  │ │ │                                             │  │
│ │ [Giới thiệu sản phẩm  ▼] │ │ │                                             │  │
│ │                          │ │ │                                             │  │
│ │ 📝 System Prompt Preview:│ │ │                                             │  │
│ │ ┌──────────────────────┐ │ │ │                                             │  │
│ │ │Tôi là chuyên gia     │ │ │ │                                             │  │
│ │ │Marketing chuyên về   │ │ │ │                                             │  │
│ │ │ra mắt sản phẩm mới...│ │ │ │                                             │  │
│ │ └──────────────────────┘ │ │ │                                             │  │
│ └──────────────────────────┘ │ │                                             │  │
│                              │ │                                             │  │
│ ┌──────────────────────────┐ │ │                                             │  │
│ │ ⬇️ Tải video             │ │ │                                             │  │
│ ├──────────────────────────┤ │ │                                             │  │
│ │ ☑ Tự động tải video      │ │ │                                             │  │
│ │ Chất lượng: [1080p ▼]   │ │ │                                             │  │
│ │ Thư mục: ~/Videos    [📁]│ │ │                                             │  │
│ └──────────────────────────┘ │ │                                             │  │
│                              │ │                                             │  │
│ ┌──────────────────────────┐ │ │                                             │  │
│ │ ⚡ Tạo video tự động     │ │ │                                             │  │
│ │    (3 bước)          [⏹]│ │ │                                             │  │
│ └──────────────────────────┘ │ │                                             │  │
│                              │ │                                             │  │
│ ┌──────────────────────────┐ │ │                                             │  │
│ │ 📁 Mở thư mục dự án      │ │ │                                             │  │
│ └──────────────────────────┘ │ │                                             │  │
│                              │ │                                             │  │
│ Console:                     │ │                                             │  │
│ ┌──────────────────────────┐ │ │                                             │  │
│ │[INFO] Ready...           │ │ │                                             │  │
│ │                          │ │ │                                             │  │
│ └──────────────────────────┘ │ └────────────────────────────────────────────┘  │
│                              │                                                  │
└──────────────────────────────┴──────────────────────────────────────────────────┘
```

## New Components Details

### 1. Voice Settings Group (NEW)

```
┌─────────────────────────────┐
│ 🎙️ Voice Settings           │
├─────────────────────────────┤
│ TTS Provider:               │
│ [Google TTS            ▼]   │  ← Dropdown: Google TTS | ElevenLabs
│                             │
│ Voice:                      │
│ [🇻🇳 Nam Miền Bắc      ▼]   │  ← Dynamic dropdown (updates with provider/language)
│                             │     Shows flag emoji and descriptive name
│ Custom Voice:               │
│ [_____________________]     │  ← Optional: Override with custom voice ID
└─────────────────────────────┘
```

**Features:**
- TTS Provider dropdown switches between Google TTS and ElevenLabs
- Voice dropdown automatically updates when:
  - User changes TTS provider
  - User changes output language (for Google TTS)
- Custom Voice field allows manual voice ID entry
- Voice names include emoji flags for visual recognition

**Google TTS Voice Examples:**
- 🇻🇳 Nam Miền Bắc (Standard) → `vi-VN-Standard-A`
- 🇻🇳 Nữ Miền Nam (Standard) → `vi-VN-Standard-B`
- 🇻🇳 Nam Wavenet (Premium) → `vi-VN-Wavenet-A`
- 🇺🇸 Male (Neural) → `en-US-Neural2-A`
- 🇬🇧 Female British (Neural) → `en-GB-Neural2-B`

**ElevenLabs Voice Examples:**
- Adam (Deep & Authoritative)
- Rachel (Calm Narration)
- Antoni (Young & Energetic)
- Bella (Soft & Friendly)

### 2. Domain & Topic Group (NEW)

```
┌─────────────────────────────┐
│ 🎯 Lĩnh vực & Chủ đề        │
├─────────────────────────────┤
│ Lĩnh vực:                   │
│ [Marketing & Branding  ▼]   │  ← Domain dropdown (6 options)
│                             │
│ Chủ đề:                     │
│ [Giới thiệu sản phẩm   ▼]   │  ← Topic dropdown (cascades from domain)
│                             │     Disabled until domain selected
│ 📝 System Prompt Preview:   │
│ ┌─────────────────────────┐ │
│ │Tôi là chuyên gia        │ │  ← Read-only preview area
│ │Marketing chuyên về ra   │ │     Updates when topic selected
│ │mắt sản phẩm mới. Tôi có │ │     Shows Vietnamese or English
│ │10 năm kinh nghiệm...    │ │     based on output language
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**Features:**
- Domain dropdown with 6 categories
- Topic dropdown cascades from domain selection
  - Disabled when no domain selected
  - Shows placeholder text: "(Chọn lĩnh vực để load chủ đề)"
  - Updates with 3 topics per domain when domain selected
- System Prompt Preview shows expert prompt
  - Read-only text area
  - Updates automatically on topic selection
  - Language matches output language setting
  - Scrollable for long prompts

**Cascading Behavior:**
```
User selects: Marketing & Branding
    ↓
Topic dropdown activates with:
    - Giới thiệu sản phẩm
    - Xây dựng thương hiệu
    - Quảng cáo sản phẩm
    ↓
User selects: Giới thiệu sản phẩm
    ↓
Preview shows:
    "Tôi là chuyên gia Marketing chuyên về
     ra mắt sản phẩm mới. Tôi có 10 năm
     kinh nghiệm trong việc tạo ra các
     chiến dịch giới thiệu sản phẩm..."
```

## User Interaction Flow

### Voice Selection Flow

1. User opens Text2Video panel
2. Default: Google TTS with Vietnamese voice selected
3. User can:
   - Change TTS provider → Voice list updates immediately
   - Change output language → Voice list updates (Google TTS only)
   - Select voice from dropdown
   - Enter custom voice ID (advanced)

### Domain/Topic Selection Flow

1. User sees "(Không chọn)" in domain dropdown by default
2. User selects domain (e.g., "Marketing & Branding")
   - Topic dropdown enables
   - Shows "(Chọn chủ đề)" placeholder
3. User selects topic (e.g., "Giới thiệu sản phẩm")
   - Preview area updates with system prompt
4. User can change selections anytime
   - Domain change clears topic and preview
   - Topic change updates preview

### Script Generation Flow

1. User fills in project details and idea
2. User selects voice settings (optional but recommended)
3. User selects domain/topic (optional for specialized content)
4. User clicks "⚡ Tạo video tự động (3 bước)"
5. System:
   - Builds voice config from selections
   - Prepends expert intro if domain/topic selected
   - Calls LLM to generate script
   - Saves voice config and domain/topic to project files
   - Uses consistent voice across all scenes

## Visual Improvements

- **Emoji Icons**: Make sections easily identifiable
  - 🎙️ Voice Settings
  - 🎯 Domain & Topic
  - ⬇️ Download Settings
- **Group Boxes**: Clear visual separation of features
- **Cascading Dropdowns**: Intuitive hierarchical selection
- **Preview Area**: Immediate feedback on selections
- **Consistent Layout**: Follows existing panel style
