import { useState } from "react";
import Chart from "../components/Chart";
import { ADMIN_USERS, CMS_ITEMS, CHART_DATA_WEEKLY, CHART_DATA_MONTHLY } from "../data/constants";
import "../styles/AdminScreen.css";

// ─── Shared: KPICard ───
function KPICard({ label, value, valueModifier, change, changeModifier }) {
  return (
    <div className="kpi-card">
      <div className="kpi-card__label">{label}</div>
      <div className={`kpi-card__value ${valueModifier ? `kpi-card__value--${valueModifier}` : ""}`}>
        {value}
      </div>
      <div className={`kpi-card__change ${changeModifier ? `kpi-card__change--${changeModifier}` : ""}`}>
        {change}
      </div>
    </div>
  );
}

// ─── Tab: Dashboard ───
function AdminDashboard() {
  return (
    <>
      <h2 className="admin__title">Dashboard</h2>
      <p className="admin__subtitle">Tổng quan hoạt động nền tảng SửKý AI</p>

      <div className="kpi-grid">
        <KPICard label="Tổng người dùng" value="1,284" valueModifier="gold"  change="+12% tuần này" changeModifier="up" />
        <KPICard label="Slide đã tạo"    value="2,419"                        change="+48 hôm nay"   changeModifier="up" />
        <KPICard label="Truyện tranh"    value="890"                           change="+7 hôm nay"    changeModifier="up" />
        <KPICard label="API calls / ngày" value="4.2K"                        change="↑ 18% MoM"     changeModifier="down" />
      </div>

      <div className="chart-card">
        <div className="chart-card__title">Hoạt động 7 ngày qua</div>
        <Chart data={CHART_DATA_WEEKLY} />
      </div>
    </>
  );
}

// ─── Tab: Users ───
function AdminUsers() {
  return (
    <>
      <h2 className="admin__title">Người dùng</h2>
      <p className="admin__subtitle">Quản lý tài khoản và quyền truy cập</p>

      <div className="admin-table-wrap">
        <div className="admin-table-wrap__header">
          <span className="admin-table-wrap__title">Danh sách người dùng</span>
          <button className="admin-table-wrap__action-btn">+ Thêm người dùng</button>
        </div>

        <table className="admin-table">
          <thead>
            <tr>
              {["Người dùng", "Ngày tham gia", "Sử dụng", "Trạng thái", "Thao tác"].map((h) => (
                <th key={h}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ADMIN_USERS.map((u, i) => (
              <tr key={i}>
                <td>
                  <div className="user-cell">
                    <div className="user-cell__avatar" style={{ background: u.avaColor }}>
                      {u.ava}
                    </div>
                    <div>
                      <div className="user-cell__name">{u.name}</div>
                      <div className="user-cell__email">{u.email}</div>
                    </div>
                  </div>
                </td>
                <td style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>{u.joined}</td>
                <td>{u.usage}</td>
                <td>
                  <span className={`status-badge status-badge--${u.status}`}>
                    {u.status === "active" ? "✓ Active" : "✗ Banned"}
                  </span>
                </td>
                <td>
                  <button
                    className="action-link"
                    style={{ color: u.status === "active" ? "var(--gold)" : "var(--green-light)" }}
                  >
                    {u.status === "active" ? "Xem chi tiết" : "Mở khóa"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ─── Tab: CMS ───
function AdminCMS() {
  return (
    <>
      <h2 className="admin__title">Quản lý Sự kiện Lịch sử</h2>
      <p className="admin__subtitle">Nội dung phục vụ Thư viện Lịch sử cho người dùng</p>

      <div className="cms-grid">
        {CMS_ITEMS.map((item, i) => (
          <div key={i} className="cms-card">
            <div className="cms-card__thumb" style={{ background: item.bg }}>
              {item.emoji}
            </div>
            <div className="cms-card__body">
              <div className="cms-card__title">{item.title}</div>
              <div className="cms-card__meta">
                <span>{item.meta}</span>
                <span className={`cms-published cms-published--${item.published ? "yes" : "no"}`}>
                  {item.published ? "Đã đăng" : "Nháp"}
                </span>
              </div>
            </div>
          </div>
        ))}

        <div className="add-card">
          <div className="add-card__icon">＋</div>
          <span>Thêm sự kiện mới</span>
        </div>
      </div>
    </>
  );
}

// ─── Tab: Analytics ───
function AdminAnalytics() {
  return (
    <>
      <h2 className="admin__title">Phân tích</h2>
      <p className="admin__subtitle">Số liệu chi tiết về lưu lượng và API consumption</p>

      <div className="kpi-grid">
        <KPICard label="Groq API / tháng"  value="124K"  valueModifier="gold"  change="requests" />
        <KPICard label="Image API / tháng" value="38K"                          change="↑ 55% MoM"  changeModifier="down" />
        <KPICard label="Chi phí ước tính"  value="$184"  valueModifier="red"   change="tháng này" />
        <KPICard label="Tỉ lệ thành công"  value="97.2%" valueModifier="green" change="↑ 0.8%"    changeModifier="up" />
      </div>

      <div className="chart-card">
        <div className="chart-card__title">API Consumption – 30 ngày</div>
        <Chart data={CHART_DATA_MONTHLY} />
      </div>
    </>
  );
}

// ─── Sidebar config ───
const SIDEBAR_ITEMS = [
  { id: "dashboard", icon: "📊", label: "Dashboard",        section: "Tổng quan" },
  { id: "users",     icon: "👥", label: "Người dùng",       section: "Quản lý" },
  { id: "cms",       icon: "📚", label: "Nội dung / CMS",   section: null },
  { id: "analytics", icon: "📈", label: "Analytics",        section: null },
];

const TAB_CONTENT = {
  dashboard: <AdminDashboard />,
  users:     <AdminUsers />,
  cms:       <AdminCMS />,
  analytics: <AdminAnalytics />,
};

// ─── AdminScreen ───
export default function AdminScreen() {
  const [tab, setTab] = useState("dashboard");

  return (
    <div className="admin">
      <div className="admin__layout">
        {/* Sidebar */}
        <aside className="admin__sidebar">
          {SIDEBAR_ITEMS.map((item, i) => (
            <div key={item.id}>
              {item.section && (
                <div
                  className="sidebar__section-label"
                  style={{ marginTop: i > 0 ? 24 : 0 }}
                >
                  {item.section}
                </div>
              )}
              <div
                className={`sidebar__item ${tab === item.id ? "sidebar__item--active" : ""}`}
                onClick={() => setTab(item.id)}
              >
                <span className="sidebar__icon">{item.icon}</span>
                {item.label}
              </div>
            </div>
          ))}
        </aside>

        {/* Main Content */}
        <main className="admin__main">
          {TAB_CONTENT[tab]}
        </main>
      </div>
    </div>
  );
}
