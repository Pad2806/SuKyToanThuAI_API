// ─── STATIC DATA ───

export const EVENTS = [
  {
    id: 1,
    img: "/images/hai_ba_trung.png",
    bg: "linear-gradient(135deg,#1C0808,#2D1008)",
    era: "40 SCN",
    title: "Khởi nghĩa Hai Bà Trưng",
    desc: "Cuộc khởi nghĩa đầu tiên của phụ nữ Việt Nam chống lại ách đô hộ nhà Hán, do Trưng Trắc và Trưng Nhị lãnh đạo năm 40 SCN.",
  },
  {
    id: 2,
    img: "/images/dien_bien_phu.png",
    bg: "linear-gradient(135deg,#08181C,#0A2820)",
    era: "1954",
    title: "Chiến thắng Điện Biên Phủ",
    desc: "Trận quyết chiến chiến lược kết thúc chiến tranh Đông Dương, quân dân Việt Nam đánh bại tập đoàn cứ điểm của Pháp.",
  },
  {
    id: 3,
    img: "/images/quang_trung.png",
    bg: "linear-gradient(135deg,#181808,#28200A)",
    era: "1788",
    title: "Đại phá quân Thanh",
    desc: "Vua Quang Trung lãnh đạo 10 vạn quân thần tốc tiến ra Bắc, đại phá 29 vạn quân Mãn Thanh trong 5 ngày Tết Kỷ Dậu.",
  },
  {
    id: 4,
    img: "/images/world_war_2.png",
    bg: "linear-gradient(135deg,#0A0818,#100A28)",
    era: "1939–1945",
    title: "Chiến tranh Thế giới II",
    desc: "Cuộc chiến toàn cầu lớn nhất lịch sử nhân loại, kéo dài 6 năm với hơn 70 triệu người thiệt mạng trên khắp các châu lục.",
  },
  {
    id: 5,
    img: "/images/tran_mongol.png",
    bg: "linear-gradient(135deg,#18080A,#2A0E10)",
    era: "TK XIII",
    title: "Ba lần thắng Mông Cổ",
    desc: "Nhà Trần ba lần đánh bại đế chế Mông Cổ hùng mạnh nhất thế giới, viết nên trang sử vẻ vang với tinh thần Hào khí Đông A.",
  },
  {
    id: 6,
    img: "/images/mesopotamia.png",
    bg: "linear-gradient(135deg,#1A1008,#2A1E08)",
    era: "TCN",
    title: "Văn minh Lưỡng Hà",
    desc: "Nền văn minh sông Tigris và Euphrates — cái nôi của chữ viết, luật pháp, toán học và thiên văn học đầu tiên của nhân loại.",
  },
];

export const RECENT_WORKS = [
  { img: "/images/hai_ba_trung.png", bg: "linear-gradient(135deg,#1a0a0a,#2D1810)", badge: "Slide", badgeKey: "slide", title: "Khởi nghĩa Hai Bà Trưng", meta: "12 trang", time: "2 giờ trước", goAi: false },
  { img: "/images/dien_bien_phu.png", bg: "linear-gradient(135deg,#0a1a10,#102816)", badge: "Truyện tranh", badgeKey: "comic", title: "Chiến thắng Điện Biên Phủ", meta: "18 khung", time: "Hôm qua", goAi: false },
  { img: "/images/world_war_2.png", bg: "linear-gradient(135deg,#0a0a1a,#101028)", badge: "Đang làm", badgeKey: "wip", title: "Thế chiến II – Mặt trận châu Á", meta: "8/24 trang", time: "3 ngày trước", goAi: false },
  { img: "/images/tran_mongol.png", bg: "linear-gradient(135deg,#1a1000,#2A1E00)", badge: "Slide", badgeKey: "slide", title: "Đế chế Mông Cổ – Thành Cát Tư Hãn", meta: "20 trang", time: "1 tuần trước", goAi: true },
];

export const ADMIN_USERS = [
  { ava: "NT", avaColor: "linear-gradient(135deg,#C9A84C,#7A5500)", name: "Nguyễn Thanh", email: "thanh@gmail.com", joined: "1 Jan 2025", usage: "12 Slide · 3 Comic", status: "active" },
  { ava: "LM", avaColor: "linear-gradient(135deg,#4A7C59,#203A2A)", name: "Lê Minh", email: "minh.le@edu.vn", joined: "15 Feb 2025", usage: "5 Slide · 8 Comic", status: "active" },
  { ava: "PH", avaColor: "linear-gradient(135deg,#B5352A,#5A1A14)", name: "Phạm Hương", email: "huong.pham@school.vn", joined: "3 Mar 2025", usage: "2 Slide · 0 Comic", status: "banned" },
];

export const CMS_ITEMS = [
  { emoji: "🏯", bg: "linear-gradient(135deg,#1C0808,#2D1008)", title: "Khởi nghĩa Hai Bà Trưng", meta: "Lịch sử VN · 40 SCN", published: true },
  { emoji: "⚔️", bg: "linear-gradient(135deg,#08181C,#0A2820)", title: "Chiến thắng Điện Biên Phủ", meta: "Lịch sử VN · 1954", published: true },
  { emoji: "🐉", bg: "linear-gradient(135deg,#181808,#28200A)", title: "Đại phá quân Thanh", meta: "Lịch sử VN · 1788", published: false },
  { emoji: "🌍", bg: "linear-gradient(135deg,#0A0818,#100A28)", title: "Chiến tranh Thế giới II", meta: "TG · 1939–1945", published: true },
  { emoji: "🦁", bg: "linear-gradient(135deg,#18080A,#2A0E10)", title: "Ba lần thắng Mông Cổ", meta: "Lịch sử VN · TK XIII", published: true },
];

export const CHART_DATA_WEEKLY = [
  { l: "T2", v: 42 }, { l: "T3", v: 68 }, { l: "T4", v: 35 }, { l: "T5", v: 82 },
  { l: "T6", v: 91 }, { l: "T7", v: 56 }, { l: "CN", v: 29 },
];

export const CHART_DATA_MONTHLY = [
  { l: "W1", v: 55 }, { l: "W2", v: 72 }, { l: "W3", v: 48 }, { l: "W4", v: 88 },
];

export const AI_REPLIES = [
  { text: "Tuyệt! Mình sẽ tạo theo phong cách đó. Bạn muốn tone màu chủ đạo là gì?", opts: ["🔴 Đỏ – Nhiệt huyết, chiến đấu", "🟡 Vàng – Uy nghiêm, lịch sử", "⚫ Tối – Trầm hùng, sử thi"] },
  { text: "Tone màu đẹp đấy! Bạn muốn bao nhiêu trang slide?", opts: ["8 trang – Ngắn gọn", "12 trang – Tiêu chuẩn", "20 trang – Chi tiết đầy đủ"] },
  { text: "Hoàn hảo! Đang tạo 12 trang slide với tone đỏ – vàng uy nghiêm... Bạn có muốn thêm phần câu hỏi ôn tập ở cuối không?", opts: ["✅ Có, thêm vào", "❌ Không cần"] },
  { text: "Xong rồi! Bạn có thể click thẳng vào từng slide bên phải để sửa chữ. Hoặc nói với mình cần chỉnh gì!", opts: null },
];

export const LOADING_MSGS = [
  "Đang phác thảo nhân vật lịch sử...",
  "Đang tô màu áo giáp và y phục...",
  "Đang xây dựng bối cảnh sự kiện...",
  "Đang ghép chữ vào các khung...",
  "Đang kiểm tra độ chính xác lịch sử...",
  "Sắp hoàn thành rồi, đợi tí nhé!",
];
