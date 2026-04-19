import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { useState, useCallback } from "react";

import "./user/styles/global.css";

import Admin from "./admin/pages/admin.jsx";
import Auth from "./user/pages/auth/auth.jsx";

import Nav from "./user/components/Nav";
import LoadingOverlay from "./user/components/LoadingOverlay";
import HomeScreen from "./user/pages/HomeScreen";
import LibraryScreen from "./user/pages/LibraryScreen";
import WorkspaceScreen from "./user/pages/WorkspaceScreen";
import AIScreen from "./user/pages/AIScreen";
import AdminScreen from "./user/pages/AdminScreen";
import ProfileScreen from "./user/pages/ProfileScreen";

const DEFAULT_USER = {
  firstName: "Quang Thảo",
  lastName: "Trương Như",
  email: "thaotruong@gmail.com",
  phone: "0901 234 567",
  birthYear: "2004",
  gender: "male",
  school: "THPT Nguyễn Huệ",
  grade: "12",
  bio: "",
};

function AppContent() {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(DEFAULT_USER);

  const location = useLocation();

  const showLoadingThen = useCallback((navigate) => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      navigate();
    }, 3500);
  }, []);

  const hideNavRoutes = ["/login", "/admin"];
  const showNav = !hideNavRoutes.includes(location.pathname);

  return (
    <div id="suky-root">
      {showNav && <Nav user={user} />}

      <LoadingOverlay visible={loading} />

      <Routes>
        <Route path="/" element={<HomeScreen />} />
        <Route path="/library" element={<LibraryScreen />} />
        <Route path="/workspace" element={<WorkspaceScreen />} />
        <Route path="/ai" element={<AIScreen />} />
        <Route
          path="/profile"
          element={<ProfileScreen user={user} setUser={setUser} />}
        />

        <Route path="/login" element={<Auth />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
