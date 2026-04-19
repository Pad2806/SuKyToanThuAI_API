# SuKyToanThuAI - Microservice API Backend

Dự án Hệ thống AI Hỗ trợ Trực quan hóa Nội dung Lịch sử.

## 🚀 Kiến trúc dự án
Kiến trúc **Modular Monolithic chạy bằng Docker Compose**:
- **Auth Service** (:8001)
- **Content Service** (:8002) - Cốt lõi Sinh Text Outline AI
- **Media Service** (:8003) - Visual AI (Wiki, Assets)
- **Education Service** (:8004) - Luyện thi Flashcard
- **Workspace Service** (:8005) - Lưu trữ Project & Xuất PPTX
- **API Gateway (Nginx)** (:8000)

## 🐳 Hướng dẫn chạy cho Dev

1. Mở Terminal tại rễ dự án.
2. Di chuyển vào thư mục backend: 
   `cd backend`
3. Chép file config môi trường (Và phải tự điền API Key): 
   `cp .env.example .env`
4. Khởi động Cụm Server bằng Docker:
   `docker-compose up --build`

👉 **Truy cập:** Các API có thể dùng trực tiếp qua gateway tại `http://localhost:8000/api/v1/`

## 🐘 Database Migration (Supabase CLI)
Quy trình thêm/sửa cột (Nguyên tắc: Không sửa DB trên Cloud Server!):
1. Chạy `npx supabase start` để bật Local Supabase.
2. Mở Studio `localhost:54323` đổi Table.
3. Chạy `npx supabase db diff -f ten_thay_doi` để tạo file sql migration.
4. Chạy `npx supabase db push` để đẩy lên Cloud của đội nhóm.
