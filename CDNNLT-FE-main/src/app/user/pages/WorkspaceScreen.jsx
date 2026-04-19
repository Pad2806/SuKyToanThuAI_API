import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { FaChartBar, FaBookOpen, FaMap, FaCloudUploadAlt, FaRocket } from "react-icons/fa";
import "../styles/WorkspaceScreen.css";

const OUTPUT_OPTIONS = [
  { icon: <FaChartBar />, label: "Bài Slide",    desc: "PowerPoint / PDF" },
  { icon: <FaBookOpen />, label: "Truyện tranh", desc: "Manga / Webtoon"  },
  { icon: <FaMap />,      label: "Infographic",  desc: "Timeline / Map"   },
];

const FILE_TYPES = ["PDF", "DOCX", "TXT", "PPTX", "JPG"];

export default function WorkspaceScreen() {
  const [selectedOutput, setSelectedOutput] = useState(0);
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="workspace">
      <div className="workspace__container">
        <h1 className="workspace__title">Tạo từ nội dung của bạn</h1>
        <p className="workspace__sub">
          Tải lên tài liệu hoặc nhập văn bản — AI sẽ chuyển hóa thành sản
          phẩm học tập tuyệt vời
        </p>

        {/* Upload Zone */}
        <div className="upload-zone" onClick={handleUploadClick}>
          <input 
            type="file" 
            ref={fileInputRef} 
            style={{ display: 'none' }} 
            accept=".pdf,.docx,.txt,.pptx,.jpg,.jpeg,.png" 
          />
          <div className="upload-zone__icon">
            <FaCloudUploadAlt style={{ color: 'var(--gold)' }} />
          </div>
          <div className="upload-zone__title">Kéo thả file vào đây</div>
          <div className="upload-zone__sub">
            hoặc click để chọn file từ máy tính
          </div>
          <div className="upload-zone__types">
            {FILE_TYPES.map((t) => (
              <span key={t} className="type-tag">{t}</span>
            ))}
          </div>
        </div>

        {/* Divider */}
        <div className="divider">hoặc nhập văn bản</div>

        {/* Textarea */}
        <textarea
          className="text-area"
          placeholder="Dán nội dung lịch sử vào đây... VD: Khởi nghĩa Hai Bà Trưng năm 40 SCN do Trưng Trắc và Trưng Nhị lãnh đạo..."
        />

        {/* Output Select */}
        <p className="output-select__label">Chọn định dạng đầu ra</p>
        <div className="output-select">
          {OUTPUT_OPTIONS.map((o, i) => (
            <div
              key={i}
              className={`output-option ${selectedOutput === i ? "output-option--selected" : ""}`}
              onClick={() => setSelectedOutput(i)}
            >
              <div className="output-option__icon">{o.icon}</div>
              <div className="output-option__label">{o.label}</div>
              <div className="output-option__desc">{o.desc}</div>
            </div>
          ))}
        </div>

        {/* Start Button */}
        <button
          className="start-btn"
          onClick={() => navigate("/ai")}
        >
          <FaRocket style={{ marginRight: '8px' }} /> Bắt đầu tạo với AI
        </button>
      </div>
    </div>
  );
}
