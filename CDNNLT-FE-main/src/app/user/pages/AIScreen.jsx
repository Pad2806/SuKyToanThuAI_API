import { useState, useRef, useEffect, useCallback } from "react";
import { AI_REPLIES } from "../data/constants";
import "../styles/AIScreen.css";

// ─── Slide sub-components ───
function Slide1() {
  return (
    <div
      className="slide-preview slide-preview--editing"
      style={{ background: "linear-gradient(135deg,#180808 0%,#2D1008 50%,#180808 100%)" }}
    >
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", padding: 40, textAlign: "center" }}>
        <div style={{ fontSize: "0.6rem", letterSpacing: "0.3em", textTransform: "uppercase", color: "rgba(201,168,76,0.6)", marginBottom: 12 }}>
          Lịch sử Việt Nam
        </div>
        <div style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: "2rem", fontWeight: 700, lineHeight: 1.2, marginBottom: 10, color: "#F0E8D8" }}>
          Khởi Nghĩa<br />
          <em style={{ color: "var(--gold)" }}>Hai Bà Trưng</em>
        </div>
        <div style={{ fontSize: "0.65rem", color: "rgba(240,232,216,0.4)", letterSpacing: "0.1em" }}>
          Năm 40 Sau Công Nguyên
        </div>
        <div style={{ position: "absolute", bottom: 20, left: "50%", transform: "translateX(-50%)", fontSize: "2rem", opacity: 0.15 }}>🏯</div>
      </div>
      <div className="slide-preview__num">1 / 12</div>
      <div className="slide-preview__edit-hint">✏ Click để chỉnh sửa</div>
    </div>
  );
}

function Slide2() {
  return (
    <div
      className="slide-preview"
      style={{ background: "linear-gradient(135deg,#0C1018 0%,#101828 100%)" }}
    >
      <div style={{ display: "flex", height: "100%", padding: "32px 40px", gap: 40, alignItems: "center" }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: "0.55rem", color: "var(--gold)", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 8 }}>Bối cảnh</div>
          <div style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: "1.3rem", fontWeight: 700, marginBottom: 12, lineHeight: 1.3 }}>
            Việt Nam dưới ách đô hộ của nhà Hán
          </div>
          <ul style={{ fontSize: "0.68rem", color: "rgba(240,232,216,0.7)", lineHeight: 1.8, paddingLeft: 16 }}>
            <li>Nhà Hán đô hộ từ năm 111 TCN</li>
            <li>Bóc lột nặng nề về thuế má</li>
            <li>Đồng hóa văn hóa, ngôn ngữ</li>
            <li>Phân biệt đối xử tàn tệ</li>
          </ul>
        </div>
        <div style={{ width: 140, height: 140, borderRadius: "50%", background: "rgba(201,168,76,0.08)", border: "1px solid rgba(201,168,76,0.2)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "3.5rem", flexShrink: 0 }}>
          ⛓️
        </div>
      </div>
      <div className="slide-preview__num">2 / 12</div>
      <div className="slide-preview__edit-hint">✏ Click để chỉnh sửa</div>
    </div>
  );
}

function Slide3() {
  const leaders = [
    { e: "👑", name: "Trưng Trắc", desc: "Con gái Lạc tướng Mê Linh, chồng là Thi Sách bị giặc Hán giết hại." },
    { e: "⚔️", name: "Trưng Nhị",  desc: "Em gái Trưng Trắc, tướng giỏi, cùng chị lãnh đạo toàn bộ cuộc khởi nghĩa." },
  ];

  return (
    <div
      className="slide-preview"
      style={{ background: "linear-gradient(160deg,#14080A 0%,#220E10 60%,#18080A 100%)" }}
    >
      <div style={{ display: "flex", height: "100%", flexDirection: "column", justifyContent: "center", padding: "32px 40px" }}>
        <div style={{ fontSize: "0.55rem", color: "#D4846B", letterSpacing: "0.2em", textTransform: "uppercase", marginBottom: 8 }}>
          Lãnh đạo khởi nghĩa
        </div>
        <div style={{ fontFamily: "'Cormorant Garamond',serif", fontSize: "1.3rem", fontWeight: 700, marginBottom: 20 }}>
          Hai người phụ nữ làm rung chuyển lịch sử
        </div>
        <div style={{ display: "flex", gap: 20 }}>
          {leaders.map((l) => (
            <div key={l.name} style={{ flex: 1, background: "rgba(255,255,255,0.03)", border: "1px solid rgba(213,100,80,0.2)", borderRadius: 6, padding: 14 }}>
              <div style={{ fontSize: "1.4rem", marginBottom: 6 }}>{l.e}</div>
              <div style={{ fontSize: "0.8rem", fontWeight: 600, color: "#E8C97A", marginBottom: 4 }}>{l.name}</div>
              <div style={{ fontSize: "0.65rem", color: "rgba(240,232,216,0.5)", lineHeight: 1.6 }}>{l.desc}</div>
            </div>
          ))}
        </div>
      </div>
      <div className="slide-preview__num">3 / 12</div>
      <div className="slide-preview__edit-hint">✏ Click để chỉnh sửa</div>
    </div>
  );
}

