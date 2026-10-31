import React from "react";
import { SlidersHorizontal, ArrowRightLeft, Calendar, RotateCcw } from "lucide-react";

export interface ResearchScopeFilters {
  scJudgments: boolean;
  hcJudgments: boolean;
  centralStatutes: boolean;
  constitution: boolean;
  commentaries: boolean;
  statuteScope: string;
  courtLevel: "supreme" | "high" | "both";
  dateFrom: string;
  dateTo: string;
  resultPreference: "relevant" | "latest" | "landmark";
}

interface Props {
  filters: ResearchScopeFilters;
  onChange: (updated: Partial<ResearchScopeFilters>) => void;
  onReset: () => void;
  className?: string;
}

export const ResearchScopeSidebar: React.FC<Props> = ({
  filters,
  onChange,
  onReset,
  className = "",
}) => {
  const toggleStatuteScope = () => {
    if (filters.statuteScope.includes("IPC")) {
      onChange({ statuteScope: "Bharatiya Nyaya Sanhita (BNS 2023)" });
    } else {
      onChange({ statuteScope: "Indian Penal Code (IPC)" });
    }
  };

  return (
    <aside
      className={`w-full lg:w-64 shrink-0 space-y-6 text-slate-950 font-sans ${className}`}
      aria-label="Research Scope Filters"
    >
      {/* Scope Header */}
      <div className="flex items-center justify-between pb-2.5 border-b-2 border-slate-300">
        <h2 className="text-base font-bold text-slate-950 tracking-tight">
          Research Scope
        </h2>
        <SlidersHorizontal className="h-4 w-4 text-slate-900 stroke-[2.5]" />
      </div>

      {/* Data Sources */}
      <div className="space-y-3">
        <label className="block text-xs font-black text-slate-950 uppercase tracking-wider">
          Data Sources
        </label>
        <div className="space-y-2.5 text-sm font-bold">
          <label className="flex items-center space-x-2.5 cursor-pointer hover:text-[#0f2c24] transition-colors">
            <input
              type="checkbox"
              checked={filters.scJudgments}
              onChange={(e) => onChange({ scJudgments: e.target.checked })}
              className="w-4 h-4 rounded text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Supreme Court Judgments</span>
          </label>

          <label className="flex items-center space-x-2.5 cursor-pointer hover:text-[#0f2c24] transition-colors">
            <input
              type="checkbox"
              checked={filters.hcJudgments}
              onChange={(e) => onChange({ hcJudgments: e.target.checked })}
              className="w-4 h-4 rounded text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">High Court Judgments</span>
          </label>

          <label className="flex items-center space-x-2.5 cursor-pointer hover:text-[#0f2c24] transition-colors">
            <input
              type="checkbox"
              checked={filters.centralStatutes}
              onChange={(e) => onChange({ centralStatutes: e.target.checked })}
              className="w-4 h-4 rounded text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Central Statutes (IPC, BNS, etc.)</span>
          </label>

          <label className="flex items-center space-x-2.5 cursor-pointer hover:text-[#0f2c24] transition-colors">
            <input
              type="checkbox"
              checked={filters.constitution}
              onChange={(e) => onChange({ constitution: e.target.checked })}
              className="w-4 h-4 rounded text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950 font-bold">Constitution of India</span>
          </label>

          <label className="flex items-center space-x-2.5 cursor-pointer hover:text-[#0f2c24] transition-colors">
            <input
              type="checkbox"
              checked={filters.commentaries}
              onChange={(e) => onChange({ commentaries: e.target.checked })}
              className="w-4 h-4 rounded text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950 font-bold">Commentaries &amp; Articles</span>
          </label>
        </div>
      </div>

      {/* Statute Scope */}
      <div className="space-y-2.5">
        <label className="block text-xs font-black text-slate-950 uppercase tracking-wider">
          Statute Scope
        </label>
        <select
          value={filters.statuteScope}
          onChange={(e) => onChange({ statuteScope: e.target.value })}
          className="w-full bg-white border-2 border-slate-300 rounded-xl px-3.5 py-2 text-sm font-bold text-slate-950 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-xs"
        >
          <option value="Indian Penal Code (IPC)">Indian Penal Code (IPC)</option>
          <option value="Bharatiya Nyaya Sanhita (BNS 2023)">Bharatiya Nyaya Sanhita (BNS 2023)</option>
          <option value="Code of Criminal Procedure (CrPC)">Code of Criminal Procedure (CrPC)</option>
          <option value="Bharatiya Nagarik Suraksha (BNSS 2023)">Bharatiya Nagarik Suraksha (BNSS)</option>
          <option value="All Indian Statutes">All Indian Statutes (Combined)</option>
        </select>

        <button
          type="button"
          onClick={toggleStatuteScope}
          className="w-full flex items-center justify-center space-x-2 py-2 px-3.5 rounded-xl bg-[#faeae1] hover:bg-[#f5ddcc] text-[#78350f] border-2 border-[#f3d3be] font-bold text-xs sm:text-sm transition-all hover:scale-[1.01] shadow-xs"
        >
          <ArrowRightLeft className="h-4 w-4 text-[#b45309] stroke-[2.5]" />
          <span>
            {filters.statuteScope.includes("IPC")
              ? "Switch to BNS (2023)"
              : "Switch to IPC (1860)"}
          </span>
        </button>
      </div>

      {/* Court Level */}
      <div className="space-y-2.5">
        <label className="block text-xs font-black text-slate-950 uppercase tracking-wider">
          Court Level
        </label>
        <div className="space-y-2 text-sm font-bold">
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="radio"
              name="courtLevel"
              checked={filters.courtLevel === "supreme"}
              onChange={() => onChange({ courtLevel: "supreme" })}
              className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Supreme Court</span>
          </label>
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="radio"
              name="courtLevel"
              checked={filters.courtLevel === "high"}
              onChange={() => onChange({ courtLevel: "high" })}
              className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">High Court</span>
          </label>
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="radio"
              name="courtLevel"
              checked={filters.courtLevel === "both"}
              onChange={() => onChange({ courtLevel: "both" })}
              className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Both</span>
          </label>
        </div>
      </div>

      {/* Date Range (Optional) */}
      <div className="space-y-2.5">
        <label className="block text-xs font-black text-slate-950 uppercase tracking-wider">
          Date Range (Optional)
        </label>
        <div className="grid grid-cols-2 gap-2">
          <div className="relative">
            <input
              type="text"
              placeholder="From"
              value={filters.dateFrom}
              onChange={(e) => onChange({ dateFrom: e.target.value })}
              className="w-full bg-white border-2 border-slate-300 rounded-xl pl-3 pr-8 py-2 text-sm font-bold text-slate-950 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-xs"
            />
            <Calendar className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-700 pointer-events-none stroke-[2.5]" />
          </div>
          <div className="relative">
            <input
              type="text"
              placeholder="To"
              value={filters.dateTo}
              onChange={(e) => onChange({ dateTo: e.target.value })}
              className="w-full bg-white border-2 border-slate-300 rounded-xl pl-3 pr-8 py-2 text-sm font-bold text-slate-950 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#0f2c24] shadow-xs"
            />
            <Calendar className="absolute right-2.5 top-2.5 h-4 w-4 text-slate-700 pointer-events-none stroke-[2.5]" />
          </div>
        </div>
      </div>

      {/* Result Preference */}
      <div className="space-y-2.5">
        <label className="block text-xs font-black text-slate-950 uppercase tracking-wider">
          Result Preference
        </label>
        <div className="space-y-2 text-sm font-bold">
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="radio"
              name="resultPref"
              checked={filters.resultPreference === "relevant"}
              onChange={() => onChange({ resultPreference: "relevant" })}
              className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Most Relevant</span>
          </label>
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="radio"
              name="resultPref"
              checked={filters.resultPreference === "latest"}
              onChange={() => onChange({ resultPreference: "latest" })}
              className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Latest First</span>
          </label>
          <label className="flex items-center space-x-2.5 cursor-pointer">
            <input
              type="radio"
              name="resultPref"
              checked={filters.resultPreference === "landmark"}
              onChange={() => onChange({ resultPreference: "landmark" })}
              className="w-4 h-4 text-[#0f2c24] focus:ring-[#0f2c24] border-slate-400 accent-[#0f2c24]"
            />
            <span className="text-slate-950">Landmark Judgments</span>
          </label>
        </div>
      </div>

      {/* Clear Filters Button */}
      <div className="pt-1">
        <button
          type="button"
          onClick={onReset}
          className="flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-[#faeae1] hover:bg-[#f5ddcc] text-[#78350f] text-xs font-bold border-2 border-[#f3d3be] transition-all hover:scale-105 shadow-xs"
        >
          <RotateCcw className="h-4 w-4 stroke-[2.5]" />
          <span>Clear Filters</span>
        </button>
      </div>
    </aside>
  );
};

export default ResearchScopeSidebar;
