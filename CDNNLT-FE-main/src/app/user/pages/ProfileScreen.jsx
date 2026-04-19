import { useState } from "react";
import "../styles/ProfileScreen.css";

const RECENT_ACTIVITY = [
  { icon: "📊", type: "slide", title: "Khởi nghĩa Hai Bà Trưng",          time: "2 giờ trước" },
  { icon: "📖", type: "comic", title: "Chiến thắng Điện Biên Phủ",         time: "Hôm qua" },
  { icon: "📊", type: "slide", title: "Đế chế Mông Cổ – Thành Cát Tư Hãn", time: "1 tuần trước" },
  { icon: "📖", type: "comic", title: "Đại phá quân Thanh",                  time: "2 tuần trước" },
];

// ─── Password strength helper ───
function getStrength(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8)              score++;
  if (/[A-Z]/.test(pw))           score++;
  if (/[0-9]/.test(pw))           score++;
  if (/[^A-Za-z0-9]/.test(pw))    score++;
  return score; // 0-4
}

const STRENGTH_LABELS = ["", "Yếu", "Trung bình", "Mạnh", "Rất mạnh"];
const STRENGTH_KEYS   = ["", "weak", "weak", "medium", "strong"];

export default function ProfileScreen({ user, setUser }) {
  // ── Form state ──
  const [form, setForm] = useState({
    firstName:   user?.firstName  ?? "Trương Như",
    lastName:    user?.lastName   ?? "Quang Thảo",
    email:       user?.email      ?? "thaotruong23082004@gmail.com",
    phone:       user?.phone      ?? "0901 234 567",
    birthYear:   user?.birthYear  ?? "2004",
    gender:      user?.gender     ?? "male",
    school:      user?.school     ?? "THPT Nguyễn Huệ",
    grade:       user?.grade      ?? "12",
    bio:         user?.bio        ?? "",
  });

  const [saved,   setSaved]   = useState(false);
  const [saving,  setSaving]  = useState(false);
  const [pwForm,  setPwForm]  = useState({ current: "", next: "", confirm: "" });
  const [pwSaved, setPwSaved] = useState(false);

  const strength = getStrength(pwForm.next);

  function handleChange(e) {
    setSaved(false);
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));
  }

  function handleSave(e) {
    e.preventDefault();
    setSaving(true);
    setTimeout(() => {
      setUser?.({ ...form });
      setSaving(false);
      setSaved(true);
    }, 800);
  }

  function handlePwSave(e) {
    e.preventDefault();
    if (pwForm.next !== pwForm.confirm) return alert("Mật khẩu xác nhận không khớp!");
    if (strength < 2) return alert("Mật khẩu quá yếu!");
    setPwSaved(true);
    setPwForm({ current: "", next: "", confirm: "" });
    setTimeout(() => setPwSaved(false), 3000);
  }

  const initials = `${form.firstName?.[0] ?? ""}${form.lastName?.[0] ?? ""}`.toUpperCase();

  return (
    <div className="profile">
      {/* ── Hero banner ── */}
      <div className="profile__hero">
        <div className="profile__avatar-wrap">
          <div className="profile__avatar">
            {initials}
            <div className="profile__avatar-overlay">📷</div>
          </div>
        </div>
        <div className="profile__hero-info">
          <div className="profile__hero-role">Thành viên</div>
          <h1 className="profile__hero-name">
            {form.firstName} {form.lastName}
          </h1>
          <div className="profile__hero-meta">
            <span>{form.email}</span>
            <span>{form.school || "Chưa cập nhật trường"}</span>
            <span>Tham gia tháng 1, 2025</span>
          </div>
        </div>
      </div>

      {/* ── Body ── */}
      <div className="profile__body">
        {/* ── LEFT COLUMN ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>

          {/* Card: Thông tin cá nhân */}
          <div className="profile__card">
            <div className="profile__card-header">
              <div>
                <div className="profile__card-title">Thông tin cá nhân</div>
                <div className="profile__card-subtitle">Cập nhật họ tên, liên lạc và thông tin học tập</div>
              </div>
            </div>

            <form onSubmit={handleSave}>
              <div className="profile__form">

                {/* Row 1: first + last name */}
                <div className="profile__form-row">
                  <div className="profile__field">
                    <label className="profile__label">Họ</label>
                    <input
                      className="profile__input"
                      name="lastName"
                      value={form.lastName}
                      onChange={handleChange}
                      placeholder="Nguyễn"
                    />
                  </div>
                  <div className="profile__field">
                    <label className="profile__label">Tên</label>
                    <input
                      className="profile__input"
                      name="firstName"
                      value={form.firstName}
                      onChange={handleChange}
                      placeholder="Văn A"
                    />
                  </div>
                </div>

                {/* Row 2: email + phone */}
                <div className="profile__form-row">
                  <div className="profile__field">
                    <label className="profile__label">Email</label>
                    <div className="profile__input-wrap">
                      <span className="profile__input-icon">✉️</span>
                      <input
                        className="profile__input"
                        type="email"
                        name="email"
                        value={form.email}
                        onChange={handleChange}
                        placeholder="email@example.com"
                      />
                    </div>
                  </div>
                  <div className="profile__field">
                    <label className="profile__label">Số điện thoại</label>
                    <div className="profile__input-wrap">
                      <span className="profile__input-icon">📱</span>
                      <input
                        className="profile__input"
                        type="tel"
                        name="phone"
                        value={form.phone}
                        onChange={handleChange}
                        placeholder="09xx xxx xxx"
                      />
                    </div>
                  </div>
                </div>

                {/* Row 3: birth year + gender */}
                <div className="profile__form-row">
                  <div className="profile__field">
                    <label className="profile__label">Năm sinh</label>
                    <input
                      className="profile__input"
                      type="number"
                      name="birthYear"
                      value={form.birthYear}
                      onChange={handleChange}
                      placeholder="2005"
                      min="1950"
                      max="2015"
                    />
                  </div>
                  <div className="profile__field">
                    <label className="profile__label">Giới tính</label>
                    <select
                      className="profile__select"
                      name="gender"
                      value={form.gender}
                      onChange={handleChange}
                    >
                      <option value="male">Nam</option>
                      <option value="female">Nữ</option>
                      <option value="other">Khác</option>
                    </select>
                  </div>
                </div>

                {/* Row 4: school + grade */}
                <div className="profile__form-row">
                  <div className="profile__field">
                    <label className="profile__label">Trường học</label>
                    <div className="profile__input-wrap">
                      <span className="profile__input-icon">🏫</span>
                      <input
                        className="profile__input"
                        name="school"
                        value={form.school}
                        onChange={handleChange}
                        placeholder="Tên trường..."
                      />
                    </div>
                  </div>
                  <div className="profile__field">
                    <label className="profile__label">Lớp / Khối</label>
                    <select
                      className="profile__select"
                      name="grade"
                      value={form.grade}
                      onChange={handleChange}
                    >
                      {["6","7","8","9","10","11","12","Đại học","Khác"].map((g) => (
                        <option key={g} value={g}>{g}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Bio */}
                <div className="profile__field profile__field--full">
                  <label className="profile__label">Giới thiệu bản thân</label>
                  <textarea
                    className="profile__textarea"
                    name="bio"
                    value={form.bio}
                    onChange={handleChange}
                    placeholder="Chia sẻ đôi điều về bạn và sở thích học lịch sử..."
                  />
                </div>
              </div>

              <div className="profile__form-footer">
                <span className={`profile__save-hint ${saved ? "profile__save-hint--success" : ""}`}>
                  {saved ? "✓ Đã lưu thành công!" : "Thay đổi chưa được lưu"}
                </span>
                <button
                  type="submit"
                  className="profile__btn-save"
                  disabled={saving}
                >
                  {saving ? "⏳ Đang lưu..." : "💾 Lưu thay đổi"}
                </button>
              </div>
            </form>
          </div>

          {/* Card: Đổi mật khẩu */}
          <div className="profile__card">
            <div className="profile__card-header">
              <div>
                <div className="profile__card-title">Bảo mật & Mật khẩu</div>
                <div className="profile__card-subtitle">Cập nhật mật khẩu để bảo vệ tài khoản</div>
              </div>
            </div>

            <form onSubmit={handlePwSave}>
              <div className="profile__password-form">
                <div className="profile__field">
                  <label className="profile__label">Mật khẩu hiện tại</label>
                  <input
                    className="profile__input"
                    type="password"
                    value={pwForm.current}
                    onChange={(e) => setPwForm((f) => ({ ...f, current: e.target.value }))}
                    placeholder="••••••••"
                  />
                </div>
                <div className="profile__field">
                  <label className="profile__label">Mật khẩu mới</label>
                  <input
                    className="profile__input"
                    type="password"
                    value={pwForm.next}
                    onChange={(e) => { setPwSaved(false); setPwForm((f) => ({ ...f, next: e.target.value })); }}
                    placeholder="••••••••"
                  />
                  {pwForm.next && (
                    <>
                      <div className="profile__password-strength">
                        {[1,2,3,4].map((i) => (
                          <div
                            key={i}
                            className={`profile__strength-bar ${i <= strength ? `profile__strength-bar--${STRENGTH_KEYS[strength]}` : ""}`}
                          />
                        ))}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-dim)", marginTop: 2 }}>
                        Độ mạnh: <span style={{ color: strength >= 3 ? "var(--green-light)" : strength >= 2 ? "var(--gold)" : "#D4846B" }}>
                          {STRENGTH_LABELS[strength]}
                        </span>
                      </div>
                    </>
                  )}
                </div>
                <div className="profile__field">
                  <label className="profile__label">Xác nhận mật khẩu mới</label>
                  <input
                    className="profile__input"
                    type="password"
                    value={pwForm.confirm}
                    onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))}
                    placeholder="••••••••"
                  />
                  {pwForm.confirm && pwForm.next !== pwForm.confirm && (
                    <div style={{ fontSize: "0.72rem", color: "#D4846B", marginTop: 2 }}>Mật khẩu không khớp</div>
                  )}
                </div>
              </div>

              <div className="profile__form-footer">
                <span className={`profile__save-hint ${pwSaved ? "profile__save-hint--success" : ""}`}>
                  {pwSaved ? "✓ Mật khẩu đã được cập nhật!" : ""}
                </span>
                <button type="submit" className="profile__btn-save">
                  🔒 Đổi mật khẩu
                </button>
              </div>
            </form>
          </div>

          {/* Card: Vùng nguy hiểm */}
          <div className="profile__card">
            <div className="profile__card-header">
              <div>
                <div className="profile__card-title" style={{ color: "#D4846B" }}>Vùng nguy hiểm</div>
                <div className="profile__card-subtitle">Các thao tác không thể hoàn tác</div>
              </div>
            </div>
            <div className="profile__danger-zone">
              <button className="profile__btn-danger">
                🗑 Xoá tất cả dự án của tôi
              </button>
              <button className="profile__btn-danger">
                ❌ Xoá tài khoản vĩnh viễn
              </button>
            </div>
          </div>
        </div>

        {/* ── RIGHT SIDEBAR ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>

          {/* Stats */}
          <div className="profile__card">
            <div className="profile__card-header">
              <div className="profile__card-title">Thống kê</div>
            </div>
            <div className="profile__stats-grid">
              {[
                { num: "12", label: "Slide đã tạo" },
                { num: "3",  label: "Truyện tranh" },
                { num: "8",  label: "Tuần học" },
                { num: "47", label: "Giờ học" },
              ].map((s) => (
                <div key={s.label} className="profile__stat">
                  <div className="profile__stat-num">{s.num}</div>
                  <div className="profile__stat-label">{s.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="profile__card">
            <div className="profile__card-header">
              <div className="profile__card-title">Hoạt động gần đây</div>
            </div>
            <div className="profile__activity">
              {RECENT_ACTIVITY.map((a, i) => (
                <div key={i} className="profile__activity-item">
                  <div className={`profile__activity-icon profile__activity-icon--${a.type}`}>
                    {a.icon}
                  </div>
                  <div style={{ overflow: "hidden" }}>
                    <div className="profile__activity-title">{a.title}</div>
                    <div className="profile__activity-time">{a.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Membership */}
          <div className="profile__card">
            <div className="profile__card-header">
              <div className="profile__card-title">Gói hiện tại</div>
            </div>
            <div style={{ padding: "20px 24px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 16 }}>
                <div style={{ width: 40, height: 40, borderRadius: 8, background: "rgba(201,168,76,0.12)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.2rem" }}>⭐</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.92rem" }}>Miễn phí</div>
                  <div style={{ fontSize: "0.72rem", color: "var(--text-dim)" }}>5 Slide / tháng · 2 Truyện tranh</div>
                </div>
              </div>
              <button style={{
                width: "100%", padding: "11px 0", borderRadius: 7,
                background: "linear-gradient(135deg, var(--gold), #A07830)",
                color: "var(--dark)", border: "none",
                fontWeight: 700, fontSize: "0.85rem", cursor: "pointer",
                letterSpacing: "0.02em", transition: "all 0.2s",
              }}
                onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-1px)"; e.currentTarget.style.boxShadow = "0 6px 20px rgba(201,168,76,0.3)"; }}
                onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = ""; }}
              >
                🚀 Nâng cấp lên Pro
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}