// ─── AIScreen ───
export default function AIScreen({ setScreen }) {
  const initialMessages = [
    {
      role: "ai",
      content: (
        <>
          <p>Xin chào! Mình đã đọc xong nội dung về <strong>Khởi nghĩa Hai Bà Trưng</strong>. 📜</p>
          <p>Bạn muốn thiết kế Slide theo phong cách nào?</p>
        </>
      ),
      opts: ["🎓 Chuyên nghiệp / Học thuật", "🎨 Sinh động / Học sinh", "🏮 Cổ điển / Truyền thống"],
    },
  ];

  const [messages, setMessages]   = useState(initialMessages);
  const [inputVal, setInputVal]   = useState("");
  const [replyIdx, setReplyIdx]   = useState(0);
  const messagesEndRef             = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMsg = useCallback(
    (text) => {
      setMessages((prev) => [...prev, { role: "user", text }]);
      setTimeout(() => {
        if (replyIdx < AI_REPLIES.length) {
          const r = AI_REPLIES[replyIdx];
          setMessages((prev) => [...prev, { role: "ai", text: r.text, opts: r.opts }]);
          setReplyIdx((i) => i + 1);
        }
      }, 600);
    },
    [replyIdx]
  );

  const handleSend = () => {
    const val = inputVal.trim();
    if (!val) return;
    sendMsg(val);
    setInputVal("");
  };

  return (
    <div className="ai-screen">
      {/* ── Topbar ── */}
      <div className="ai-topbar">
        <div className="ai-topbar__left">
          <button className="ai-topbar__back" onClick={() => setScreen("library")}>
            ← Quay lại
          </button>
          <div className="ai-topbar__project">
            <span className="ai-topbar__dot" />
            Khởi nghĩa Hai Bà Trưng – Slide 12 trang
          </div>
        </div>
        <div className="ai-topbar__right">
          <button className="btn-icon">🔗 Chia sẻ</button>
          <button className="btn-icon btn-icon--primary">⬇ Xuất file</button>
        </div>
      </div>

      {/* ── Split Layout ── */}
      <div className="ai-split">
        {/* Chat Panel */}
        <div className="chat-panel">
          <div className="chat-panel__header">💬 AI Trợ lý</div>

          <div className="chat-panel__messages">
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role === "user" ? "msg--user" : ""}`}>
                <div className={`msg__avatar msg__avatar--${m.role}`}>
                  {m.role === "ai" ? "AI" : "Bạn"}
                </div>
                <div className={`msg__bubble msg__bubble--${m.role}`}>
                  {m.content || <p>{m.text}</p>}
                  {m.opts && (
                    <div className="chat-options">
                      {m.opts.map((o, j) => (
                        <button key={j} className="chat-option" onClick={() => sendMsg(o)}>
                          {o}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-panel__input-area">
            <input
              className="chat-input"
              type="text"
              placeholder="Nhập yêu cầu của bạn..."
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
            />
            <button className="chat-send" onClick={handleSend}>➤</button>
          </div>
        </div>

        {/* Canvas Panel */}
        <div className="canvas-panel">
          <div className="canvas-toolbar">
            <button className="canvas-tab canvas-tab--active">Xem trước</button>
            <div className="canvas-tab-divider" />
            <button className="canvas-tab">Slide 1</button>
            <button className="canvas-tab">Slide 2</button>
            <button className="canvas-tab">Slide 3</button>
            <button className="canvas-tab" style={{ color: "var(--text-dim)" }}>
              + 9 trang khác
            </button>
            <div className="canvas-zoom">
              <button className="canvas-zoom__btn">−</button>
              <span>100%</span>
              <button className="canvas-zoom__btn">+</button>
            </div>
          </div>

          <div className="canvas-content">
            <Slide1 />
            <Slide2 />
            <Slide3 />
            <p className="canvas-more-hint">
              ... 9 trang còn lại đang được AI tạo ra •{" "}
              <span>Xem tất cả</span>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
