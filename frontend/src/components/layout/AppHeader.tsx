import { Sparkles } from "lucide-react";

export function AppHeader() {
  return (
    <header className="panel mb-4 overflow-hidden">
      <div className="flex flex-col gap-3 bg-gradient-to-r from-[#f8faf9] to-[#e9f6ee] p-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="mb-1 flex items-center gap-2 text-xs font-bold uppercase text-[#16834f]">
            <Sparkles size={15} />
            Operations analytics agent
          </p>
          <h1 className="text-3xl font-bold text-[#202423]">
            Rappi Operations Intelligence
          </h1>
          <p className="mt-2 max-w-3xl text-sm text-[#53625b]">
            Choose an LLM provider, ask business questions, inspect evidence and
            generate an executive readout from the same operational dataset.
          </p>
        </div>
        <div className="rounded-lg border border-[#cfe2d5] bg-white px-4 py-3 text-sm text-[#315246]">
          LangGraph planner + pandas tools
        </div>
      </div>
    </header>
  );
}
