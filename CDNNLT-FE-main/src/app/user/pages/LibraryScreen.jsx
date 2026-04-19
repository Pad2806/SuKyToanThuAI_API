import { useState } from "react";
import { FaLandmark, FaSearch, FaChartBar, FaBookOpen } from "react-icons/fa";
import { EVENTS } from "../data/constants";
import "../styles/LibraryScreen.css";

const CHIPS = ["Tất cả", "Lịch sử Việt Nam", "Lịch sử Thế giới", "Cổ đại", "Cận đại", "Thế chiến"];

// ─── EventCard ───
function EventCard({ ev, onAction }) {
  return (
    <div className="event-card">
      <div className="event-card__thumb" style={{ background: ev.bg }}>
        {ev.img ? (
          <img src={ev.img} alt={ev.title} className="event-card__thumb-inner" style={{ objectFit: 'cover' }} />
        ) : (
          <div className="event-card__thumb-inner">{ev.emoji}</div>
        )}
        <div className="event-card__era">{ev.era}</div>
      </div>

      <div className="event-card__body">
        <h3 className="event-card__title">{ev.title}</h3>
        <p className="event-card__desc">{ev.desc}</p>

        <div className="event-card__actions">
          <button className="btn-sm btn-sm--gold" onClick={onAction}>
            <FaChartBar style={{ marginRight: '6px' }} /> Tạo Slide
          </button>
          <button className="btn-sm btn-sm--red" onClick={onAction}>
            <FaBookOpen style={{ marginRight: '6px' }} /> Tạo Truyện tranh
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── LibraryScreen ───
export default function LibraryScreen({ showLoadingThen }) {
  const [activeChip, setActiveChip] = useState("Tất cả");

  return (
    <div className="library">
      {/* Header */}
      <div className="library__header">
        <h1 className="page-title">
          <FaLandmark style={{ marginRight: '10px', color: 'var(--gold)', verticalAlign: 'middle' }} /> 
          Thư viện Lịch sử
        </h1>
        <p className="page-subtitle">
          Khám phá kho tư liệu lịch sử được biên soạn cẩn thận — sẵn sàng để
          biến thành Slide hoặc Truyện tranh
        </p>

        <div className="search-filter-bar">
          <div className="search-input-wrapper" style={{ position: 'relative', flex: 1, minWidth: '260px' }}>
            <FaSearch style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-dim)' }} />
            <input
              className="search-input"
              type="text"
              placeholder="Tìm kiếm sự kiện lịch sử..."
              style={{ paddingLeft: '40px', width: '100%' }}
            />
          </div>
          <div className="filter-chips">
            {CHIPS.map((c) => (
              <button
                key={c}
                className={`chip ${activeChip === c ? "chip--active" : ""}`}
                onClick={() => setActiveChip(c)}
              >
                {c}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Events Grid */}
      <div className="events-grid">
        {EVENTS.map((ev) => (
          <EventCard
            key={ev.id}
            ev={ev}
            onAction={() => showLoadingThen("ai")}
          />
        ))}
      </div>
    </div>
  );
}
