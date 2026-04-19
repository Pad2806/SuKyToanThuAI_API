import { useNavigate } from "react-router-dom";
import { FaLandmark, FaPen } from "react-icons/fa";
import { RECENT_WORKS } from "../data/constants";
import "../styles/HomeScreen.css";

// ─── WorkCard ───
function WorkCard({ work, onClick }) {
  return (
    <div className="work-card" onClick={onClick}>
      <div className="work-card__thumb">
        <div
          className="work-card__thumb-bg"
          style={{ background: work.bg }}
        >
          {work.img ? (
            <img src={work.img} alt={work.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          ) : (
            work.emoji
          )}
        </div>
        <span className={`work-card__badge work-card__badge--${work.badgeKey}`}>
          {work.badge}
        </span>
      </div>
      <div className="work-card__info">
        <div className="work-card__title">{work.title}</div>
        <div className="work-card__meta">
          <span>{work.meta}</span>
          <span>{work.time}</span>
        </div>
      </div>
    </div>
  );
}

// ─── HomeScreen ───
export default function HomeScreen({ setScreen, showLoadingThen }) {
  const navigate = useNavigate();
  
  return (
    <div className="home">
      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero__bg" />
        <div className="hero__ring" />
        <div className="hero__vertical">Lịch Sử Việt Nam & Thế Giới</div>

        <div className="hero__content">
          <div className="hero__eyebrow fade-up-1">
            Nền tảng học lịch sử thế hệ mới
          </div>

          <h1 className="hero__title fade-up-2">
            Lịch sử trở nên
            <em>sống động</em>
          </h1>

          <p className="hero__desc fade-up-3">
            Biến những trang sử khô khan thành Slide thuyết trình ấn tượng hoặc
            Truyện tranh hấp dẫn — chỉ trong vài phút, cùng AI.
          </p>

          <div className="hero__cta fade-up-4">
            <button
              className="btn-primary"
              onClick={() => navigate("/library")}
            >
              <FaLandmark style={{ marginRight: '8px' }} /> Khám phá Sự kiện Lịch sử
            </button>
            <button
              className="btn-secondary"
              onClick={() => navigate("/workspace")}
            >
              <FaPen style={{ marginRight: '8px' }} /> Tạo từ nội dung của bạn
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="hero__stats fade-up-5">
          {[
            { num: "48+", label: "Sự kiện lịch sử" },
            { num: "2.4K", label: "Slide đã tạo" },
            { num: "890", label: "Truyện tranh" },
          ].map((s) => (
            <div key={s.label}>
              <div className="stat-item__num">{s.num}</div>
              <div className="stat-item__label">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Recent Works ── */}
      <section className="section">
        <div className="section__header">
          <h2 className="section__title">Dự án gần đây</h2>
          <button className="section__more">Xem tất cả →</button>
        </div>

        <div className="works-grid">
          {RECENT_WORKS.map((w, i) => (
            <WorkCard
              key={i}
              work={w}
              onClick={() => w.goAi && navigate("/ai")}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
