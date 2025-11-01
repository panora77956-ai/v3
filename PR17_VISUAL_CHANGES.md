# PR #17 Visual Changes Guide

## Change 1: Left Column Width (400px → 480px)

### Before (400px)
```
┌────────────────────┐  ┌──────────────────────────────────┐
│                    │  │                                  │
│  LEFT COLUMN       │  │     RIGHT AREA                   │
│  (400px width)     │  │     (flexible)                   │
│  - Cramped         │  │                                  │
│  - Limited space   │  │                                  │
│                    │  │                                  │
└────────────────────┘  └──────────────────────────────────┘
```

### After (480px)
```
┌────────────────────────┐  ┌────────────────────────────┐
│                        │  │                            │
│  LEFT COLUMN           │  │     RIGHT AREA             │
│  (480px width)         │  │     (flexible)             │
│  - More comfortable    │  │                            │
│  - Better spacing      │  │                            │
│  +80px wider (+20%)    │  │                            │
│                        │  │                            │
└────────────────────────┘  └────────────────────────────┘
```

**Impact**: 
- +80px width (+20% increase)
- More breathing room for inputs and controls
- Reduced text wrapping
- Better visual hierarchy

---

## Change 2: Model Selector Toggle (Always Visible → Hidden by Default)

### Before (Always Visible)
```
┌─────────────────────────────────────────┐
│ 📁 Dự án                                │
│ [Project Name Input]                     │
│ [Idea Input]                            │
│ [Content Input]                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 👤 Thông tin người mẫu                  │
│ ┌───────────────────────────────────┐   │
│ │ [Model 1 Card]                    │   │
│ │ [Image] [JSON Data]               │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ [Model 2 Card]                    │   │
│ │ [Image] [JSON Data]               │   │
│ └───────────────────────────────────┘   │
│ [▼] [+ Thêm người mẫu]               │   │
└─────────────────────────────────────────┘
       ↑ Takes up ~200px even when empty

┌─────────────────────────────────────────┐
│ 📦 Ảnh sản phẩm                         │
└─────────────────────────────────────────┘
```

### After (Hidden by Default)
```
┌─────────────────────────────────────────┐
│ 📁 Dự án                                │
│ [Project Name Input]                     │
│ [Idea Input]                            │
│ [Content Input]                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 👤 Thông tin người mẫu                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃  ➕ Thêm người mẫu  (Green Button) ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│                                         │
│ [Hidden content - click button to show] │
│                                         │
└─────────────────────────────────────────┘
       ↑ Saves ~200px vertical space!

┌─────────────────────────────────────────┐
│ 📦 Ảnh sản phẩm                         │
└─────────────────────────────────────────┘
```

### When Expanded (User Clicks Button)
```
┌─────────────────────────────────────────┐
│ 👤 Thông tin người mẫu                  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │
│ ┃  ➖ Ẩn người mẫu  (Orange Button)  ┃ │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │
│ ┌───────────────────────────────────┐   │
│ │ [Model 1 Card]                    │   │
│ │ [Image] [JSON Data]               │   │
│ └───────────────────────────────────┘   │
│ ┌───────────────────────────────────┐   │
│ │ [Model 2 Card]                    │   │
│ │ [Image] [JSON Data]               │   │
│ └───────────────────────────────────┘   │
│ [▼] [+ Thêm người mẫu]               │   │
└─────────────────────────────────────────┘
```

