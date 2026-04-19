import { Routes, Route } from "react-router-dom";
import Admin from "../pages/admin";

export default function AdminRoutes() {
  return (
    <Routes>
      <Route path="/admin" element={<Admin />} />
    </Routes>
  );
}
