# SuKyToanThuAI - API Contract & JSON Standards

> Tài liệu chuẩn hóa JSON format cho toàn bộ microservices.
> Tất cả services PHẢI tuân theo các quy ước này.

---

## 1. RESPONSE FORMAT CHUẨN (Bắt buộc cho mọi endpoint)

### 1.1 Success Response

```json
{
  "success": true,
  "message": "Mô tả ngắn gọn",
  "data": { ... },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-28T10:00:00Z"
  }
}
```

### 1.2 Success Response với Pagination

```json
{
  "success": true,
  "message": "Lấy danh sách thành công",
  "data": [ ... ],
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-28T10:00:00Z"
  },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8
  }
}
```

### 1.3 Error Response

```json
{
  "success": false,
  "message": "Mô tả lỗi cho user",
  "error": {
    "code": "VALIDATION_ERROR",
    "details": [
      {
        "field": "email",
        "message": "Email không hợp lệ"
      }
    ]
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "2026-04-28T10:00:00Z"
  }
}
```

### 1.4 Error Codes chuẩn

| Code | HTTP Status | Mô tả |
|------|-------------|--------|
| `VALIDATION_ERROR` | 422 | Dữ liệu đầu vào không hợp lệ |
| `UNAUTHORIZED` | 401 | Chưa đăng nhập / Token hết hạn |
| `FORBIDDEN` | 403 | Không có quyền truy cập |
| `NOT_FOUND` | 404 | Không tìm thấy resource |
| `CONFLICT` | 409 | Dữ liệu bị trùng (email đã tồn tại) |
| `RATE_LIMITED` | 429 | Vượt quá giới hạn request |
| `AI_SERVICE_ERROR` | 502 | Lỗi từ OpenAI/Groq API |
| `CREDIT_EXHAUSTED` | 402 | Hết credit gọi AI |
| `CONTENT_FLAGGED` | 451 | Nội dung bị cắm cờ (vi phạm) |
| `INTERNAL_ERROR` | 500 | Lỗi server nội bộ |

---

## 2. AUTH SERVICE - JSON Contracts

### POST /api/v1/auth/register

Request:
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "fullname": "Nguyễn Văn A",
  "role": "student"
}
```

Response:
```json
{
  "success": true,
  "message": "Đăng ký thành công",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "fullname": "Nguyễn Văn A",
      "role": "student",
      "credit_balance": 100,
      "created_at": "2026-04-28T10:00:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 604800
  }
}
```

### POST /api/v1/auth/login

Request:
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

Response:
```json
{
  "success": true,
  "message": "Đăng nhập thành công",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "fullname": "Nguyễn Văn A",
      "role": "student",
      "avatar_url": null,
      "credit_balance": 95,
      "language_preference": "vi"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 604800
  }
}
```

### GET /api/v1/auth/me

Headers: `Authorization: Bearer <token>`

Response:
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "fullname": "Nguyễn Văn A",
    "role": "student",
    "avatar_url": null,
    "credit_balance": 95,
    "language_preference": "vi",
    "is_active": true,
    "last_login_at": "2026-04-28T09:00:00Z",
    "created_at": "2026-04-20T10:00:00Z",
    "settings": {
      "default_slide_style": null,
      "default_comic_style": null,
      "preferred_ai_model": "llama-3.3-70b-versatile",
      "theme": "auto",
      "notifications_enabled": true
    }
  }
}
```

---

## 3. CONTENT SERVICE - JSON Contracts

### POST /api/v1/content/moderate

Request:
```json
{
  "text": "Nội dung người dùng nhập vào...",
  "language": "vi"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "confidence_score": 0.87,
    "flags": [],
    "analysis": {
      "toxicity": false,
      "historical_accuracy": "high",
      "factual_issues": [],
      "suggestions": []
    }
  }
}
```

Response (nội dung bị cắm cờ):
```json
{
  "success": true,
  "data": {
    "is_valid": false,
    "confidence_score": 0.35,
    "flags": ["low_accuracy", "unverified_claims"],
    "analysis": {
      "toxicity": false,
      "historical_accuracy": "low",
      "factual_issues": [
        {
          "text": "Trận Điện Biên Phủ diễn ra năm 1960",
          "issue": "Sai năm. Trận Điện Biên Phủ diễn ra năm 1954",
          "severity": "high"
        }
      ],
      "suggestions": [
        "Kiểm tra lại mốc thời gian của sự kiện"
      ]
    }
  }
}
```

### POST /api/v1/content/enhance