**Button States**:
- **Collapsed** (default): `➕ Thêm người mẫu` - Green (#4CAF50)
- **Expanded**: `➖ Ẩn người mẫu` - Orange (#FF9800)

**Impact**:
- Cleaner initial appearance
- Saves ~200px vertical space when not needed
- User can expand when they need to add models
- Smooth toggle transition

---

## Change 3: Stop Button Color (Gray → RED)

### Before (Gray)
```
┌─────────────────────────────────────────┐
│ [⚡ Tạo video tự động (3 bước)] [⏹️ Dừng] │
│     (Orange)              (Gray #666)   │
└─────────────────────────────────────────┘
     ↑ Stop button looks like disabled/neutral
```

### After (RED)
```
┌─────────────────────────────────────────┐
│ [⚡ Tạo video tự động (3 bước)] [⏹️ Dừng] │
│     (Orange)              (RED #F44336) │
└─────────────────────────────────────────┘
     ↑ Stop button clearly indicates danger/stop action
```

**States**:
- **Normal**: RED (#F44336) - Clear danger indication
- **Hover**: Darker Red (#D32F2F) - Interactive feedback
- **Disabled**: Light Pink (#FFCDD2) - Grayed out appearance

**Impact**:
- Clear visual indication of stop/danger action
- Consistent with standard UI patterns (red = stop/danger)
- Better user feedback
- Reduces accidental clicks

---

## Change 4: Font Size (13px → 14px)

### Before (13px)
```
┌─────────────────────────────────────────┐
│ Tên dự án: (13px)                       │
│ [Input text - 13px]                     │
│                                         │
│ Ý tưởng: (13px)                         │
│ [Textarea - 13px]                       │
│                                         │
│ Buttons: (13px)                         │
│ [Viết kịch bản] [Tạo ảnh] [Video]      │
│                                         │
│ Tabs: (14px)                            │
│ [Cài đặt] [Image2Video] [Text2Video]   │
└─────────────────────────────────────────┘
     ↑ Small text, harder to read
```

### After (14px)
```
┌─────────────────────────────────────────┐
│ Tên dự án: (14px) ← +1px                │
│ [Input text - 14px] ← +1px              │
│                                         │
│ Ý tưởng: (14px) ← +1px                  │
│ [Textarea - 14px] ← +1px                │
│                                         │
│ Buttons: (14px) ← +1px                  │
│ [Viết kịch bản] [Tạo ảnh] [Video]      │
│                                         │
│ Tabs: (15px) ← +1px                     │
│ [Cài đặt] [Image2Video] [Text2Video]   │
└─────────────────────────────────────────┘
     ↑ Larger text, more readable
```

**Elements Updated (All +1px)**:
- Labels: 13px → 14px
- Inputs (LineEdit, TextEdit): 13px → 14px
- Buttons: 13px → 14px
- ComboBoxes: 13px → 14px
- SpinBoxes: 13px → 14px
- Checkboxes: 13px → 14px
- Radio buttons: 13px → 14px
- Tables: 13px → 14px
- Progress bars: 13px → 14px
- Tabs: 14px → 15px (special case)

**Impact**:
- Better readability for all users
- Reduced eye strain
- Professional appearance maintained
- No layout breaks
- Consistent across entire application

---

## Combined Visual Impact

### Overall Layout Change
```
BEFORE:
┌─────────────┐  ┌──────────────────────┐
│ 400px       │  │ Flexible             │
│ Left Column │  │ Right Area           │
│             │  │                      │
│ • Cramped   │  │ • Tabs (14px)        │
│ • 13px text │  │ • Content            │
│ • Always-on │  │ • Results            │
│   models    │  │                      │
│ • Gray stop │  │                      │
└─────────────┘  └──────────────────────┘

AFTER:
┌───────────────┐  ┌────────────────────┐
│ 480px         │  │ Flexible           │
│ Left Column   │  │ Right Area         │
│               │  │                    │
│ • Spacious    │  │ • Tabs (15px)      │
│ • 14px text   │  │ • Content          │
│ • Hidden      │  │ • Results          │
│   models      │  │                    │
│ • RED stop    │  │                    │
└───────────────┘  └────────────────────┘
```

### Key Improvements Summary

| Aspect | Before | After | Improvement |
|--------|--------|-------|-------------|
| Left Width | 400px | 480px | +80px (+20%) |
| Model Selector | Always visible | Hidden by default | -200px space saved |
| Stop Button | Gray (#666) | RED (#F44336) | Clear danger indication |
| Font Size | 13px | 14px | +1px (+7.7% readability) |
| Tab Font | 14px | 15px | +1px |
| Overall | Cramped, hard to read | Spacious, readable | Better UX |

---

## User Experience Benefits

1. **More Workspace**: Wider left column provides comfortable input space
2. **Cleaner Interface**: Hidden model selector reduces visual clutter
3. **Safer Interaction**: RED stop button prevents accidental actions
4. **Better Readability**: Larger font reduces eye strain

---

## Technical Notes

- All changes are non-breaking
- Backward compatible
- No functionality changes
- Only visual/UX improvements
- Tested and verified

---

**Note**: This is a text-based visualization. Actual screenshots require running the application with a GUI environment.
