# SuKyToanThuAI - Microservice API Backend

Dự án Hệ thống AI Hỗ trợ Trực quan hóa Nội dung Lịch sử.

## 🚀 Kiến trúc dự án
Kiến trúc **Modular Monolithic chạy bằng Docker Compose**:
- **Auth Service** (:8001) - Auth + Admin Quản lý Users
- **Content Service** (:8002) - Lõi AI + Admin Quản lý sự kiện & Danh mục
- **Media Service** (:8003) - Visual AI (Wiki, Assets)
- **Education Service** (:8004) - Luyện thi Flashcard
- **Workspace Service** (:8005) - Lưu trữ Project & Xuất PPTX
- **API Gateway (Nginx)** (:8000)

## 🐳 Hướng dẫn Backend Chạy Server

1. Mở Terminal tại rễ dự án: `cd backend`
2. Mở file `.env.example` copy thành `.env` (Và phải tự điền API Key)
3. Khởi động Cụm Server bằng Docker:
   ```bash
   docker-compose up --build
   ```

---

## 🔌 HƯỚNG DẪN DÀNH CHO FRONTEND CONNECT LẤY DATA

Toàn bộ **5 Microservice** đã được Nginx gom chung lại chạy ở cổng duy nhất là `8000`. Do đó Front-end (ReactJS) không quan tâm Backend đằng sau chia nhỏ ra sao, FE chỉ gọi duy nhất 1 host gốc.

### 1. Setup Base URL (Trong React / Vite)
Tạo file `.env` ở Frontend và khai báo:
```env
VITE_API_BASE_URL="http://localhost:8000/api/v1"
```

### 2. File cấu hình Axios Setup (Ví dụ `axiosInstance.js`)
Frontend Developer cấu hình Axios nối vào đường dẫn trên và lấy Token từ LocalStorage:
```javascript
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Tự động chèn token vào mỗi khi Frontend đi gọi Backend
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

### 3. Cách Frontend gọi API ứng với từng Service của BE

Frontend muốn lấy dữ liệu Auth (Người 1 code):
```javascript
// Chọc vào Auth Service (Port 8001 ngầm)
const { data } = await api.post("/auth/login", { email, password });
const { data } = await api.get("/auth/me");
```

Frontend làm trang ADMIN (Quản lý User & Event):
```javascript
// Role: Admin gọi xóa User
const deleteUser = await api.delete("/auth/admin/users/123");

// Role: Admin tạo danh mục mới
const newCategory = await api.post("/content/admin/categories", { name: "Chiến tranh" });
```

Frontend gọi API Generate Content (Người 2 làm):
```javascript
// Chọc vào Content Service (Port 8002 ngầm)
const result = await api.post("/content/outline", { prompt: "Khởi nghĩa Hai Bà Trưng" });
```
*(Cấu trúc Rất đơn giản, không cần thay số 8000 trong URL)*

---

## 🐘 Database Migration (Supabase CLI)
Quy trình thêm/sửa cột (Nguyên tắc: Không sửa DB trên Cloud Server!):
1. Chạy `npx supabase start` để bật Local Supabase.
2. Mở Studio `localhost:54323` đổi Table bằng Web UI hoặc tạo mới file Migration.
3. Chạy `npx supabase db diff -f ten_thay_doi` để tạo file sql chuẩn xịn.
4. Chạy `npx supabase db push` để đẩy lên Cloud của đội nhóm không làm gián đoạn mọi người.
