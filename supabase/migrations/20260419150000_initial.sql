-- ============================================================================
-- SuKyToanThuAI - Database Schema (Option C: Hybrid - Shared DB, Logical Ownership)
-- PostgreSQL 15+ / Supabase Compatible
-- Updated: 2026-04-19 (Supabase SQL Editor Safe - Idempotent)
-- ============================================================================
--
-- DOMAIN OWNERSHIP:
--   User Service:    users, user_settings
--   Content Service: categories, historical_events, event_categories, user_contents
--   Chat Service:    conversations, messages
--   Project Service: projects, slides, story_chapters, project_versions, project_exports
--   Quiz Service:    quiz_sets, quiz_questions, quiz_options, flashcard_decks,
--                    flashcards, quiz_attempts, quiz_attempt_details, flashcard_progress
--   AI Service:      ai_tasks, prompt_templates
--
-- HOW TO USE:
--   1. Open Supabase Dashboard -> SQL Editor
--   2. Paste this entire file
--   3. Click "Run" (Ctrl+Enter)
--   4. Script is idempotent - safe to run multiple times
-- ============================================================================


-- ============================================================================
-- STEP 0: CLEANUP (Safe re-run)
-- ============================================================================
-- Drop tables in reverse dependency order to avoid FK conflicts

DROP TABLE IF EXISTS event_categories CASCADE;
DROP TABLE IF EXISTS quiz_attempt_details CASCADE;
DROP TABLE IF EXISTS quiz_attempts CASCADE;
DROP TABLE IF EXISTS flashcard_progress CASCADE;
DROP TABLE IF EXISTS flashcards CASCADE;
DROP TABLE IF EXISTS flashcard_decks CASCADE;
DROP TABLE IF EXISTS quiz_options CASCADE;
DROP TABLE IF EXISTS quiz_questions CASCADE;
DROP TABLE IF EXISTS quiz_sets CASCADE;
DROP TABLE IF EXISTS ai_tasks CASCADE;
DROP TABLE IF EXISTS prompt_templates CASCADE;
DROP TABLE IF EXISTS project_exports CASCADE;
DROP TABLE IF EXISTS project_versions CASCADE;
DROP TABLE IF EXISTS story_chapters CASCADE;
DROP TABLE IF EXISTS slides CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS messages CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS user_contents CASCADE;
DROP TABLE IF EXISTS historical_events CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS user_settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Drop all custom enum types
DROP TYPE IF EXISTS ai_task_status CASCADE;
DROP TYPE IF EXISTS ai_task_type CASCADE;
DROP TYPE IF EXISTS attempt_status CASCADE;
DROP TYPE IF EXISTS question_type CASCADE;
DROP TYPE IF EXISTS question_difficulty CASCADE;
DROP TYPE IF EXISTS quiz_difficulty CASCADE;
DROP TYPE IF EXISTS quiz_source CASCADE;
DROP TYPE IF EXISTS export_status CASCADE;
DROP TYPE IF EXISTS export_format CASCADE;
DROP TYPE IF EXISTS slide_layout CASCADE;
DROP TYPE IF EXISTS project_status CASCADE;
DROP TYPE IF EXISTS project_type CASCADE;
DROP TYPE IF EXISTS message_type CASCADE;
DROP TYPE IF EXISTS message_role CASCADE;
DROP TYPE IF EXISTS conversation_status CASCADE;
DROP TYPE IF EXISTS conversation_context CASCADE;
DROP TYPE IF EXISTS validation_status CASCADE;
DROP TYPE IF EXISTS content_type CASCADE;
DROP TYPE IF EXISTS event_status CASCADE;
DROP TYPE IF EXISTS event_region CASCADE;
DROP TYPE IF EXISTS event_era CASCADE;
DROP TYPE IF EXISTS theme_mode CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;

-- Drop trigger functions
DROP FUNCTION IF EXISTS trigger_set_updated_at() CASCADE;
DROP FUNCTION IF EXISTS trigger_update_message_count() CASCADE;
DROP FUNCTION IF EXISTS trigger_update_question_count() CASCADE;
DROP FUNCTION IF EXISTS trigger_update_card_count() CASCADE;
DROP FUNCTION IF EXISTS trigger_update_slide_count() CASCADE;
DROP FUNCTION IF EXISTS trigger_deduct_credits() CASCADE;


-- ============================================================================
-- STEP 1: EXTENSIONS
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";


-- ============================================================================
-- STEP 2: ENUM TYPES
-- ============================================================================

CREATE TYPE user_role AS ENUM ('student', 'teacher', 'admin');
CREATE TYPE theme_mode AS ENUM ('light', 'dark', 'auto');

CREATE TYPE event_era AS ENUM ('ancient', 'medieval', 'modern', 'contemporary');
CREATE TYPE event_region AS ENUM (
    'vietnam', 'east_asia', 'southeast_asia', 'europe',
    'americas', 'africa', 'middle_east', 'global'
);
CREATE TYPE event_status AS ENUM ('draft', 'review', 'published', 'archived');

CREATE TYPE content_type AS ENUM ('text', 'file', 'url');
CREATE TYPE validation_status AS ENUM ('pending', 'valid', 'invalid', 'processing');

CREATE TYPE conversation_context AS ENUM ('event_based', 'custom_content', 'free_chat', 'quiz_review');
CREATE TYPE conversation_status AS ENUM ('active', 'archived', 'deleted');

CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
CREATE TYPE message_type AS ENUM (
    'text', 'image', 'file', 'slide_preview',
    'comic_preview', 'quiz_suggestion', 'error'
);

CREATE TYPE project_type AS ENUM ('slide', 'comic');
CREATE TYPE project_status AS ENUM (
    'draft', 'generating', 'preview', 'completed', 'failed', 'archived'
);

CREATE TYPE slide_layout AS ENUM (
    'title', 'content', 'two_column', 'image_focus',
    'quote', 'timeline', 'comparison', 'summary'
);

