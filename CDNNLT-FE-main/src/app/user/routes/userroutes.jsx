import { Routes, Route } from "react-router-dom";
import Auth from "../pages/login/auth";

export default function UserRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Auth />} />
    </Routes>
  );
}
