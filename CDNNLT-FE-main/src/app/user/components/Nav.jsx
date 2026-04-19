import { useState, useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../styles/Nav.css";

export default function Nav({ user }) {
  const [open, setOpen] = useState(false);
  const dropRef = useRef(null);

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    function handleClick(e) {
      if (dropRef.current && !dropRef.current.contains(e.target)) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const initials = user
    ? `${user.firstName?.[0] ?? ""}${user.lastName?.[0] ?? ""}`.toUpperCase()
    : "HT";

  const links = [
    { path: "/", label: "Trang chủ" },
    { path: "/library", label: "Thư viện Lịch sử" },
    { path: "/workspace", label: "Sáng tạo" },
  ];

  function go(path) {
    setOpen(false);
    navigate(path);
  }

  return (
    <nav className="nav">
      <div className="nav__logo" onClick={() => navigate("/")}>
        Sử<span>Ký</span> AI
      </div>

      <div className="nav__links">
        {links.map((l) => (
          <button
            key={l.path}
            className={`nav__btn ${location.pathname === l.path ? "nav__btn--active" : ""
              }`}
            onClick={() => navigate(l.path)}
          >
            {l.label}
          </button>
        ))}

        <button
          className={`nav__btn nav__btn--admin ${location.pathname === "/admin" ? "nav__btn--active" : ""
            }`}
          onClick={() => navigate("/admin")}
        >
          ⚙ Admin
        </button>
      </div>

      <div className="nav__user" ref={dropRef}>
        <div className="nav__avatar" onClick={() => setOpen((v) => !v)}>
          {initials}
        </div>

        {open && (
          <div className="nav__dropdown">
            <div className="nav__dropdown-header">
              <div className="nav__dropdown-avatar">{initials}</div>
              <div>
                <div className="nav__dropdown-name">
                  {user
                    ? `${user.firstName} ${user.lastName}`
                    : "Hoàng Tuấn"}
                </div>
                <div className="nav__dropdown-email">
                  {user?.email ?? "hoang.tuan@gmail.com"}
                </div>
              </div>
            </div>

            <div className="nav__dropdown-items">
              <button
                className="nav__dropdown-item"
                onClick={() => go("/profile")}
              >
                <span className="nav__dropdown-item__icon">👤</span>
                Thông tin người dùng
              </button>

              <div className="nav__dropdown-divider" />

              <button
                className="nav__dropdown-item nav__dropdown-item--danger"
                onClick={() => {
                  setOpen(false);
                  navigate("/login");
                }}
              >
                <span className="nav__dropdown-item__icon">🚪</span>
                Đăng xuất
              </button>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}