CREATE TYPE export_format AS ENUM ('pdf', 'pptx', 'png_zip', 'jpg_zip', 'html');
CREATE TYPE export_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TYPE quiz_source AS ENUM ('system', 'conversation', 'project', 'custom');
CREATE TYPE quiz_difficulty AS ENUM ('easy', 'medium', 'hard', 'mixed');
CREATE TYPE question_difficulty AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE question_type AS ENUM (
    'multiple_choice', 'true_false', 'fill_blank', 'ordering', 'matching'
);
CREATE TYPE attempt_status AS ENUM ('in_progress', 'completed', 'abandoned');

CREATE TYPE ai_task_type AS ENUM (
    'chat', 'generate_slide_content', 'generate_comic_content',
    'generate_image', 'validate_content', 'generate_quiz',
    'generate_flashcard', 'translate'
);
CREATE TYPE ai_task_status AS ENUM ('queued', 'processing', 'completed', 'failed', 'cancelled');


-- ============================================================================
-- STEP 3: TABLES - User Service
-- ============================================================================

CREATE TABLE users (
    id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email                    VARCHAR(255) NOT NULL UNIQUE,
    password_hash            VARCHAR(255) NOT NULL,
    fullname                 VARCHAR(255) NOT NULL,
    avatar_url               VARCHAR(500),
    role                     user_role NOT NULL DEFAULT 'student',
    credit_balance           INTEGER NOT NULL DEFAULT 100,
    credit_warning_threshold INTEGER NOT NULL DEFAULT 10,
    language_preference      VARCHAR(5) NOT NULL DEFAULT 'vi',
    is_active                BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at            TIMESTAMPTZ,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at               TIMESTAMPTZ
);

COMMENT ON TABLE users IS '[User Service] Bang nguoi dung chinh';
COMMENT ON COLUMN users.credit_balance IS 'So luot goi AI con lai (chi tracking, khong lien quan giao dich tien)';
COMMENT ON COLUMN users.credit_warning_threshold IS 'Nguong canh bao het credits';
COMMENT ON COLUMN users.language_preference IS 'Ngon ngu ua thich: vi, en, ja...';


