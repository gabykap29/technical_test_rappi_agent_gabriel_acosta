import Image from "next/image";
import { Sparkles, Moon, Sun } from "lucide-react";

type Theme = "light" | "dark";

type AppHeaderProps = {
  theme: Theme;
  onToggleTheme: () => void;
};

export function AppHeader({ theme, onToggleTheme }: AppHeaderProps) {
  const isDark = theme === "dark";

  return (
    <header className={`panel mb-4 overflow-hidden ${isDark ? 'bg-gray-900 border-gray-700' : 'bg-white'}`}>
      <div className={`flex flex-col gap-3 bg-gradient-to-r ${isDark ? 'from-[#211513] to-[#352018]' : 'from-[#fff7f2] to-[#ffe2d1]'} p-6 md:flex-row md:items-center md:justify-between`}>
        <div className="flex min-w-0 items-center gap-4">
          <Image
            alt="Rappi"
            className="h-14 w-14 rounded-lg bg-white object-contain p-2 shadow-sm"
            height={56}
            src="/rappi-seeklogo.png"
            width={56}
          />
          <div className="min-w-0">
            <p className="mb-1 flex items-center gap-2 text-xs font-bold uppercase text-[var(--accent)]">
              <Sparkles size={15} />
              Operations analytics agent
            </p>
            <h1 className="text-theme text-3xl font-bold">
              Rappi Operations Intelligence
            </h1>
            <p className="text-theme-muted mt-2 max-w-3xl text-sm">
              Choose an LLM provider, ask business questions, inspect evidence and
              generate an executive readout from the same operational dataset.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            className={`rounded-lg border px-3 py-2 text-sm hover:bg-gray-100 ${isDark ? 'border-[#5a3328] bg-[var(--surface)] text-gray-200 hover:bg-[#2a1b18]' : 'border-[#ffd1bc] bg-white text-[#7a2a1a] hover:bg-[#fff0e7]'}`}
            onClick={onToggleTheme}
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <div className={`text-theme rounded-lg border px-4 py-3 text-sm ${isDark ? 'border-[#5a3328] bg-[var(--surface)]' : 'border-[#ffd1bc] bg-white'}`}>
            LangGraph planner + pandas tools
          </div>
        </div>
      </div>
    </header>
  );
}
