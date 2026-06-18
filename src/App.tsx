import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import Dashboard from "@/pages/Dashboard";
import SimulationView from "@/pages/SimulationView";
import DefectsPage from "@/pages/DefectsPage";
import AlertsPage from "@/pages/AlertsPage";
import HistoryPage from "@/pages/HistoryPage";

export default function App() {
  return (
    <Router>
      <div className="flex h-screen w-screen overflow-hidden bg-[#05030a] text-amber-50">
        <Sidebar />
        <main className="flex-1 overflow-hidden bg-gradient-to-br from-[#070503] via-[#0a0705] to-[#05030a]">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/simulation" element={<SimulationView />} />
            <Route path="/defects" element={<DefectsPage />} />
            <Route path="/alerts" element={<AlertsPage />} />
            <Route path="/history" element={<HistoryPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}
