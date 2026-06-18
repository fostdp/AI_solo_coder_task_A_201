import { NavLink } from "react-router-dom";
import { LayoutDashboard, Box, TriangleAlert, AlertOctagon, History, Anvil } from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "监控仪表盘" },
  { to: "/simulation", icon: Box, label: "充型仿真" },
  { to: "/defects", icon: TriangleAlert, label: "缺陷预测" },
  { to: "/alerts", icon: AlertOctagon, label: "告警中心" },
  { to: "/history", icon: History, label: "历史回放" },
];

export function Sidebar() {
  return (
    <aside className="flex h-screen w-60 shrink-0 flex-col border-r border-amber-900/30 bg-gradient-to-b from-[#0a0807] via-[#100b08] to-[#0a0807]">
      <div className="flex items-center gap-3 border-b border-amber-900/30 px-5 py-5">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-amber-600 to-amber-900 shadow-[0_0_20px_rgba(184,115,51,0.35)]">
          <Anvil className="h-5 w-5 text-amber-50" />
        </div>
        <div className="min-w-0">
          <div className="font-serif text-base font-bold tracking-wider text-amber-300">失蜡铸造</div>
          <div className="text-[10px] tracking-[0.2em] text-amber-500/70">LOST WAX CASTING</div>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${
                isActive
                  ? "bg-gradient-to-r from-amber-700/30 to-amber-900/10 text-amber-200 shadow-[inset_2px_0_0_0_#d4af37]"
                  : "text-amber-100/60 hover:bg-amber-900/15 hover:text-amber-200"
              }`
            }
          >
            <Icon className="h-4.5 w-4.5 shrink-0" />
            <span className="font-medium tracking-wide">{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-amber-900/30 p-4">
        <div className="rounded-lg border border-amber-800/30 bg-black/40 p-3">
          <div className="mb-1 text-[10px] uppercase tracking-[0.15em] text-amber-500/60">工艺阶段</div>
          <div className="text-sm font-medium text-amber-200">曾侯乙尊盘复原 · 实验001</div>
          <div className="mt-2 flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            <span className="text-xs text-emerald-400">仿真运行中</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