Request:
```json
{
  "text": "Đoạn text thô cần làm mượt...",
  "style": "storytelling",
  "language": "vi"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "original_text": "Đoạn text thô...",
    "enhanced_text": "Đoạn text đã được viết lại theo phong cách storytelling...",
    "style_applied": "storytelling",
    "word_count": {
      "original": 120,
      "enhanced": 185
    }
  }
}
```

### POST /api/v1/content/outline

Request:
```json
{
  "source_type": "event",
  "source_id": "uuid-of-event",
  "output_type": "slide",
  "style": "storytelling",
  "detail_level": "detailed",
  "language": "vi",
  "custom_instructions": "Tập trung vào chiến thuật quân sự"
}
```

Response (Slide outline):
```json
{
  "success": true,
  "data": {
    "outline_type": "slide",
    "title": "Chiến thắng Điện Biên Phủ 1954",
    "total_slides": 8,
    "estimated_duration": "15 phút",
    "slides": [
      {
        "slide_order": 1,
        "layout_type": "title",
        "title": "Chiến thắng Điện Biên Phủ",
        "content": "Trận đánh quyết định kết thúc chiến tranh Đông Dương",
        "speaker_notes": "Giới thiệu tổng quan về trận đánh...",
        "image_suggestion": "Panorama thung lũng Điện Biên Phủ"
      },
      {
        "slide_order": 2,
        "layout_type": "content",
        "title": "Bối cảnh lịch sử",
        "content": "Sau 8 năm kháng chiến chống Pháp...",
        "speaker_notes": "Trình bày bối cảnh...",
        "image_suggestion": "Bản đồ Đông Dương 1954"
      }
    ]
  }
}
```

Response (Comic outline):
```json
{
  "success": true,
  "data": {
    "outline_type": "comic",
    "title": "Chiến thắng Điện Biên Phủ 1954",
    "total_chapters": 3,
    "chapters": [
      {
        "chapter_no": 1,
        "title": "Kế hoạch táo bạo",
        "narration": "Mùa đông 1953, tại chiến khu Việt Bắc...",
        "panel_count": 4,
        "panels": [
          {
            "panel_no": 1,
            "description": "Đại tướng Võ Nguyên Giáp đứng trước bản đồ chiến thuật",
            "dialogue": "Chúng ta sẽ thay đổi phương châm: đánh chắc, tiến chắc!",
            "image_suggestion": "Tướng Giáp chỉ bản đồ, phong cách manga lịch sử"
          },
          {
            "panel_no": 2,
            "description": "Hàng ngàn dân công kéo pháo qua đèo",
            "dialogue": null,
            "image_suggestion": "Dân công kéo pháo lên núi, góc nhìn rộng"
          }
        ]
      }
    ]
  }
}
```

---

## 4. MEDIA SERVICE - JSON Contracts

### POST /api/v1/media/search

Request:
```json
{
  "keywords": [
    {
      "keyword_en": "Dien Bien Phu",
      "category": "location"
    },
    {
      "keyword_en": "Vo Nguyen Giap",
      "category": "person"
    }
  ],
  "max_results": 10,
  "min_width": 800,
  "license_filter": ["cc-by", "cc-by-sa", "public-domain"]
}
```

Response:
```json
{
  "success": true,
  "data": {
    "images": [
      {
        "id": "wikimedia-file-id",
        "title": "Battle of Dien Bien Phu.jpg",
        "url": "https://upload.wikimedia.org/...",
        "thumbnail_url": "https://upload.wikimedia.org/.../300px-...",
        "width": 1200,
        "height": 800,
        "license": "public-domain",
        "author": "Unknown",
        "source_url": "https://commons.wikimedia.org/wiki/File:...",
        "relevance_score": 0.91,
        "matched_keyword": "Dien Bien Phu"
      }
    ],
    "total_found": 5
  }
}
```

### POST /api/v1/media/generate-assets

Request:
```json
{
  "project_id": "uuid",
  "slides": [
    {
      "slide_order": 1,
      "image_suggestion": "Panorama thung lũng Điện Biên Phủ"
    },
    {
      "slide_order": 2,
      "image_suggestion": "Bản đồ Đông Dương 1954"
    }
  ]
}
```

Response:
```json
{
  "success": true,
  "data": {
    "assets": [
      {
        "slide_order": 1,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "public-domain"
      },
      {
        "slide_order": 2,
        "image_url": "https://upload.wikimedia.org/...",
        "source": "wikimedia",
        "license": "cc-by-sa"
      }
    ],
    "total_matched": 2,
    "total_requested": 2
  }
}
```

