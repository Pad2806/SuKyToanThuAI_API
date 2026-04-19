import { useState } from "react";
import { LuEye, LuEyeOff } from "react-icons/lu";
import Sidebar from "../components/sidebar/SideBar";
import DashboardCard from "../components/dashboardcard/DashboardCard";
import EventItem from "../components/eventitem/EventItem";
import styles from "./admin.module.scss";

import imgBHT from "../assets/images/hbt.png";
import imgDBP from "../assets/images/dbp.png";
import imgQThanh from "../assets/images/qthanh.png";

export default function Admin() {
  const [activeTab, setActiveTab] = useState("events");
  const [showEventForm, setShowEventForm] = useState(false);
  const [showCategoryForm, setShowCategoryForm] = useState(false);
  const [showUserForm, setShowUserForm] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const renderContent = () => {
    switch (activeTab) {
      case "dashboard":
        return (
          <div className={styles.fadeUp}>
            <h1 className={styles.title}>Dashboard</h1>
            <p className={styles.subtitle}>
              Tổng quan hệ thống – Cập nhật lúc 09:41 sáng nay
            </p>

            <div className={styles.kpiGrid}>
              <DashboardCard title="Tổng người dùng" value="2,418" />
              <DashboardCard title="Slide đã tạo" value="4,832" />
              <DashboardCard title="Truyện tranh" value="1,290" />
              <DashboardCard title="API Requests" value="8,247" />
            </div>

            <div className={styles.chartCard}>
              <h3>Lưu lượng sử dụng – 30 ngày qua</h3>
              <div className={styles.chartBars}>
                {[
                  40, 70, 45, 90, 65, 80, 30, 100, 50, 85, 40, 70, 45, 90, 65,
                  80, 30, 100, 50, 85,
                ].map((h, i) => (
                  <div
                    key={i}
                    className={styles.bar}
                    style={{ height: `${h}%` }}
                  />
                ))}
              </div>
            </div>

            <div className={styles.activities}>
              <h3>Hoạt động gần đây</h3>
              <table className={styles.activityTable}>
                <thead>
                  <tr>
                    <th>Người dùng</th>
                    <th>Hành động</th>
                    <th>Thời gian</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Nguyễn Lan</td>
                    <td>Đăng ký tài khoản</td>
                    <td>12 Jan 2025</td>
                    <td style={{ color: "#84c794" }}>● Active</td>
                  </tr>
                  <tr>
                    <td>Trần Hùng</td>
                    <td>Đăng nhập</td>
                    <td>28 Feb 2025</td>
                    <td style={{ color: "#84c794" }}>● Active</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        );

      case "users":
        return (
          <div className={styles.fadeUp}>
            <h1 className={styles.title}>Quản lý người dùng</h1>
            <p className={styles.subtitle}>2,418 tài khoản đăng ký</p>

            <div className={styles.userToolbar}>
              <input
                type="text"
                placeholder="Tìm kiếm theo tên hoặc email..."
                className={styles.searchInput}
              />

              <div style={{ display: 'flex', gap: '16px' }}>
                <select className={styles.filterSelect}>
                  <option>Tất cả trạng thái</option>
                  <option>Đang hoạt động</option>
                  <option>Ngừng hoạt động</option>
                </select>
                <button className={styles.btn_add} onClick={() => setShowUserForm(true)}>
                  + Thêm người dùng mới
                </button>
              </div>
            </div>

            <table className={styles.adminTable}>
              <thead>
                <tr>
                  <th>Người dùng</th>
                  <th>Ngày đăng ký</th>
                  <th>Trạng thái</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Nguyễn Lan (lan.nguyen@email.com)</td>
                  <td>12 Jan 2025</td>
                  <td style={{ color: "#84c794" }}>● Active</td>
                  <td className={styles.actionCell}>
                    <button className={styles.btn_edit}>Sửa</button>
                    <button className={styles.btn_del}>Xóa</button>
                  </td>
                </tr>

                <tr>
                  <td>Trần Hùng (hung.tran@gmail.com)</td>
                  <td>28 Feb 2025</td>
                  <td style={{ color: "#84c794" }}>● Active</td>
                  <td className={styles.actionCell}>
                    <button className={styles.btn_edit}>Sửa</button>
                    <button className={styles.btn_del}>Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>

            {showUserForm && (
              <div className={styles.modalOverlay}>
                <div className={styles.modalBoxLarge}>
                  <h2>Thêm người dùng mới</h2>
                  <div className={styles.formGrid}>
                    <input type="text" placeholder="Họ và tên" autoComplete="off" />
                    <input type="email" placeholder="Email (duy nhất)" autoComplete="off" />
                    
                    <div style={{ position: 'relative' }}>
                      <input 
                        type={showPassword ? "text" : "password"} 
                        placeholder="Mật khẩu" 
                        autoComplete="new-password"
                      />
                      <div 
                        onClick={() => setShowPassword(!showPassword)}
                        style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', cursor: 'pointer', color: '#9a8f7c', display: 'flex' }}
                      >
                       {showPassword ? <LuEyeOff size={18} /> : <LuEye size={18} />}
                      </div>
                    </div>
                    
                    <input type="number" placeholder="Số điểm Credits" />
                    
                    <select>
                      <option value="">Chọn vai trò...</option>
                      <option value="user">Người dùng (User)</option>
                      <option value="admin">Quản trị viên (Admin)</option>
                    </select>
                    
                    <select>
                      <option value="">Phương thức đăng nhập...</option>
                      <option value="local">Tài khoản thường (Local)</option>
                      <option value="google">Google</option>
                      <option value="facebook">Facebook</option>
                    </select>
                  </div>
                  <div className={styles.formActions}>
                    <button className={styles.btn_add}>Lưu người dùng</button>
                    <button
                      className={styles.btn_close}
                      onClick={() => setShowUserForm(false)}
                    >
                      Đóng
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case "categories":
        return (
          <div className={styles.fadeUp}>
            <h1 className={styles.title}>Danh mục</h1>
            <p className={styles.subtitle}>Quản lý phân loại sự kiện / bài viết</p>

            <div className={styles.userToolbar}>
              <input
                type="text"
                placeholder="Tìm kiếm danh mục..."
                className={styles.searchInput}
              />
              <button className={styles.btn_add} onClick={() => setShowCategoryForm(true)}>
                + Thêm danh mục
              </button>
            </div>

            <table className={styles.adminTable}>
              <thead>
                <tr>
                  <th>Tên danh mục</th>
                  <th>Mô tả</th>
                  <th>Sự kiện</th>
                  <th>Hành động</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Triều đại phong kiến</td>
                  <td>Các triều đại trong lịch sử Việt Nam</td>
                  <td>120</td>
                  <td className={styles.actionCell}>
                    <button className={styles.btn_edit}>Sửa</button>
                    <button className={styles.btn_del}>Xóa</button>
                  </td>
                </tr>
                <tr>
                  <td>Trận chiến lịch sử</td>
                  <td>Những trận đánh nổi bật</td>
                  <td>85</td>
                  <td className={styles.actionCell}>
                    <button className={styles.btn_edit}>Sửa</button>
                    <button className={styles.btn_del}>Xóa</button>
                  </td>
                </tr>
              </tbody>
            </table>

            {showCategoryForm && (
              <div className={styles.modalOverlay}>
                <div className={styles.modalBoxLarge} style={{ width: '500px' }}>
                  <h2>Thêm danh mục mới</h2>
                  <input placeholder="Tên danh mục" />
                  <textarea rows="4" placeholder="Mô tả danh mục" />
                  <div className={styles.formActions}>
                    <button className={styles.btn_add}>Lưu danh mục</button>
                    <button
                      className={styles.btn_close}
                      onClick={() => setShowCategoryForm(false)}
                    >
                      Đóng
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      case "events":
        return (
          <div className={styles.fadeUp}>
            <h1 className={styles.title}>Sự kiện lịch sử</h1>
            <p className={styles.subtitle}>Quản lý thư viện sự kiện</p>

            <div className={styles.cmsGrid}>
              <div className={styles.eventWrapper}>
                <EventItem
                  title="Khởi nghĩa Hai Bà Trưng"
                  desc="Cuộc khởi nghĩa đầu tiên của phụ nữ Việt Nam chống lại ách đô hộ nhà Hán do Trưng Trắc và Trưng Nhị lãnh đạo."
                  status="Đã đăng"
                  image={imgBHT}
                />
                <div className={styles.hoverActions}>
                  <button className={styles.btn_edit}>Sửa</button>
                  <button className={styles.btn_del}>Xóa</button>
                </div>
              </div>

              <div className={styles.eventWrapper}>
                <EventItem
                  title="Chiến thắng Điện Biên Phủ"
                  desc="Trận quyết chiến chiến lược kết thúc thắng lợi kháng chiến chống Pháp, chấn động địa cầu."
                  status="Đã đăng"
                  image={imgDBP}
                />
                <div className={styles.hoverActions}>
                  <button className={styles.btn_edit}>Sửa</button>
                  <button className={styles.btn_del}>Xóa</button>
                </div>
              </div>

              <div className={styles.eventWrapper}>
                <EventItem
                  title="Đại phá quân Thanh"
                  desc="Vua Quang Trung tiến quân thần tốc vây đánh đồn Ngọc Hồi, Đống Đa làm nên chiến thắng lịch sử."
                  status="Nháp"
                  image={imgQThanh}
                />
                <div className={styles.hoverActions}>
                  <button className={styles.btn_edit}>Sửa</button>
                  <button className={styles.btn_del}>Xóa</button>
                </div>
              </div>

              <div className={styles.addCard} onClick={() => setShowEventForm(true)}>
                <span className={styles.plus}>+</span>
                <p>Thêm sự kiện</p>
              </div>
            </div>

            {showEventForm && (
              <div className={styles.modalOverlay}>
                <div className={styles.modalBoxLarge}>
                  <h2>Đăng sự kiện lịch sử mới</h2>

                  <div className={styles.formGrid}>
                    <input placeholder="Tiêu đề sự kiện" />
                    <input placeholder="Năm bắt đầu (VD: 1954)" />
                    <input placeholder="Năm kết thúc (VD: Dấu - hoặc để trống)" />
                    <input placeholder="Nhân vật chính" />
                    <input placeholder="Địa điểm" />
                    <select>
                      <option value="">Chọn danh mục...</option>
                      <option value="1">Triều đại phong kiến</option>
                      <option value="2">Trận chiến lịch sử</option>
                    </select>
                    <select>
                      <option value="">Trạng thái...</option>
                      <option value="published">Đã đăng</option>
                      <option value="draft">Nháp</option>
                    </select>
                  </div>

                  <textarea rows="4" placeholder="Mô tả ngắn sự kiện" />

                  <textarea rows="6" placeholder="Nội dung chi tiết sự kiện" />

                  <textarea rows="4" placeholder="Ý nghĩa lịch sử" />

                  <div className={styles.uploadBox}>
                    <label>Ảnh đại diện sự kiện</label>
                    <input type="file" accept="image/*" />
                  </div>

                  <div className={styles.formActions}>
                    <button className={styles.btn_add}>Đăng sự kiện</button>
                    <button
                      className={styles.btn_close}
                      onClick={() => setShowEventForm(false)}
                    >
                      Đóng
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        );

      default:
        return <h1>Không có dữ liệu</h1>;
    }
  };

  return (
    <div className={styles.layout}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className={styles.content}>{renderContent()}</div>
    </div>
  );
}
