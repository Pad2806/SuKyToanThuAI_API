import styles from "./SideBar.module.scss";
import {
  LuLayoutDashboard,
  LuUsers,
  LuBookOpen,
  LuKey,
  LuSettings,
  LuList
} from "react-icons/lu";

export default function Sidebar({ activeTab, setActiveTab }) {
  const menuData = [
    {
      title: "TỔNG QUAN",
      items: [
        { key: "dashboard", label: "Dashboard", icon: <LuLayoutDashboard /> },
      ],
    },
    {
      title: "QUẢN LÝ",
      items: [
        { key: "users", label: "Người dùng", icon: <LuUsers /> },
        { key: "events", label: "Sự kiện lịch sử", icon: <LuBookOpen /> },
        { key: "categories", label: "Danh mục", icon: <LuList /> },
      ],
    },
    {
      title: "HỆ THỐNG",
      items: [
        { key: "api", label: "API Keys", icon: <LuKey /> },
        { key: "settings", label: "Cài đặt", icon: <LuSettings /> },
      ],
    },
  ];

  return (
    <div className={styles.sidebar}>
      <div className={styles.logo}>
        Sử<span>Ký</span> AI
      </div>

      {menuData.map((section, idx) => (
        <div key={idx} className={styles.section}>
          <div className={styles.label}>{section.title}</div>
          {section.items.map((item) => (
            <div
              key={item.key}
              className={`${styles.item} ${activeTab === item.key ? styles.active : ""}`}
              onClick={() => setActiveTab(item.key)}
            >
              <span className={styles.icon}>{item.icon}</span>
              <span className={styles.text}>{item.label}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
