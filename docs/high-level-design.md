# 🏗️ SuKyToanThuAI — High-Level Design

> Hệ thống AI Hỗ trợ Trực quan hóa Nội dung Lịch sử
> Ngày tạo: 28/04/2026

---

## 1. Sơ đồ Kiến trúc Tổng thể (System Architecture)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          👤 USERS (Browser / Mobile)                        │
│                                                                             │
│                    ┌──────────────────────────────┐                         │
│                    │   SuKyToanThuAI_Web (React)  │                         │
│                    │   Vite + TailwindCSS          │                         │
│                    │   Port: 5173 (dev)            │                         │
│                    └──────────────┬───────────────┘                         │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │ HTTP (REST API)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     🌐 API GATEWAY — Nginx (:8000)                          │
│                                                                              │
│   /api/v1/auth/*       → Auth Service (:8001)                                │
│   /api/v1/content/*    → Content Service (:8002)                             │
│   /api/v1/media/*      → Media Service (:8003)                               │
│   /api/v1/education/*  → Education Service (:8004)                           │
│   /api/v1/workspace/*  → Workspace Service (:8005)                           │
└────┬──────────┬──────────────┬──────────────┬──────────────┬─────────────────┘
     │          │              │              │              │
     ▼          ▼              ▼              ▼              ▼
┌─────────┐┌──────────┐┌────────────┐┌────────────┐┌─────────────┐
│  Auth   ││ Content  ││   Media    ││ Education  ││  Workspace  │
│ Service ││ Service  ││  Service   ││  Service   ││   Service   │
│ :8001   ││ :8002    ││  :8003     ││  :8004     ││   :8005     │
│         ││          ││            ││            ││             │
│ FastAPI ││ FastAPI  ││  FastAPI   ││  FastAPI   ││  FastAPI    │
│ Python  ││ Python   ││  Python    ││  Python    ││  Python     │
└────┬────┘└────┬─────┘└─────┬──────┘└─────┬──────┘└──────┬──────┘
     │          │            │             │              │
     └──────────┴────────────┴─────────────┴──────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │   🐘 Supabase PostgreSQL     │
              │   (Shared DB, Logical Owner) │
              │   21 Tables + Enums          │
              └──────────────────────────────┘
```

---

## 2. Sơ đồ Luồng Dữ liệu Chính (Data Flow)

### 2.1. Tính năng 1 & 2: Tạo Slide/Comic

```
┌──────────┐     ┌─────────────────────────────────────────────────────────┐
│          │     │                  CONTENT SERVICE                        │
│   USER   │     │                                                         │
│          │     │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│ Chọn sự  │────▶│  │/moderate │─▶│/enhance  │─▶│/keywords │─▶│/outline│  │
│ kiện     │     │  │Kiểm duyệt│  │Làm mượt  │  │Trích xuất│  │Tạo     │  │
│ HOẶC     │     │  │nội dung  │  │nội dung  │  │keyword   │  │scenes[]│  │
│ Nhập text│     │  └──────────┘  └──────────┘  └──────────┘  └───┬────┘  │
│          │     │                                                 │       │
└──────────┘     └─────────────────────────────────────────────────┼───────┘
                                                                   │
                                                          scenes[] │
                                                                   ▼
                 ┌─────────────────────────────────────────────────────────┐
                 │                   MEDIA SERVICE                         │
                 │                                                         │
                 │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
                 │  │ Keyword      │  │ Wikimedia    │  │ Filter       │  │
                 │  │ Service      │─▶│ Service      │─▶│ Service      │  │
                 │  │              │  │              │  │              │  │
                 │  │ AI (Groq)    │  │ Commons API  │  │ Quality +    │  │
                 │  │ sinh keyword │  │ tìm ảnh      │  │ AI Relevance │  │
                 │  │ tiếng Anh    │  │ lịch sử      │  │ Scoring      │  │
                 │  └──────────────┘  └──────────────┘  └──────┬───────┘  │
                 │                                             │          │
                 └─────────────────────────────────────────────┼──────────┘
                                                               │
                                                      images[] │
                                                               ▼
┌──────────┐     ┌─────────────────────────────────────────────────────────┐
│          │     │                 WORKSPACE SERVICE                        │
│   USER   │◀───│                                                          │
│          │     │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│ Preview  │     │  │ Lưu Project  │  │ Version      │  │ Export       │  │
│ & Export │     │  │ (slides/     │  │ Control      │  │ PDF / PPTX   │  │
│          │     │  │  chapters)   │  │              │  │ PNG / HTML   │  │
│          │     │  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────┘     └─────────────────────────────────────────────────────────┘
```

### 2.2. Tính năng 3: Quiz & Flashcard

```
┌──────────┐     ┌─────────────────────────────────────────────────────────┐
│          │     │                EDUCATION SERVICE                         │
│   USER   │────▶│                                                         │
│          │     │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│ Ôn tập   │     │  │ Quiz         │  │ Flashcard    │  │ SM-2         │  │
│ Luyện thi│     │  │ Generator    │  │ Generator    │  │ Algorithm    │  │
│          │     │  │ (AI tạo quiz)│  │ (AI tạo thẻ) │  │ (Lặp cách   │  │
│          │◀───│  │              │  │              │  │  quãng)      │  │
│          │     │  └──────────────┘  └──────────────┘  └──────────────┘  │
│          │     │                         │                               │
└──────────┘     └─────────────────────────┼───────────────────────────────┘
                                           │ (Cần ảnh minh họa?)
                                           ▼
                                   ┌──────────────┐
                                   │ MEDIA SERVICE │
                                   │ /quiz-image   │
                                   └──────────────┘
```

---

## 3. Chi tiết từng Service

### 3.1. Auth Service (:8001)

```
┌─────────────────────────────────────────────┐
│              AUTH SERVICE                     │
│                                              │
│  Endpoints:                                  │
│  ├── POST /auth/register    → Đăng ký       │
│  ├── POST /auth/login       → Đăng nhập     │
│  ├── GET  /auth/me          → Thông tin user │
│  │                                           │
│  │  Admin:                                   │
│  ├── GET    /auth/admin/users     → DS user  │
│  └── DELETE /auth/admin/users/:id → Xóa user│
│                                              │
│  Tables owned:                               │
│  ├── users                                   │
│  └── user_settings                           │
│                                              │
│  Tech: JWT Token, bcrypt password hash       │
└─────────────────────────────────────────────┘
```

### 3.2. Content Service (:8002)

```
┌─────────────────────────────────────────────────────┐
│              CONTENT SERVICE                         │
│                                                      │
│  User Endpoints:                                     │
│  ├── POST /content/moderate    → Kiểm duyệt text    │
│  ├── POST /content/enhance     → Làm mượt nội dung  │
│  ├── GET  /content/keywords    → Trích xuất keyword  │
│  ├── POST /content/outline     → Tạo outline/scenes  │
│  └── POST /content/regenerate  → Tạo lại nội dung   │
│                                                      │
│  Admin Endpoints:                                    │
│  ├── POST /content/admin/categories     → Tạo DM     │
│  ├── PUT  /content/admin/categories/:id → Sửa DM     │
│  ├── POST /content/admin/events         → Tạo SK     │
│  ├── PUT  /content/admin/events/:id     → Sửa SK     │
│  └── DEL  /content/admin/events/:id     → Xóa SK     │
│                                                      │
│  Tables owned:                                       │
│  ├── categories                                      │
│  ├── historical_events (nội dung từ SGK)             │
│  ├── event_categories                                │
│  └── user_contents                                   │
│                                                      │
│  AI: Groq LLM (moderate, enhance, outline)           │
│  Nguồn nội dung: Sách giáo khoa Lịch sử             │
└─────────────────────────────────────────────────────┘
```

### 3.3. Media Service (:8003) — 🔥 Phần của bạn

```
┌─────────────────────────────────────────────────────┐
│              MEDIA SERVICE                           │
│                                                      │
│  Endpoints:                                          │
│  ├── POST /media/generate-assets  → 🔥 API chính    │
│  ├── POST /media/regenerate-image → Đổi ảnh         │
│  ├── GET  /media/search           → Search thủ công  │
│  ├── GET  /media/categories       → Danh mục         │
│  └── POST /media/quiz-image       → Ảnh cho quiz    │
│                                                      │
│  Internal Services:                                  │
│  ┌─────────────────────────────────────────────┐     │
│  │ keyword_service  → AI sinh keyword tiếng Anh│     │
│  │ wikimedia_service→ Gọi Wikimedia Commons API│     │
│  │ filter_service   → Lọc chất lượng + AI rank │     │
│  │ asset_service    → Orchestrator tổng hợp    │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  Tables READ: historical_events, categories          │
│  Tables WRITE: slides.image_url, story_chapters.*    │
│                projects.thumbnail_url                │
│                quiz_questions.question_image_url      │
│                                                      │
│  External API: Wikimedia Commons                     │
│  AI: Groq LLM (keyword gen + relevance scoring)     │
└─────────────────────────────────────────────────────┘
```

### 3.4. Education Service (:8004)

```
┌─────────────────────────────────────────────────────┐
│              EDUCATION SERVICE                       │
│                                                      │
│  Endpoints:                                          │
│  ├── POST /education/quiz       → Tạo quiz          │
│  ├── POST /education/flashcard  → Tạo flashcard     │
│  └── GET  /education/history    → Lịch sử học tập   │
│                                                      │
│  Tables owned:                                       │
│  ├── quiz_sets, quiz_questions, quiz_options         │
│  ├── quiz_attempts, quiz_attempt_details             │
│  ├── flashcard_decks, flashcards                     │
│  └── flashcard_progress (SM-2 algorithm)             │
│                                                      │
│  AI: Groq LLM (sinh quiz + flashcard từ nội dung)   │
└─────────────────────────────────────────────────────┘
```

### 3.5. Workspace Service (:8005)

```
┌─────────────────────────────────────────────────────┐
│              WORKSPACE SERVICE                       │
│                                                      │
│  Endpoints:                                          │
│  ├── POST /workspace/projects      → Tạo project    │
│  ├── GET  /workspace/projects      → DS project      │
│  ├── GET  /workspace/projects/:id  → Chi tiết        │
│  ├── POST /workspace/export/pptx   → Xuất PPTX      │
│  └── POST /workspace/export/pdf    → Xuất PDF        │
│                                                      │
│  Tables owned:                                       │
│  ├── projects                                        │
│  ├── slides                                          │
│  ├── story_chapters                                  │
│  ├── project_versions                                │
│  └── project_exports                                 │
└─────────────────────────────────────────────────────┘
```

---

## 4. Sơ đồ Database (Entity Relationship — Simplified)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        SUPABASE POSTGRESQL                               │
│                                                                          │
│  ┌─── User Domain ───┐   ┌─── Content Domain ──────────────────────┐    │
│  │                    │   │                                         │    │
│  │  users ◄──────────┼───┤  categories (danh mục, cây phân cấp)   │    │
│  │    │               │   │       │                                 │    │
│  │  user_settings     │   │  event_categories (N-N)                │    │
│  │                    │   │       │                                 │    │
│  └────────────────────┘   │  historical_events (sự kiện SGK)      │    │
│           │               │       │                                 │    │
│           │               │  user_contents (nội dung user nhập)    │    │
│           │               └─────────────────────────────────────────┘    │
│           │                       │                                      │
│           ▼                       ▼                                      │
│  ┌─── Chat Domain ────┐   ┌─── Project Domain ─────────────────────┐   │
│  │                     │   │                                        │   │
│  │  conversations ◄────┼───┤  projects                              │   │
│  │       │             │   │    ├── slides (image_url, content)     │   │
│  │  messages           │   │    ├── story_chapters (panels_data)    │   │
│  │                     │   │    ├── project_versions                │   │
│  └─────────────────────┘   │    └── project_exports                 │   │
│                            └────────────────────────────────────────┘   │
│           │                       │                                      │
│           ▼                       ▼                                      │
│  ┌─── Quiz Domain ─────────────────────────────────────────────────┐    │
│  │                                                                  │    │
│  │  quiz_sets → quiz_questions → quiz_options                      │    │
│  │                │                                                 │    │
│  │  quiz_attempts → quiz_attempt_details                           │    │
│  │                                                                  │    │
│  │  flashcard_decks → flashcards → flashcard_progress (SM-2)       │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─── AI Domain ───────────────────────────────────────────────────┐    │
│  │  prompt_templates    ai_tasks (tracking token, cost, errors)    │    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Sơ đồ Giao tiếp giữa các Service (Inter-Service Communication)

```
                        ┌──────────────┐
                        │   Frontend   │
                        │   (React)    │
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │   Nginx Gateway     │
                    │   (:8000)           │
                    └──┬──┬──┬──┬──┬─────┘
                       │  │  │  │  │
          ┌────────────┘  │  │  │  └────────────┐
          ▼               ▼  │  ▼               ▼
    ┌──────────┐  ┌─────────┐│┌──────────┐┌──────────┐
    │  Auth    │  │ Content ││ │Education │ │Workspace │
    │ :8001    │  │ :8002   │││ :8004    │ │ :8005    │
    └──────────┘  └────┬────┘│└────┬─────┘ └──────────┘
                       │     │     │
                       │     ▼     │
                       │ ┌────────────┐
                       └▶│  Media     │◀┘
                  scenes[]│  :8003    │ quiz-image
                         └─────┬──────┘
                               │
                    ┌──────────▼──────────┐
                    │  External Services  │
                    │                     │
                    │  🌐 Wikimedia       │
                    │     Commons API     │
                    │                     │
                    │  🤖 Groq LLM API   │
                    │     (Free tier)     │
                    └─────────────────────┘
```

### Luồng gọi giữa services:

| Từ              | Đến             | Dữ liệu              | Khi nào                          |
| :-------------- | :-------------- | :-------------------- | :------------------------------- |
| Content Service | Media Service   | `scenes[]`            | Sau khi tạo xong outline         |
| Education Svc   | Media Service   | quiz question context | Khi quiz cần ảnh minh họa        |
| Frontend        | Media Service   | regenerate request    | User bấm "Đổi ảnh"              |
| Media Service   | Wikimedia API   | search keywords       | Tìm ảnh lịch sử                 |
| Media Service   | Groq LLM API   | prompts               | Sinh keyword + chấm điểm ảnh    |
| All Services    | Supabase DB     | SQL queries           | CRUD dữ liệu                    |

---

## 6. Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        TECHNOLOGY STACK                          │
├─────────────────┬───────────────────────────────────────────────┤
│ Frontend        │ React + Vite + TailwindCSS                    │
│ Backend         │ Python 3.11+ / FastAPI (5 microservices)      │
│ API Gateway     │ Nginx (reverse proxy, load balancing)         │
│ Database        │ Supabase PostgreSQL 15+                       │
│ AI / LLM        │ Groq (llama-3.3-70b-versatile) — FREE        │
│ Image Source    │ Wikimedia Commons API (CC license)            │
│ HTTP Client     │ httpx (async)                                 │
│ ORM             │ SQLAlchemy 2.0+                               │
│ Validation      │ Pydantic v2                                   │
│ Auth            │ JWT (JSON Web Token)                          │
│ Containerization│ Docker + Docker Compose                       │
│ Content Source  │ Sách giáo khoa Lịch sử (nhập bởi Admin)      │
└─────────────────┴───────────────────────────────────────────────┘
```

---

## 7. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Compose Cluster                         │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ nginx    │  │ auth     │  │ content  │  │ media    │        │
│  │ :8000    │  │ :8001    │  │ :8002    │  │ :8003    │        │
│  │ (alpine) │  │ (python) │  │ (python) │  │ (python) │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
│  ┌──────────┐  ┌──────────┐                                     │
│  │education │  │workspace │                                     │
│  │ :8004    │  │ :8005    │                                     │
│  │ (python) │  │ (python) │                                     │
│  └──────────┘  └──────────┘                                     │
│                                                                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │   Supabase Cloud        │
              │   (PostgreSQL + Auth)   │
              │   Managed by team       │
              └─────────────────────────┘
```

---

## 8. Phân công Team (5 người)

| Người | Service           | Trách nhiệm chính                                    |
| :---- | :---------------- | :---------------------------------------------------- |
| 1     | Auth Service      | Đăng ký, đăng nhập, JWT, Admin quản lý user          |
| 2     | Content Service   | AI xử lý text, outline, moderate, DB sự kiện từ SGK  |
| **3** | **Media Service** | **Tìm ảnh Wikimedia, AI keyword, filter, ranking**   |
| 4     | Education Service | Quiz, flashcard, SM-2 spaced repetition               |
| 5     | Workspace Service | Lưu project, version control, export PDF/PPTX         |
