import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Header from "./components/Header.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import History from "./pages/History.jsx";
import Monitors from "./pages/Monitors.jsx";

export default function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Header />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/entry/:entryId" element={<Dashboard />} />
          <Route path="/monitors" element={<Monitors />} />
          <Route path="/history" element={<History />} />
        </Routes>
      </div>
    </Router>
  );
}