---

## 5. EDUCATION SERVICE - JSON Contracts

### POST /api/v1/education/quiz

Request:
```json
{
  "source_type": "event",
  "source_id": "uuid-of-event",
  "question_count": 10,
  "difficulty": "mixed",
  "question_types": ["multiple_choice", "true_false"],
  "language": "vi"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "quiz_set": {
      "id": "uuid",
      "title": "Quiz: Chiến thắng Điện Biên Phủ",
      "description": "Bộ câu hỏi trắc nghiệm về trận Điện Biên Phủ 1954",
      "source_type": "event",
      "difficulty": "mixed",
      "question_count": 10,
      "time_limit_seconds": 600,
      "questions": [
        {
          "id": "uuid",
          "question_order": 1,
          "question_type": "multiple_choice",
          "question_text": "Trận Điện Biên Phủ diễn ra vào năm nào?",
          "difficulty": "easy",
          "points": 1,
          "hint": "Đây là năm ký Hiệp định Geneva",
          "options": [
            {
              "id": "uuid",
              "option_order": 1,
              "option_text": "1953",
              "is_correct": false
            },
            {
              "id": "uuid",
              "option_order": 2,
              "option_text": "1954",
              "is_correct": true
            },
            {
              "id": "uuid",
              "option_order": 3,
              "option_text": "1955",
              "is_correct": false
            },
            {
              "id": "uuid",
              "option_order": 4,
              "option_text": "1956",
              "is_correct": false
            }
          ],
          "explanation": "Chiến dịch Điện Biên Phủ diễn ra từ 13/3 đến 7/5/1954"
        },
        {
          "id": "uuid",
          "question_order": 2,
          "question_type": "true_false",
          "question_text": "Đại tướng Võ Nguyên Giáp là Tổng tư lệnh chiến dịch Điện Biên Phủ",
          "difficulty": "easy",
          "points": 1,
          "options": [
            {
              "id": "uuid",
              "option_order": 1,
              "option_text": "Đúng",
              "is_correct": true
            },
            {
              "id": "uuid",
              "option_order": 2,
              "option_text": "Sai",
              "is_correct": false
            }
          ],
          "explanation": "Đại tướng Võ Nguyên Giáp trực tiếp chỉ huy chiến dịch"
        }
      ]
    }
  }
}
```

### POST /api/v1/education/quiz/submit

Request:
```json
{
  "quiz_set_id": "uuid",
  "answers": [
    {
      "question_id": "uuid",
      "selected_option_id": "uuid",
      "time_spent_seconds": 15
    },
    {
      "question_id": "uuid",
      "selected_option_id": "uuid",
      "time_spent_seconds": 22
    }
  ],
  "total_time_seconds": 320
}
```

Response:
```json
{
  "success": true,
  "data": {
    "attempt": {
      "id": "uuid",
      "quiz_set_id": "uuid",
      "score": 80.00,
      "correct_count": 8,
      "total_questions": 10,
      "time_spent_seconds": 320,
      "status": "completed",
      "details": [
        {
          "question_id": "uuid",
          "question_text": "Trận Điện Biên Phủ diễn ra vào năm nào?",
          "selected_option_id": "uuid",
          "selected_text": "1954",
          "is_correct": true,
          "correct_answer": "1954",
          "explanation": "Chiến dịch diễn ra từ 13/3 đến 7/5/1954"
        }
      ]
    }
  }
}
```

### POST /api/v1/education/flashcard

Request:
```json
{
  "source_type": "event",
  "source_id": "uuid-of-event",
  "card_count": 15,
  "language": "vi"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "deck": {
      "id": "uuid",
      "title": "Flashcard: Chiến thắng Điện Biên Phủ",
      "description": "Bộ thẻ ghi nhớ về trận Điện Biên Phủ 1954",
      "source_type": "event",
      "card_count": 15,
      "cards": [
        {
          "id": "uuid",
          "card_order": 1,
          "front_text": "Ai là Tổng tư lệnh chiến dịch Điện Biên Phủ?",
          "back_text": "Đại tướng Võ Nguyên Giáp",
          "difficulty": "easy",
          "tags": ["nhân vật", "quân sự"]
        },
        {
          "id": "uuid",
          "card_order": 2,
          "front_text": "Chiến dịch Điện Biên Phủ kéo dài bao nhiêu ngày?",
          "back_text": "56 ngày đêm (13/3 - 7/5/1954)",
          "difficulty": "medium",
          "tags": ["thời gian", "chiến dịch"]
        }
      ]
    }
  }
}
```

