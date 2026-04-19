import { Outlet } from "react-router-dom";
import Sidebar from "./components/Sidebar/Sidebar";
import styles from "./AdminLayout.module.scss";

export default function AdminLayout() {
  return (
    <div className={styles.layout}>
      <Sidebar />
      <div className={styles.main}>
        <Outlet />
      </div>
    </div>
  );
}
