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
      <div className={`flex flex-col gap-3 bg-gradient-to-r ${isDark ? 'from-gray-800 to-gray-700' : 'from-[#f8faf9] to-[#e9f6ee]'} p-6 md:flex-row md:items-center md:justify-between`}>
        <div>
          <p className={`mb-1 flex items-center gap-2 text-xs font-bold uppercase ${isDark ? 'text-green-400' : 'text-[#16834f]'}`}>
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
        <div className="flex items-center gap-3">
          <button
            className={`rounded-lg border px-3 py-2 text-sm hover:bg-gray-100 ${isDark ? 'border-gray-600 bg-gray-800 text-gray-200 hover:bg-gray-700' : 'border-[#cfe2d5] bg-white text-[#315246] hover:bg-gray-50'}`}
            onClick={onToggleTheme}
          >
            {isDark ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <div className={`text-theme rounded-lg border px-4 py-3 text-sm ${isDark ? 'border-gray-600 bg-gray-800' : 'border-[#cfe2d5] bg-white'}`}>
            LangGraph planner + pandas tools
          </div>
        </div>
      </div>
    </header>
  );
}