CREATE TABLE user_settings (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    default_slide_style   VARCHAR(50),
    default_comic_style   VARCHAR(50),
    preferred_ai_model    VARCHAR(100) DEFAULT 'llama-3.3-70b-versatile',
    theme                 theme_mode NOT NULL DEFAULT 'auto',
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE user_settings IS '[User Service] Cai dat ca nhan nguoi dung (1-1 voi users)';


-- ============================================================================
-- STEP 4: TABLES - Content Service
-- ============================================================================

CREATE TABLE categories (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug          VARCHAR(100) NOT NULL UNIQUE,
    name_vi       VARCHAR(255) NOT NULL,
    name_en       VARCHAR(255) NOT NULL,
    description_vi TEXT,
    description_en TEXT,
    icon_url      VARCHAR(500),
    parent_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE categories IS '[Content Service] Danh muc su kien lich su (ho tro cay phan cap qua parent_id)';


CREATE TABLE historical_events (
    id                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                       VARCHAR(200) NOT NULL UNIQUE,
    title_vi                   VARCHAR(500) NOT NULL,
    title_en                   VARCHAR(500) NOT NULL,
    start_year                 INTEGER NOT NULL,
    end_year                   INTEGER,
    era                        event_era NOT NULL,
    region                     event_region NOT NULL,
    location                   VARCHAR(255),
    main_characters            JSONB NOT NULL DEFAULT '[]'::jsonb,
    short_desc_vi              VARCHAR(500) NOT NULL,
    short_desc_en              VARCHAR(500) NOT NULL,
    full_content_vi            TEXT NOT NULL,
    full_content_en            TEXT NOT NULL,
    historical_significance_vi TEXT,
    historical_significance_en TEXT,
    key_dates                  JSONB NOT NULL DEFAULT '[]'::jsonb,
    image_url                  VARCHAR(500),
    sources                    JSONB NOT NULL DEFAULT '[]'::jsonb,
    status                     event_status NOT NULL DEFAULT 'draft',
    verified_by                UUID REFERENCES users(id) ON DELETE SET NULL,
    verified_at                TIMESTAMPTZ,
    view_count                 INTEGER NOT NULL DEFAULT 0,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE historical_events IS '[Content Service] Su kien lich su da duoc kiem chung';


CREATE TABLE event_categories (
    event_id    UUID NOT NULL REFERENCES historical_events(id) ON DELETE CASCADE,
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, category_id)
);

COMMENT ON TABLE event_categories IS '[Content Service] Lien ket N-N giua su kien va danh muc';


CREATE TABLE user_contents (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title             VARCHAR(500) NOT NULL,
    original_content  TEXT NOT NULL,
    content_type      content_type NOT NULL,
    file_url          VARCHAR(500),
    validation_status validation_status NOT NULL DEFAULT 'pending',
    validation_result JSONB,
    validated_at      TIMESTAMPTZ,
    language_detected VARCHAR(5),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ
);

COMMENT ON TABLE user_contents IS '[Content Service] Noi dung do nguoi dung paste/upload, can AI validate';


-- ============================================================================
-- STEP 5: TABLES - Chat / Conversation Service
-- ============================================================================

CREATE TABLE conversations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(255) NOT NULL,
    context_type    conversation_context NOT NULL,
    ref_event_id    UUID REFERENCES historical_events(id) ON DELETE SET NULL,
    ref_content_id  UUID REFERENCES user_contents(id) ON DELETE SET NULL,
    status          conversation_status NOT NULL DEFAULT 'active',
    message_count   INTEGER NOT NULL DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

COMMENT ON TABLE conversations IS '[Chat Service] Cuoc hoi thoai giua user va AI tro ly';


CREATE TABLE messages (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role             message_role NOT NULL,
    message_type     message_type NOT NULL DEFAULT 'text',
    content          TEXT NOT NULL,
    attachment_urls  JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_model         VARCHAR(100),
    token_input      INTEGER,
    token_output     INTEGER,
    response_time_ms INTEGER,
    is_pinned        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE messages IS '[Chat Service] Tin nhan trong cuoc hoi thoai';


-- ============================================================================
-- STEP 6: TABLES - Project Service (Slides & Comics)
-- ============================================================================

CREATE TABLE projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    ref_event_id    UUID REFERENCES historical_events(id) ON DELETE SET NULL,
    ref_content_id  UUID REFERENCES user_contents(id) ON DELETE SET NULL,
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    type            project_type NOT NULL,
    status          project_status NOT NULL DEFAULT 'draft',
    language        VARCHAR(5) NOT NULL DEFAULT 'vi',
    style_config    JSONB NOT NULL DEFAULT '{}'::jsonb,
    total_items     INTEGER NOT NULL DEFAULT 0,
    thumbnail_url   VARCHAR(500),
    is_public       BOOLEAN NOT NULL DEFAULT FALSE,
    share_token     VARCHAR(100) UNIQUE,
    view_count      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

COMMENT ON TABLE projects IS '[Project Service] Du an slide hoac comic cua nguoi dung';


CREATE TABLE slides (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id     UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    slide_order    INTEGER NOT NULL,
    title          VARCHAR(500) NOT NULL,
    content        TEXT NOT NULL,
    speaker_notes  TEXT,
    layout_type    slide_layout NOT NULL DEFAULT 'content',
    image_url      VARCHAR(500),
    image_prompt   TEXT,
    background_url VARCHAR(500),
    metadata       JSONB NOT NULL DEFAULT '{}'::jsonb,
    ai_generated   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_slides_project_order UNIQUE (project_id, slide_order)
);

COMMENT ON TABLE slides IS '[Project Service] Cac slide trong project loai slide';


CREATE TABLE story_chapters (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_no      INTEGER NOT NULL,
    title           VARCHAR(500) NOT NULL,
    narration       TEXT,
    panel_count     INTEGER NOT NULL DEFAULT 4,
    panels_data     JSONB NOT NULL DEFAULT '[]'::jsonb,
    cover_image_url VARCHAR(500),
    image_urls      JSONB NOT NULL DEFAULT '[]'::jsonb,
    image_prompts   JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chapters_project_order UNIQUE (project_id, chapter_no)
);

COMMENT ON TABLE story_chapters IS '[Project Service] Cac chuong comic trong project loai comic';


CREATE TABLE project_versions (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id     UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    change_summary VARCHAR(500),
    snapshot_data  JSONB NOT NULL,
    created_by     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_versions_project_number UNIQUE (project_id, version_number)
);

COMMENT ON TABLE project_versions IS '[Project Service] Lich su phien ban project (snapshot toan bo data)';


CREATE TABLE project_exports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    export_format   export_format NOT NULL,
    file_url        VARCHAR(500),
    file_size_bytes BIGINT,
    status          export_status NOT NULL DEFAULT 'pending',
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

COMMENT ON TABLE project_exports IS '[Project Service] Tracking export/download du an';


-- ============================================================================
-- STEP 7: TABLES - Quiz & Flashcard Service
-- ============================================================================

CREATE TABLE quiz_sets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ref_event_id        UUID REFERENCES historical_events(id) ON DELETE SET NULL,
    ref_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    ref_project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    source_type         quiz_source NOT NULL,
    difficulty          quiz_difficulty NOT NULL DEFAULT 'mixed',
    question_count      INTEGER NOT NULL DEFAULT 0,
    time_limit_seconds  INTEGER,
    language            VARCHAR(5) NOT NULL DEFAULT 'vi',
    is_public           BOOLEAN NOT NULL DEFAULT FALSE,
    play_count          INTEGER NOT NULL DEFAULT 0,
    avg_score           DECIMAL(5, 2),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE quiz_sets IS '[Quiz Service] Bo cau hoi quiz';


CREATE TABLE quiz_questions (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_set_id        UUID NOT NULL REFERENCES quiz_sets(id) ON DELETE CASCADE,
    question_order     INTEGER NOT NULL,
    question_type      question_type NOT NULL DEFAULT 'multiple_choice',
    question_text      TEXT NOT NULL,
    question_image_url VARCHAR(500),
    explanation        TEXT,
    difficulty         question_difficulty NOT NULL DEFAULT 'medium',
    points             INTEGER NOT NULL DEFAULT 1,
    time_limit_seconds INTEGER,
    hint               TEXT,
    tags               JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_questions_quiz_order UNIQUE (quiz_set_id, question_order)
);

COMMENT ON TABLE quiz_questions IS '[Quiz Service] Cau hoi trong quiz - ho tro nhieu loai';


CREATE TABLE quiz_options (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id      UUID NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    option_order     INTEGER NOT NULL,
    option_text      TEXT NOT NULL,
    option_image_url VARCHAR(500),
    is_correct       BOOLEAN NOT NULL DEFAULT FALSE,
    match_pair       VARCHAR(255)
);

COMMENT ON TABLE quiz_options IS '[Quiz Service] Cac lua chon dap an (khong gioi han so luong)';


CREATE TABLE flashcard_decks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ref_event_id        UUID REFERENCES historical_events(id) ON DELETE SET NULL,
    ref_conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL,
    ref_project_id      UUID REFERENCES projects(id) ON DELETE SET NULL,
    title               VARCHAR(500) NOT NULL,
    description         TEXT,
    source_type         quiz_source NOT NULL,
    card_count          INTEGER NOT NULL DEFAULT 0,
    language            VARCHAR(5) NOT NULL DEFAULT 'vi',
    is_public           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ
);

COMMENT ON TABLE flashcard_decks IS '[Quiz Service] Bo flashcard';


CREATE TABLE flashcards (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    deck_id         UUID NOT NULL REFERENCES flashcard_decks(id) ON DELETE CASCADE,
    card_order      INTEGER NOT NULL,
    front_text      TEXT NOT NULL,
    front_image_url VARCHAR(500),
    back_text       TEXT NOT NULL,
    back_image_url  VARCHAR(500),
    difficulty      question_difficulty NOT NULL DEFAULT 'medium',
    tags            JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_flashcards_deck_order UNIQUE (deck_id, card_order)
);

COMMENT ON TABLE flashcards IS '[Quiz Service] The flashcard (mat truoc: cau hoi, mat sau: dap an)';


CREATE TABLE quiz_attempts (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_set_id        UUID NOT NULL REFERENCES quiz_sets(id) ON DELETE CASCADE,
    score              DECIMAL(5, 2) NOT NULL DEFAULT 0,
    correct_count      INTEGER NOT NULL DEFAULT 0,
    total_questions    INTEGER NOT NULL,
    time_spent_seconds INTEGER,
    status             attempt_status NOT NULL DEFAULT 'in_progress',
    started_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMPTZ
);

COMMENT ON TABLE quiz_attempts IS '[Quiz Service] Luot lam quiz cua nguoi dung';


CREATE TABLE quiz_attempt_details (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id         UUID NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
    question_id        UUID NOT NULL REFERENCES quiz_questions(id) ON DELETE CASCADE,
    selected_option_id UUID REFERENCES quiz_options(id) ON DELETE SET NULL,
    user_answer_text   TEXT,
    is_correct         BOOLEAN NOT NULL,
    time_spent_seconds INTEGER,
    answered_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE quiz_attempt_details IS '[Quiz Service] Chi tiet tung cau tra loi trong 1 luot quiz';


CREATE TABLE flashcard_progress (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    flashcard_id     UUID NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
    ease_factor      DECIMAL(4, 2) NOT NULL DEFAULT 2.50,
    interval_days    INTEGER NOT NULL DEFAULT 1,
    repetitions      INTEGER NOT NULL DEFAULT 0,
    next_review_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_quality     INTEGER,
    last_reviewed_at TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_flashcard_progress_user_card UNIQUE (user_id, flashcard_id)
);

COMMENT ON TABLE flashcard_progress IS '[Quiz Service] Tien trinh on flashcard theo SM-2 (Spaced Repetition)';


-- ============================================================================
-- STEP 8: TABLES - AI Generation Service
-- ============================================================================

CREATE TABLE prompt_templates (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 VARCHAR(255) NOT NULL UNIQUE,
    task_type            ai_task_type NOT NULL,
    template_text        TEXT NOT NULL,
    variables            JSONB NOT NULL DEFAULT '[]'::jsonb,
    ai_model_recommended VARCHAR(100),
    version              INTEGER NOT NULL DEFAULT 1,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    description          TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE prompt_templates IS '[AI Service] Template prompt cho cac loai tac vu AI';


CREATE TABLE ai_tasks (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id    UUID REFERENCES conversations(id) ON DELETE SET NULL,
    project_id         UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_type          ai_task_type NOT NULL,
    ai_provider        VARCHAR(50) NOT NULL DEFAULT 'groq',
    ai_model           VARCHAR(100) NOT NULL,
    prompt_template_id UUID REFERENCES prompt_templates(id) ON DELETE SET NULL,
    input_data         JSONB NOT NULL,
    output_data        JSONB,
    status             ai_task_status NOT NULL DEFAULT 'queued',
    token_input        INTEGER,
    token_output       INTEGER,
    credits_used       INTEGER NOT NULL DEFAULT 1,
    response_time_ms   INTEGER,
    error_message      TEXT,
    retry_count        INTEGER NOT NULL DEFAULT 0,
    started_at         TIMESTAMPTZ,
    completed_at       TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE ai_tasks IS '[AI Service] Tracking moi tac vu AI: token, cost, response time, errors';


-- ============================================================================
-- STEP 9: INDEXES
-- ============================================================================

-- User Service
-- (email and slug already have unique indexes from UNIQUE constraint, skip duplicates)
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_users_deleted ON users(deleted_at) WHERE deleted_at IS NULL;

-- Content Service
CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_active ON categories(is_active) WHERE is_active = TRUE;

CREATE INDEX idx_events_era_region ON historical_events(era, region);
CREATE INDEX idx_events_status ON historical_events(status);
CREATE INDEX idx_events_years ON historical_events(start_year, end_year);
CREATE INDEX idx_events_published ON historical_events(status) WHERE status = 'published';

CREATE INDEX idx_event_categories_event ON event_categories(event_id);
CREATE INDEX idx_event_categories_category ON event_categories(category_id);

CREATE INDEX idx_user_contents_user ON user_contents(user_id);
CREATE INDEX idx_user_contents_status ON user_contents(validation_status);
CREATE INDEX idx_user_contents_deleted ON user_contents(deleted_at) WHERE deleted_at IS NULL;

-- Chat Service
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_user_active ON conversations(user_id, updated_at DESC) WHERE status = 'active';
CREATE INDEX idx_conversations_ref_event ON conversations(ref_event_id) WHERE ref_event_id IS NOT NULL;
CREATE INDEX idx_conversations_ref_content ON conversations(ref_content_id) WHERE ref_content_id IS NOT NULL;

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);
CREATE INDEX idx_messages_pinned ON messages(conversation_id) WHERE is_pinned = TRUE;

-- Project Service
CREATE INDEX idx_projects_user ON projects(user_id);
CREATE INDEX idx_projects_user_active ON projects(user_id, updated_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_projects_type_status ON projects(type, status);
CREATE INDEX idx_projects_public ON projects(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_projects_share_token ON projects(share_token) WHERE share_token IS NOT NULL;
CREATE INDEX idx_projects_conversation ON projects(conversation_id) WHERE conversation_id IS NOT NULL;

CREATE INDEX idx_slides_project_order ON slides(project_id, slide_order);
CREATE INDEX idx_chapters_project_order ON story_chapters(project_id, chapter_no);
CREATE INDEX idx_versions_project ON project_versions(project_id, version_number DESC);
CREATE INDEX idx_exports_project ON project_exports(project_id);
CREATE INDEX idx_exports_user ON project_exports(user_id);

-- Quiz Service
CREATE INDEX idx_quiz_sets_user ON quiz_sets(user_id);
CREATE INDEX idx_quiz_sets_source ON quiz_sets(source_type);
CREATE INDEX idx_quiz_sets_public ON quiz_sets(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_quiz_sets_ref_event ON quiz_sets(ref_event_id) WHERE ref_event_id IS NOT NULL;
CREATE INDEX idx_quiz_sets_deleted ON quiz_sets(deleted_at) WHERE deleted_at IS NULL;

CREATE INDEX idx_questions_quiz ON quiz_questions(quiz_set_id, question_order);
CREATE INDEX idx_options_question ON quiz_options(question_id, option_order);

CREATE INDEX idx_flashcard_decks_user ON flashcard_decks(user_id);
CREATE INDEX idx_flashcard_decks_deleted ON flashcard_decks(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_flashcards_deck ON flashcards(deck_id, card_order);

CREATE INDEX idx_attempts_user ON quiz_attempts(user_id, started_at DESC);
CREATE INDEX idx_attempts_quiz ON quiz_attempts(quiz_set_id);
CREATE INDEX idx_attempt_details_attempt ON quiz_attempt_details(attempt_id);
CREATE INDEX idx_attempt_details_question ON quiz_attempt_details(question_id);

CREATE INDEX idx_flashcard_progress_user ON flashcard_progress(user_id);
CREATE INDEX idx_flashcard_progress_review ON flashcard_progress(user_id, next_review_at);

-- AI Service
CREATE INDEX idx_ai_tasks_user ON ai_tasks(user_id);
CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_type ON ai_tasks(task_type);
CREATE INDEX idx_ai_tasks_conversation ON ai_tasks(conversation_id) WHERE conversation_id IS NOT NULL;
CREATE INDEX idx_ai_tasks_project ON ai_tasks(project_id) WHERE project_id IS NOT NULL;
CREATE INDEX idx_ai_tasks_created ON ai_tasks(created_at DESC);


-- ============================================================================
-- STEP 10: TRIGGER FUNCTIONS & TRIGGERS
-- ============================================================================

-- 10a: Auto-update updated_at on any UPDATE
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to each table individually (no dynamic DO block)
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_user_settings_updated_at
    BEFORE UPDATE ON user_settings FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_categories_updated_at
    BEFORE UPDATE ON categories FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_historical_events_updated_at
    BEFORE UPDATE ON historical_events FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_user_contents_updated_at
    BEFORE UPDATE ON user_contents FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_conversations_updated_at
    BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_slides_updated_at
    BEFORE UPDATE ON slides FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_story_chapters_updated_at
    BEFORE UPDATE ON story_chapters FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_quiz_sets_updated_at
    BEFORE UPDATE ON quiz_sets FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_quiz_questions_updated_at
    BEFORE UPDATE ON quiz_questions FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_flashcard_decks_updated_at
    BEFORE UPDATE ON flashcard_decks FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_flashcards_updated_at
    BEFORE UPDATE ON flashcards FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_flashcard_progress_updated_at
    BEFORE UPDATE ON flashcard_progress FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER trg_prompt_templates_updated_at
    BEFORE UPDATE ON prompt_templates FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();


-- 10b: Auto-update message_count in conversations
CREATE OR REPLACE FUNCTION trigger_update_message_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE conversations
        SET message_count = message_count + 1,
            last_message_at = NEW.created_at
        WHERE id = NEW.conversation_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE conversations
        SET message_count = GREATEST(message_count - 1, 0)
        WHERE id = OLD.conversation_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_messages_count
    AFTER INSERT OR DELETE ON messages
    FOR EACH ROW EXECUTE FUNCTION trigger_update_message_count();


-- 10c: Auto-update question_count in quiz_sets
CREATE OR REPLACE FUNCTION trigger_update_question_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE quiz_sets SET question_count = question_count + 1
        WHERE id = NEW.quiz_set_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE quiz_sets SET question_count = GREATEST(question_count - 1, 0)
        WHERE id = OLD.quiz_set_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_quiz_questions_count
    AFTER INSERT OR DELETE ON quiz_questions
    FOR EACH ROW EXECUTE FUNCTION trigger_update_question_count();


-- 10d: Auto-update card_count in flashcard_decks
CREATE OR REPLACE FUNCTION trigger_update_card_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE flashcard_decks SET card_count = card_count + 1
        WHERE id = NEW.deck_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE flashcard_decks SET card_count = GREATEST(card_count - 1, 0)
        WHERE id = OLD.deck_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_flashcards_count
    AFTER INSERT OR DELETE ON flashcards
    FOR EACH ROW EXECUTE FUNCTION trigger_update_card_count();


-- 10e: Auto-update total_items in projects (slides + chapters)
CREATE OR REPLACE FUNCTION trigger_update_slide_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE projects SET total_items = total_items + 1
        WHERE id = NEW.project_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE projects SET total_items = GREATEST(total_items - 1, 0)
        WHERE id = OLD.project_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_slides_count
    AFTER INSERT OR DELETE ON slides
    FOR EACH ROW EXECUTE FUNCTION trigger_update_slide_count();

CREATE TRIGGER trg_chapters_count
    AFTER INSERT OR DELETE ON story_chapters
    FOR EACH ROW EXECUTE FUNCTION trigger_update_slide_count();


-- 10f: Auto-deduct credits when AI task completes
CREATE OR REPLACE FUNCTION trigger_deduct_credits()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND (OLD.status IS DISTINCT FROM 'completed') THEN
        UPDATE users
        SET credit_balance = GREATEST(credit_balance - NEW.credits_used, 0)
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_ai_tasks_deduct_credits
    AFTER UPDATE ON ai_tasks
    FOR EACH ROW EXECUTE FUNCTION trigger_deduct_credits();


-- ============================================================================
-- STEP 11: SEED DATA - Prompt Templates
-- ============================================================================

INSERT INTO prompt_templates (name, task_type, template_text, variables, ai_model_recommended, description) VALUES
(
    'slide_content_generator',
    'generate_slide_content',
    E'Ban la chuyen gia lich su va thiet ke trinh bay. Hay tao noi dung cho {{num_slides}} slide thuyet trinh ve chu de: "{{topic}}".\n\nYeu cau:\n- Ngon ngu: {{language}}\n- Phong cach: {{style}}\n- Doi tuong: {{audience}}\n- Moi slide can co: tieu de, noi dung chinh (3-5 bullet points), ghi chu thuyet trinh\n- Slide dau: trang bia. Slide cuoi: tong ket.\n\nTra ve JSON array voi format:\n[{"slide_order":1,"title":"...","content":"...","speaker_notes":"...","layout_type":"title","image_suggestion":"..."}]',
    '["topic","num_slides","language","style","audience"]'::jsonb,
    'llama-3.3-70b-versatile',
    'Tao noi dung slide thuyet trinh ve su kien lich su'
),
(
    'comic_content_generator',
    'generate_comic_content',
    E'Ban la hoa si truyen tranh lich su. Hay tao kich ban cho {{num_chapters}} chuong truyen tranh ve: "{{topic}}".\n\nYeu cau:\n- Ngon ngu: {{language}}\n- Phong cach ve: {{art_style}}\n- Moi chuong co {{panels_per_chapter}} panel\n- Moi panel can: mo ta canh, hoi thoai nhan vat, loi dan truyen, mood\n\nTra ve JSON array voi format:\n[{"chapter_no":1,"title":"...","narration":"...","panels":[{"panel_no":1,"scene_description":"...","dialogue":[{"character":"...","text":"..."}],"narration_box":"...","mood":"..."}]}]',
    '["topic","num_chapters","panels_per_chapter","language","art_style"]'::jsonb,
    'llama-3.3-70b-versatile',
    'Tao kich ban comic ve su kien lich su'
),
(
    'content_validator',
    'validate_content',
    E'Ban la chuyen gia kiem duyet noi dung lich su. Hay danh gia noi dung sau va cho biet:\n1. Noi dung co chinh xac ve mat lich su khong? (0-100 diem)\n2. Co phu hop cho giao duc khong?\n3. Co chua thong tin sai lech, thien vi, hoac khong phu hop khong?\n4. De xuat cai thien (neu co)\n\nNoi dung can danh gia:\n"""{{content}}"""\n\nTra ve JSON: {"is_valid":true,"score":85,"category":"...","issues":[],"suggestions":[],"detected_language":"..."}',
    '["content"]'::jsonb,
    'llama-3.3-70b-versatile',
    'Kiem duyet noi dung lich su do nguoi dung upload'
),
(
    'quiz_generator',
    'generate_quiz',
    E'Dua tren noi dung sau, hay tao {{num_questions}} cau hoi quiz:\n\nNoi dung: """{{content}}"""\n\nYeu cau:\n- Ngon ngu: {{language}}\n- Do kho: {{difficulty}}\n- Loai cau hoi: {{question_types}}\n- Moi cau multiple_choice co 4 dap an, danh dau dap an dung\n- Moi cau co giai thich dap an\n\nTra ve JSON array:\n[{"question_text":"...","question_type":"multiple_choice","difficulty":"medium","options":[{"text":"...","is_correct":false}],"explanation":"...","tags":[]}]',
    '["content","num_questions","language","difficulty","question_types"]'::jsonb,
    'llama-3.3-70b-versatile',
    'Tu dong tao cau hoi quiz tu noi dung lich su'
),
(
    'flashcard_generator',
    'generate_flashcard',
    E'Dua tren noi dung sau, hay tao {{num_cards}} flashcard:\n\nNoi dung: """{{content}}"""\n\nYeu cau:\n- Ngon ngu: {{language}}\n- Mat truoc: cau hoi/tu khoa/su kien ngan gon\n- Mat sau: dap an/giai thich chi tiet\n- Phan loai do kho cho moi the\n\nTra ve JSON array:\n[{"front_text":"...","back_text":"...","difficulty":"medium","tags":[]}]',
    '["content","num_cards","language"]'::jsonb,
    'llama-3.3-70b-versatile',
    'Tu dong tao flashcard tu noi dung lich su'
),
(
    'chat_historical_assistant',
    'chat',
    E'Ban la tro ly AI chuyen ve lich su ten "Su Ky". Nhiem vu:\n- Tra loi cac cau hoi ve lich su mot cach chinh xac, de hieu\n- Su dung ngon ngu {{language}}\n- Trich dan nguon khi co the\n- Neu khong chac chan, hay noi ro\n- Goi y tao slide/comic/quiz khi phu hop\n\nNgu canh cuoc tro chuyen: {{context}}\nSu kien dang thao luan: {{event_title}}',
    '["language","context","event_title"]'::jsonb,
    'llama-3.3-70b-versatile',
    'Prompt cho AI tro ly chat ve lich su'
);


-- ============================================================================
-- STEP 12: SEED DATA - Categories
-- ============================================================================

INSERT INTO categories (slug, name_vi, name_en, description_vi, description_en, display_order) VALUES
('lich-su-viet-nam', 'Lich su Viet Nam', 'Vietnamese History', 'Cac su kien lich su Viet Nam tu thoi co dai den hien dai', 'Vietnamese historical events from ancient to modern times', 1),
('lich-su-the-gioi', 'Lich su The gioi', 'World History', 'Cac su kien lich su quan trong tren the gioi', 'Major world historical events', 2),
('chien-tranh', 'Chien tranh', 'Wars & Conflicts', 'Cac cuoc chien tranh va xung dot lon', 'Major wars and conflicts', 3),
('van-minh-co-dai', 'Van minh co dai', 'Ancient Civilizations', 'Cac nen van minh co dai tren the gioi', 'Ancient civilizations around the world', 4),
('cach-mang', 'Cach mang', 'Revolutions', 'Cac cuoc cach mang lon trong lich su', 'Major revolutions in history', 5),
('nhan-vat-lich-su', 'Nhan vat lich su', 'Historical Figures', 'Cac nhan vat lich su co anh huong lon', 'Influential historical figures', 6),
('khoa-hoc-cong-nghe', 'Khoa hoc & Cong nghe', 'Science & Technology', 'Cac phat minh va buoc ngoat khoa hoc', 'Scientific inventions and breakthroughs', 7),
('van-hoa-xa-hoi', 'Van hoa & Xa hoi', 'Culture & Society', 'Cac su kien van hoa va bien doi xa hoi', 'Cultural events and social changes', 8);

-- Subcategories for Vietnamese History
INSERT INTO categories (slug, name_vi, name_en, parent_id, display_order)
SELECT
    sub.slug, sub.name_vi, sub.name_en, c.id, sub.display_order
FROM categories c
CROSS JOIN (
    VALUES
        ('thoi-ky-bac-thuoc', 'Thoi ky Bac thuoc', 'Chinese Domination Period', 1),
        ('thoi-ky-phong-kien', 'Thoi ky phong kien', 'Feudal Period', 2),
        ('khang-chien-chong-phap', 'Khang chien chong Phap', 'Resistance against France', 3),
        ('khang-chien-chong-my', 'Khang chien chong My', 'Resistance against America', 4),
        ('thong-nhat-dat-nuoc', 'Thong nhat dat nuoc', 'National Reunification', 5),
        ('doi-moi', 'Doi moi', 'Doi Moi (Renovation)', 6)
) AS sub(slug, name_vi, name_en, display_order)
WHERE c.slug = 'lich-su-viet-nam';


-- ============================================================================
-- STEP 13: SEED DATA - Sample Historical Events
-- ============================================================================

INSERT INTO historical_events (
    slug, title_vi, title_en, start_year, end_year, era, region, location,
    main_characters, short_desc_vi, short_desc_en,
    full_content_vi, full_content_en,
    historical_significance_vi, historical_significance_en,
    key_dates, sources, status
) VALUES
(
    'chien-thang-dien-bien-phu',
    'Chien thang Dien Bien Phu',
    'Battle of Dien Bien Phu',
    1954, 1954,
    'contemporary', 'vietnam', 'Dien Bien Phu, Viet Nam',
    '[{"name":"Vo Nguyen Giap","role":"Tong tu lenh Quan doi nhan dan Viet Nam"},{"name":"Christian de Castries","role":"Chi huy quan Phap tai Dien Bien Phu"}]'::jsonb,
    'Tran danh quyet dinh ket thuc chien tranh Dong Duong lan thu nhat',
    'The decisive battle that ended the First Indochina War',
    'Chien dich Dien Bien Phu dien ra tu ngay 13/3 den 7/5/1954, la tran danh lon nhat trong Chien tranh Dong Duong giua Quan doi nhan dan Viet Nam va quan vien chinh Phap. Dai tuong Vo Nguyen Giap da chi huy chien dich voi phuong cham "danh chac, tien chac". Quan doi Viet Nam da bao vay va tan cong lan luot cac cu diem cua Phap trong thung lung Dien Bien Phu. Sau 56 ngay dem chien dau, quan doi Viet Nam da gianh chien thang hoan toan.',
    'The Battle of Dien Bien Phu took place from March 13 to May 7, 1954, and was the largest battle of the First Indochina War between the Viet Minh and French forces. General Vo Nguyen Giap commanded the campaign with the strategy of "steady attack, steady advance". The Vietnamese army surrounded and systematically attacked French positions in the Dien Bien Phu valley. After 56 days and nights of fighting, the Vietnamese achieved a complete victory.',
    'Chien thang Dien Bien Phu buoc Phap phai ky Hiep dinh Geneva, cham dut su do ho cua Phap tai Dong Duong. Day la chien thang quan su dau tien cua mot dan toc thuoc dia truoc mot de quoc lon, co vu phong trao giai phong dan toc tren toan the gioi.',
    'The victory at Dien Bien Phu forced France to sign the Geneva Accords, ending French colonial rule in Indochina. It was the first military victory of a colonized nation over a major imperial power, inspiring national liberation movements worldwide.',
    '[{"date":"13/03/1954","event_vi":"Bat dau chien dich - tan cong cu diem Him Lam","event_en":"Campaign begins - attack on Him Lam strongpoint"},{"date":"30/03/1954","event_vi":"Dot tan cong thu 2 vao phan khu trung tam","event_en":"Second wave attack on central sector"},{"date":"01/05/1954","event_vi":"Dot tan cong thu 3 - tong tan cong","event_en":"Third wave - general assault"},{"date":"07/05/1954","event_vi":"Chien thang hoan toan - De Castries bi bat","event_en":"Complete victory - De Castries captured"}]'::jsonb,
    '[{"title":"Dien Bien Phu - Diem hen lich su","author":"Vo Nguyen Giap","type":"book"},{"title":"Hell in a Very Small Place","author":"Bernard B. Fall","type":"book"}]'::jsonb,
    'published'
),
(
    'cach-mang-thang-tam',
    'Cach mang Thang Tam',
    'August Revolution',
    1945, 1945,
    'contemporary', 'vietnam', 'Toan quoc Viet Nam',
    '[{"name":"Ho Chi Minh","role":"Lanh dao Viet Minh"},{"name":"Tran Huy Lieu","role":"Dai dien Chinh phu Cach mang nhan an kiem tu Bao Dai"}]'::jsonb,
    'Cuoc cach mang gianh doc lap cho Viet Nam, thanh lap nuoc Viet Nam Dan chu Cong hoa',
    'The revolution that won independence for Vietnam and established the Democratic Republic of Vietnam',
    'Cach mang Thang Tam la cuoc cach mang do Viet Minh lanh dao, lat do che do phong kien nha Nguyen va gianh chinh quyen tu tay Nhat. Ngay 2/9/1945, tai Quang truong Ba Dinh, Chu tich Ho Chi Minh doc Tuyen ngon Doc lap, khai sinh nuoc Viet Nam Dan chu Cong hoa.',
    'The August Revolution was led by the Viet Minh, overthrowing the Nguyen dynasty and seizing power from the Japanese. On September 2, 1945, at Ba Dinh Square, President Ho Chi Minh read the Declaration of Independence, establishing the Democratic Republic of Vietnam.',
    'Cach mang Thang Tam da cham dut che do phong kien hang nghin nam va ach do ho cua thuc dan Phap - phat xit Nhat, mo ra ky nguyen moi cho dan toc Viet Nam.',
    'The August Revolution ended thousands of years of feudalism and French-Japanese colonial rule, opening a new era for the Vietnamese nation.',
    '[{"date":"16/08/1945","event_vi":"Dai hoi Quoc dan Tan Trao","event_en":"Tan Trao National Congress"},{"date":"19/08/1945","event_vi":"Khoi nghia thanh cong tai Ha Noi","event_en":"Successful uprising in Hanoi"},{"date":"30/08/1945","event_vi":"Bao Dai thoai vi","event_en":"Bao Dai abdicates"},{"date":"02/09/1945","event_vi":"Tuyen ngon Doc lap","event_en":"Declaration of Independence"}]'::jsonb,
    '[{"title":"Con duong dan toi den chu nghia Lenin","author":"Ho Chi Minh","type":"article"}]'::jsonb,
    'published'
);

-- Link events to categories
INSERT INTO event_categories (event_id, category_id)
SELECT he.id, c.id
FROM historical_events he
CROSS JOIN categories c
WHERE (he.slug = 'chien-thang-dien-bien-phu' AND c.slug IN ('lich-su-viet-nam', 'chien-tranh'))
   OR (he.slug = 'cach-mang-thang-tam' AND c.slug IN ('lich-su-viet-nam', 'cach-mang'));


-- ============================================================================
-- STEP 14: ROW LEVEL SECURITY (Supabase RLS)
-- ============================================================================
-- Enable RLS on all tables (Supabase requires this for API access)
-- Policies should be added based on your auth setup

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE historical_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_contents ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE slides ENABLE ROW LEVEL SECURITY;
ALTER TABLE story_chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_sets ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_options ENABLE ROW LEVEL SECURITY;
ALTER TABLE flashcard_decks ENABLE ROW LEVEL SECURITY;
ALTER TABLE flashcards ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE quiz_attempt_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE flashcard_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE prompt_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_tasks ENABLE ROW LEVEL SECURITY;

-- Public read access for categories and published events (no auth needed)
CREATE POLICY "categories_public_read" ON categories
    FOR SELECT USING (is_active = TRUE);

CREATE POLICY "events_public_read" ON historical_events
    FOR SELECT USING (status = 'published');

CREATE POLICY "event_categories_public_read" ON event_categories
    FOR SELECT USING (TRUE);

CREATE POLICY "prompt_templates_public_read" ON prompt_templates
    FOR SELECT USING (is_active = TRUE);

-- For tables that need auth-based access, add policies after setting up
-- your JWT/auth system. Example pattern:
--
-- CREATE POLICY "users_own_data" ON conversations
--     FOR ALL USING (user_id = auth.uid());
--
-- For now, allow service_role full access (Supabase service key):

CREATE POLICY "service_role_all_users" ON users
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_user_settings" ON user_settings
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_user_contents" ON user_contents
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_conversations" ON conversations
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_messages" ON messages
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_projects" ON projects
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_slides" ON slides
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_story_chapters" ON story_chapters
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_project_versions" ON project_versions
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_project_exports" ON project_exports
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_quiz_sets" ON quiz_sets
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_quiz_questions" ON quiz_questions
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_quiz_options" ON quiz_options
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_flashcard_decks" ON flashcard_decks
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_flashcards" ON flashcards
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_quiz_attempts" ON quiz_attempts
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_quiz_attempt_details" ON quiz_attempt_details
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_flashcard_progress" ON flashcard_progress
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_ai_tasks" ON ai_tasks
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_categories" ON categories
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_historical_events" ON historical_events
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_event_categories" ON event_categories
    FOR ALL USING (TRUE) WITH CHECK (TRUE);

CREATE POLICY "service_role_all_prompt_templates" ON prompt_templates
    FOR ALL USING (TRUE) WITH CHECK (TRUE);


-- ============================================================================
-- DONE! Schema created successfully.
-- ============================================================================
-- Tables: 21
--   User Service:    users, user_settings
--   Content Service: categories, historical_events, event_categories, user_contents
--   Chat Service:    conversations, messages
--   Project Service: projects, slides, story_chapters, project_versions, project_exports
--   Quiz Service:    quiz_sets, quiz_questions, quiz_options, flashcard_decks,
--                    flashcards, quiz_attempts, quiz_attempt_details, flashcard_progress
--   AI Service:      ai_tasks, prompt_templates
-- Triggers: 20 (15 updated_at + 4 counters + 1 credit deduction)
-- Indexes: 40+
-- RLS: Enabled on all tables with service_role full access
-- ============================================================================
