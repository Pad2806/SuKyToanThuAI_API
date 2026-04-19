import { useState } from "react";
import { FaEye, FaEyeSlash } from "react-icons/fa";
import SocialLogin from "../../components/login/SocialLogin";
import styles from "./auth.module.scss";

export default function Auth() {
  const [activeTab, setActiveTab] = useState("login");
  const [showLoginPassword, setShowLoginPassword] = useState(false);
  const [showRegisterPassword, setShowRegisterPassword] = useState(false);

  return (
    <div className={styles.authContainer}>
      <div className={styles.authImagePanel}>
        <div className={styles.imageOverlay}>
          <h2>Hành Trình Gìn Giữ Lịch Sử</h2>
          <p>
            Cùng nhau khám phá và làm sống lại những trang sử hào hùng của dân
            tộc Việt Nam.
          </p>
        </div>
      </div>
      <div className={styles.authFormPanel}>
        <div className={styles.authBox}>
          <div className={styles.logo}>
            Sử<span>Ký</span> AI
          </div>

          <div className={styles.tabHeader}>
            <button
              className={`${styles.tabBtn} ${activeTab === "login" ? styles.active : ""}`}
              onClick={() => setActiveTab("login")}
            >
              Đăng nhập
            </button>
            <button
              className={`${styles.tabBtn} ${activeTab === "register" ? styles.active : ""}`}
              onClick={() => setActiveTab("register")}
            >
              Đăng ký
            </button>
          </div>

          <div className={styles.formContent}>
            {activeTab === "login" ? (
              <form
                className={styles.form}
                onSubmit={(e) => e.preventDefault()}
              >
                <div className={styles.inputGroup}>
                  <label>Email / Tên đăng nhập</label>
                  <input type="text" placeholder="Nhập email của bạn" />
                </div>
                <div className={styles.inputGroup}>
                  <label>Mật khẩu</label>
                  <div className={styles.passwordInputWrapper}>
                    <input
                      type={showLoginPassword ? "text" : "password"}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      className={styles.eyeBtn}
                      onClick={() => setShowLoginPassword(!showLoginPassword)}
                    >
                      {showLoginPassword ? <FaEyeSlash /> : <FaEye />}
                    </button>
                  </div>
                </div>
                <div className={styles.options}>
                  <label className={styles.checkbox}>
                    <input type="checkbox" /> Ghi nhớ
                  </label>
                  <span className={styles.forgot}>Quên mật khẩu?</span>
                </div>
                <button type="submit" className={styles.submitBtn}>
                  Vào thế giới sử học
                </button>
              </form>
            ) : (
              <form
                className={styles.form}
                onSubmit={(e) => e.preventDefault()}
              >
                <div className={styles.inputGroup}>
                  <label>Họ và tên</label>
                  <input type="text" placeholder="Nhập họ và tên" />
                </div>
                <div className={styles.inputGroup}>
                  <label>Email</label>
                  <input type="email" placeholder="example@mail.com" />
                </div>
                <div className={styles.inputGroup}>
                  <label>Mật khẩu</label>
                  <div className={styles.passwordInputWrapper}>
                    <input
                      type={showRegisterPassword ? "text" : "password"}
                      placeholder="Tối thiểu 8 ký tự"
                    />
                    <button
                      type="button"
                      className={styles.eyeBtn}
                      onClick={() => setShowRegisterPassword(!showRegisterPassword)}
                    >
                      {showRegisterPassword ? <FaEyeSlash /> : <FaEye />}
                    </button>
                  </div>
                </div>
                <button type="submit" className={styles.submitBtn}>
                  Tạo tài khoản
                </button>
              </form>
            )}

            <div className={styles.divider}>
              <span>Hoặc</span>
            </div>

            <SocialLogin />
          </div>

          <p className={styles.footerText}>
            Bằng việc tiếp tục, bạn đồng ý với Điều khoản dịch vụ của SửKý AI.
          </p>
        </div>
      </div>
    </div>
  );
}