### PUT /api/v1/education/flashcard/progress

Request (SM-2 Algorithm update):
```json
{
  "flashcard_id": "uuid",
  "quality": 4
}
```

> quality: 0-5 theo SM-2 (0=quên hoàn toàn, 5=nhớ rõ)

Response:
```json
{
  "success": true,
  "data": {
    "flashcard_id": "uuid",
    "ease_factor": 2.60,
    "interval_days": 6,
    "repetitions": 3,
    "next_review_at": "2026-05-04T10:00:00Z"
  }
}
```

---

## 6. WORKSPACE SERVICE - JSON Contracts

### POST /api/v1/workspace/projects

Request:
```json
{
  "title": "Chiến thắng Điện Biên Phủ - Slide",
  "description": "Bài thuyết trình về trận Điện Biên Phủ 1954",
  "type": "slide",
  "ref_event_id": "uuid-of-event",
  "language": "vi",
  "style_config": {
    "style": "storytelling",
    "detail_level": "detailed",
    "color_theme": "warm"
  },
  "outline": {
    "slides": [
      {
        "slide_order": 1,
        "layout_type": "title",
        "title": "Chiến thắng Điện Biên Phủ",
        "content": "Trận đánh quyết định...",
        "speaker_notes": "...",
        "image_url": "https://..."
      }
    ]
  }
}
```

Response:
```json
{
  "success": true,
  "message": "Tạo project thành công",
  "data": {
    "project": {
      "id": "uuid",
      "title": "Chiến thắng Điện Biên Phủ - Slide",
      "type": "slide",
      "status": "preview",
      "total_items": 8,
      "thumbnail_url": null,
      "created_at": "2026-04-28T10:00:00Z"
    }
  }
}
```

### GET /api/v1/workspace/projects

Query params: `?page=1&page_size=20&status=completed&type=slide`

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "title": "Chiến thắng Điện Biên Phủ - Slide",
      "type": "slide",
      "status": "completed",
      "total_items": 8,
      "thumbnail_url": "https://...",
      "is_public": false,
      "view_count": 12,
      "created_at": "2026-04-28T10:00:00Z",
      "updated_at": "2026-04-28T11:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 5,
    "total_pages": 1
  }
}
```

### GET /api/v1/workspace/projects/{id}

Response:
```json
{
  "success": true,
  "data": {
    "project": {
      "id": "uuid",
      "title": "Chiến thắng Điện Biên Phủ - Slide",
      "description": "Bài thuyết trình...",
      "type": "slide",
      "status": "completed",
      "language": "vi",
      "style_config": { "style": "storytelling" },
      "total_items": 8,
      "is_public": false,
      "created_at": "2026-04-28T10:00:00Z"
    },
    "slides": [
      {
        "id": "uuid",
        "slide_order": 1,
        "title": "Chiến thắng Điện Biên Phủ",
        "content": "Trận đánh quyết định...",
        "speaker_notes": "...",
        "layout_type": "title",
        "image_url": "https://...",
        "ai_generated": true
      }
    ]
  }
}
```

### POST /api/v1/workspace/export/pptx

Request:
```json
{
  "project_id": "uuid"
}
```

Response:
```json
{
  "success": true,
  "data": {
    "export": {
      "id": "uuid",
      "project_id": "uuid",
      "format": "pptx",
      "status": "completed",
      "file_url": "https://supabase-storage.../exports/project-uuid.pptx",
      "file_size_bytes": 2458624,
      "created_at": "2026-04-28T10:05:00Z"
    }
  }
}
```

---

## 7. SHARED CONVENTIONS

### 7.1 DateTime Format
- Luôn dùng ISO 8601 với timezone: `2026-04-28T10:00:00Z`
- Backend lưu TIMESTAMPTZ, trả về UTC

### 7.2 ID Format
- Luôn dùng UUID v4: `"550e8400-e29b-41d4-a716-446655440000"`

### 7.3 Pagination Query Params
- `page` (default: 1)
- `page_size` (default: 20, max: 100)
- `sort_by` (default: "created_at")
- `sort_order` (default: "desc")

### 7.4 Authentication Header
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

### 7.5 JWT Payload chuẩn
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "role": "student",
  "exp": 1714300800,
  "iat": 1713696000
}
```

### 7.6 Naming Conventions
- URL paths: `kebab-case` → `/api/v1/content/keywords`
- JSON keys: `snake_case` → `"created_at"`, `"quiz_set_id"`
- Enum values: `snake_case` → `"multiple_choice"`, `"in_progress"`
