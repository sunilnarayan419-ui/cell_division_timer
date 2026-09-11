import React, { useState, useMemo } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  BarChart3,
  CheckCircle2,
  Clock,
  Code2,
  Cpu,
  Database,
  Dna,
  FileSpreadsheet,
  FileText,
  Filter,
  Flame,
  Layers,
  Microscope,
  Play,
  RefreshCw,
  Search,
  Server,
  ShieldCheck,
  Terminal,
  Zap,
} from "lucide-react";
import { BENCHMARK_CELLS, DivisionBenchmark } from "./data/synthetic_data";
import recordsData from "./data/synthetic_records.json";

const records: DivisionBenchmark[] = recordsData as DivisionBenchmark[];

export default function App() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "dataset" | "calculator" | "analytics" | "api" | "deployment"
  >("overview");

  // Dataset filter states
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCell, setSelectedCell] = useState("ALL");
  const [selectedBatch, setSelectedBatch] = useState("ALL");
  const [selectedCondition, setSelectedCondition] = useState("ALL");
  const [outlierFilter, setOutlierFilter] = useState<"ALL" | "CLEAN" | "OUTLIER">("ALL");

  // Interactive kinetics simulator states
  const [simOrganism, setSimOrganism] = useState("Saccharomyces cerevisiae");
  const [simStartMin, setSimStartMin] = useState(0);
  const [simEndMin, setSimEndMin] = useState(28);
  const [simCycleHours, setSimCycleHours] = useState(2.2);
  const [simTemperature, setSimTemperature] = useState(30.0);

  // API Versioning tab state
  const [apiVersionTab, setApiVersionTab] = useState<"v1" | "v2" | "headers">("v1");

  // Filtered dataset
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      const matchSearch =
        searchTerm === "" ||
        r.cell_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.experimental_condition.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.experimental_batch.toLowerCase().includes(searchTerm.toLowerCase()) ||
        r.quality_flag.toLowerCase().includes(searchTerm.toLowerCase());

      const matchCell = selectedCell === "ALL" || r.cell_id === selectedCell;
      const matchBatch = selectedBatch === "ALL" || r.experimental_batch === selectedBatch;
      const matchCondition = selectedCondition === "ALL" || r.experimental_condition === selectedCondition;
      const matchOutlier =
        outlierFilter === "ALL"
          ? true
          : outlierFilter === "CLEAN"
          ? !r.is_outlier
          : r.is_outlier;

      return matchSearch && matchCell && matchBatch && matchCondition && matchOutlier;
    });
  }, [searchTerm, selectedCell, selectedBatch, selectedCondition, outlierFilter]);

  // Derived kinetics calculation for simulator
  const simDuration = Math.max(0, simEndMin - simStartMin);
  const simGrowthRate = simCycleHours > 0 ? Math.log(2) / simCycleHours : 0;

  const simEvaluation = useMemo(() => {
    if (simDuration >= simCycleHours * 60) {
      return {
        isOutlier: true,
        flag: "SUSPECT_DIVISION_EXCEEDS_CYCLE",
        reason: "Active cytokinesis duration cannot equal or exceed entire cell-cycle doubling time.",
        severity: "critical",
      };
    }
    if (simTemperature < 10.0 || simTemperature > 48.0) {
      return {
        isOutlier: true,
        flag: "OUTLIER_TEMPERATURE_EXTREME",
        reason: `Incubation temperature (${simTemperature}°C) exceeds physiological cell viability thresholds.`,
        severity: "critical",
      };
    }
    // Species thresholds
    if (simOrganism.includes("cerevisiae") && simDuration > 60) {
      return {
        isOutlier: true,
        flag: "OUTLIER_DURATION_EXCESSIVE",
        reason: `Yeast mitotic duration (${simDuration} min) exceeds 2.5x standard baseline (typical 18-35 min). Possible spindle assembly arrest.`,
        severity: "warning",
      };
    }
    if (simOrganism.includes("coli") && simDuration > 45) {
      return {
        isOutlier: true,
        flag: "OUTLIER_DURATION_EXCESSIVE",
        reason: `Bacterial division (${simDuration} min) exceeds normal prokaryotic divisome timing (typical 12-25 min).`,
        severity: "warning",
      };
    }
    if (simDuration < 5.0) {
      return {
        isOutlier: true,
        flag: "OUTLIER_DURATION_SUBPHYSIOLOGICAL",
        reason: `Division duration (${simDuration} min) is biologically too brief for chromosome segregation.`,
        severity: "warning",
      };
    }
    return {
      isOutlier: false,
      flag: "PASS",
      reason: "All kinetic variables fall strictly within physiological reference parameters.",
      severity: "success",
    };
  }, [simOrganism, simDuration, simCycleHours, simTemperature]);

  // Overall analytics stats
  const totalObs = records.length;
  const outlierObs = records.filter((r) => r.is_outlier).length;
  const cleanObs = totalObs - outlierObs;

  const avgDivision =
    records.reduce((acc, r) => acc + r.division_duration_minutes, 0) / (totalObs || 1);
  const avgCycle =
    records.reduce((acc, r) => acc + r.cell_cycle_duration_hours, 0) / (totalObs || 1);
  const avgGrowth =
    records.reduce((acc, r) => acc + r.growth_rate_per_hour, 0) / (totalObs || 1);

  // Grouped by condition
  const conditionStats = useMemo(() => {
    const map: Record<string, { count: number; divSum: number; cycleSum: number; outliers: number }> = {};
    for (const r of records) {
      if (!map[r.experimental_condition]) {
        map[r.experimental_condition] = { count: 0, divSum: 0, cycleSum: 0, outliers: 0 };
      }
      map[r.experimental_condition].count += 1;
      map[r.experimental_condition].divSum += r.division_duration_minutes;
      map[r.experimental_condition].cycleSum += r.cell_cycle_duration_hours;
      if (r.is_outlier) map[r.experimental_condition].outliers += 1;
    }
    return Object.entries(map).map(([condition, val]) => ({
      condition,
      count: val.count,
      avgDiv: (val.divSum / val.count).toFixed(1),
      avgCycle: (val.cycleSum / val.count).toFixed(2),
      outliers: val.outliers,
    }));
  }, []);

  const handleDownloadZip = () => {
    const link = document.createElement("a");
    link.href = "/cell_division_timer_fastapi.zip";
    link.download = "cell_division_timer_fastapi.zip";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadCsv = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      encodeURIComponent(
        [
          "record_id,cell_id,experimental_batch,replicate,experimental_condition,medium,temperature_celsius,generation,division_start_time,division_end_time,division_duration_minutes,cell_cycle_duration_hours,growth_rate_per_hour,is_outlier,quality_flag",
          ...records.map(
            (r) =>
              `${r.record_id},${r.cell_id},${r.experimental_batch},${r.replicate},"${r.experimental_condition}","${r.medium}",${r.temperature_celsius},${r.generation},${r.division_start_time},${r.division_end_time},${r.division_duration_minutes},${r.cell_cycle_duration_hours},${r.growth_rate_per_hour},${r.is_outlier},${r.quality_flag}`
          ),
        ].join("\n")
      );
    const link = document.createElement("a");
    link.setAttribute("href", csvContent);
    link.setAttribute("download", "synthetic_cell_divisions_100.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans antialiased selection:bg-emerald-500/30 selection:text-emerald-300">
      {/* Top Header */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-sm shadow-emerald-950">
              <Dna className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-white">
                  Cell Division Timer
                </h1>
                <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  FastAPI v2.0
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Biotechnology & Life-Sciences Cell-Cycle Kinetics Platform
              </p>
            </div>
          </div>

          {/* Quick Metrics Bar & Action */}
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden lg:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
              <div className="flex items-center gap-1.5 text-slate-300">
                <Database className="w-3.5 h-3.5 text-blue-400" />
                <span>PostgreSQL / SQLite</span>
              </div>
              <span className="text-slate-700">|</span>
              <div className="flex items-center gap-1.5 text-slate-300">
                <Layers className="w-3.5 h-3.5 text-purple-400" />
                <span>Alembic Migrations</span>
              </div>
              <span className="text-slate-700">|</span>
              <div className="flex items-center gap-1.5 text-emerald-400">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>26/26 Pytest Tests</span>
              </div>
            </div>

            <button
              id="download-zip-btn"
              onClick={handleDownloadZip}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs sm:text-sm shadow-sm transition-colors cursor-pointer"
            >
              <ArrowDownToLine className="w-4 h-4" />
              <span>Download Project ZIP</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex overflow-x-auto gap-1 border-t border-slate-800/40 text-xs sm:text-sm">
          {[
            { id: "overview", label: "Architecture & Overview", icon: Layers },
            { id: "dataset", label: "100 Benchmark Records", icon: Database },
            { id: "calculator", label: "Kinetics & Outlier Simulator", icon: Cpu },
            { id: "analytics", label: "Analytics & Batch QC", icon: BarChart3 },
            { id: "api", label: "REST API Specification", icon: Code2 },
            { id: "deployment", label: "DevOps & Deployment", icon: Terminal },
          ].map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 px-4 py-2.5 border-b-2 font-medium whitespace-nowrap transition-colors cursor-pointer ${
                  isSelected
                    ? "border-emerald-400 text-emerald-300 bg-emerald-500/5"
                    : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* TAB 1: OVERVIEW & ARCHITECTURE */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Mission Hero Banner */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-950 border border-slate-800/80 relative overflow-hidden">
              <div className="relative z-10 max-w-3xl">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-3">
                  <Microscope className="w-3.5 h-3.5" />
                  Life-Sciences Informatics Infrastructure
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                  Quantitative Cell-Cycle & Division Kinetics Engine
                </h2>
                <p className="mt-2 text-sm sm:text-base text-slate-300 leading-relaxed">
                  Engineered to transform raw time-lapse microscopy observations into structured,
                  reproducible kinetic models. Supports high-throughput sample registration, automated
                  mitotic duration tracking, doubling rate (μ) derivation, and automated biological
                  quality control across experimental stress conditions.
                </p>
              </div>
            </div>

            {/* 4-Layer Architecture Diagram */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Layers className="w-4 h-4 text-emerald-400" />
                Separation of Concerns: Layered Architecture
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 relative">
                  <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center font-bold text-xs mb-3 border border-blue-500/20">
                    API
                  </div>
                  <h4 className="text-base font-semibold text-white">REST API Layer</h4>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    FastAPI router endpoints for <code className="text-blue-300">/cells</code>,{" "}
                    <code className="text-blue-300">/divisions</code>,{" "}
                    <code className="text-blue-300">/analytics</code>, and CSV streaming.
                    Enforces strict Pydantic V2 schemas and global exception handling.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 relative">
                  <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center font-bold text-xs mb-3 border border-emerald-500/20">
                    SRV
                  </div>
                  <h4 className="text-base font-semibold text-white">Service Layer</h4>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    Pure domain business logic: computes division duration (T_div),
                    specific growth rate (μ), and tags biological outliers against
                    reference organism ranges.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 relative">
                  <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center font-bold text-xs mb-3 border border-purple-500/20">
                    REP
                  </div>
                  <h4 className="text-base font-semibold text-white">Repository Layer</h4>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    Data-access abstraction over SQLAlchemy 2.0 ORM. Implements eager-loading
                    (<code className="text-purple-300">joinedload</code>) to eliminate N+1 queries,
                    composite filters, and pagination.
                  </p>
                </div>

                <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800 relative">
                  <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center font-bold text-xs mb-3 border border-amber-500/20">
                    DB
                  </div>
                  <h4 className="text-base font-semibold text-white">Database Layer</h4>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">
                    PostgreSQL 16 / SQLite managed by versioned Alembic migrations. Includes
                    foreign-key cascades, check constraints, and composite indices.
                  </p>
                </div>
              </div>
            </div>

            {/* Kinetic Formulas & Biological Baselines */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="flex items-center gap-2 text-emerald-400 text-sm font-semibold mb-2">
                  <Clock className="w-4 h-4" />
                  Active Division Duration
                </div>
                <div className="p-3 rounded-lg bg-slate-950 font-mono text-xs text-emerald-300 border border-slate-800 my-2">
                  T_div = (end_time - start_time) / 60 [min]
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Calculates elapsed duration between mitotic prophase initiation and complete
                  cytokinetic separation. Validates timestamp integrity (t_end &ge; t_start).
                </p>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="flex items-center gap-2 text-blue-400 text-sm font-semibold mb-2">
                  <Zap className="w-4 h-4" />
                  Specific Growth Rate (μ)
                </div>
                <div className="p-3 rounded-lg bg-slate-950 font-mono text-xs text-blue-300 border border-slate-800 my-2">
                  μ = ln(2) / cell_cycle_duration_hours [hr⁻¹]
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Derived from exponential proliferation kinetics (N(t) = N₀ · 2^(t/Td) = N₀ · e^(μt)).
                  Reflects substrate utilization efficiency.
                </p>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
                <div className="flex items-center gap-2 text-purple-400 text-sm font-semibold mb-2">
                  <ShieldCheck className="w-4 h-4" />
                  Quality Control Screening
                </div>
                <div className="p-3 rounded-lg bg-slate-950 font-mono text-xs text-purple-300 border border-slate-800 my-2">
                  outlier = T_div &ge; (60 &times; T_d) || Temp &notin; [10, 50]
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Flags biological anomalies such as mitotic spindle checkpoints, metaphase arrests,
                  severe temperature shock, or cell fragmentation.
                </p>
              </div>
            </div>

            {/* Registered Biological Cell Lines */}
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
              <h3 className="text-base font-semibold text-white mb-3 flex items-center gap-2">
                <Dna className="w-4 h-4 text-emerald-400" />
                Model Organisms Registered in the Benchmark Suite
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {BENCHMARK_CELLS.map((cell) => (
                  <div
                    key={cell.id}
                    className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-emerald-400 font-semibold">
                        {cell.id}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 font-medium">
                        P{cell.passage_number}
                      </span>
                    </div>
                    <div className="mt-2 text-sm font-semibold text-white">{cell.name}</div>
                    <div className="text-xs italic text-slate-400">{cell.organism}</div>
                    <div className="mt-2 text-[11px] text-slate-500 leading-tight">
                      {cell.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: DATASET EXPLORER (100 RECORDS) */}
        {activeTab === "dataset" && (
          <div className="space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Database className="w-5 h-5 text-emerald-400" />
                  Synthetic Benchmark Observations
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  100 scientifically plausible development records across 4 model organisms, 5 conditions, and 4 experimental batches.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <button
                  id="export-csv-records-btn"
                  onClick={handleDownloadCsv}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 border border-slate-700 transition-colors cursor-pointer"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Download CSV (100 Rows)</span>
                </button>
              </div>
            </div>

            {/* Filter Bar */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
                <input
                  id="dataset-search-input"
                  type="text"
                  placeholder="Search condition, batch, ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Cell Line */}
              <div>
                <select
                  id="filter-cell-select"
                  value={selectedCell}
                  onChange={(e) => setSelectedCell(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Cell Lines ({records.length})</option>
                  <option value="CELL-SC-001">S. cerevisiae (Yeast)</option>
                  <option value="CELL-EC-001">E. coli (Bacteria)</option>
                  <option value="CELL-HELA-001">HeLa (Human)</option>
                  <option value="CELL-NIH3T3-001">NIH/3T3 (Mouse)</option>
                </select>
              </div>

              {/* Batch */}
              <div>
                <select
                  id="filter-batch-select"
                  value={selectedBatch}
                  onChange={(e) => setSelectedBatch(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Batches</option>
                  <option value="BATCH-2024-Q1">BATCH-2024-Q1</option>
                  <option value="BATCH-2024-Q2">BATCH-2024-Q2</option>
                  <option value="BATCH-2024-Q3">BATCH-2024-Q3</option>
                  <option value="BATCH-2024-Q4">BATCH-2024-Q4</option>
                </select>
              </div>

              {/* Condition */}
              <div>
                <select
                  id="filter-condition-select"
                  value={selectedCondition}
                  onChange={(e) => setSelectedCondition(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Conditions</option>
                  <option value="Control (Standard Media)">Control</option>
                  <option value="Nutrient Depletion (0.1% Glucose)">Nutrient Depletion</option>
                  <option value="Thermal Stress (+5°C)">Thermal Stress</option>
                  <option value="Rapamycin Inhibition (10 nM)">Rapamycin (10 nM)</option>
                  <option value="Osmotic Stress (0.4M Sorbitol)">Osmotic Stress</option>
                </select>
              </div>

              {/* Outlier Filter */}
              <div>
                <select
                  id="filter-outlier-select"
                  value={outlierFilter}
                  onChange={(e) => setOutlierFilter(e.target.value as any)}
                  className="w-full px-3 py-1.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="ALL">All Quality Flags</option>
                  <option value="CLEAN">Clean Only ({cleanObs})</option>
                  <option value="OUTLIER">Flagged Outliers ({outlierObs})</option>
                </select>
              </div>
            </div>

            {/* Results count */}
            <div className="flex items-center justify-between text-xs text-slate-400 px-1">
              <span>
                Showing <strong className="text-emerald-400">{filteredRecords.length}</strong> of{" "}
                {records.length} observations
              </span>
              {filteredRecords.length < records.length && (
                <button
                  onClick={() => {
                    setSearchTerm("");
                    setSelectedCell("ALL");
                    setSelectedBatch("ALL");
                    setSelectedCondition("ALL");
                    setOutlierFilter("ALL");
                  }}
                  className="text-emerald-400 hover:underline cursor-pointer"
                >
                  Reset filters
                </button>
              )}
            </div>

            {/* High-density Table */}
            <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/60">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                  <tr>
                    <th className="px-3.5 py-3">#</th>
                    <th className="px-3.5 py-3">Sample ID</th>
                    <th className="px-3.5 py-3">Batch & Rep</th>
                    <th className="px-3.5 py-3">Condition</th>
                    <th className="px-3.5 py-3">Temp</th>
                    <th className="px-3.5 py-3">Gen</th>
                    <th className="px-3.5 py-3">Div Duration</th>
                    <th className="px-3.5 py-3">Cycle (Td)</th>
                    <th className="px-3.5 py-3">Growth Rate (μ)</th>
                    <th className="px-3.5 py-3">Quality Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {filteredRecords.map((r) => (
                    <tr
                      key={r.record_id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        r.is_outlier ? "bg-amber-500/5" : ""
                      }`}
                    >
                      <td className="px-3.5 py-2.5 text-slate-500">{r.record_id}</td>
                      <td className="px-3.5 py-2.5 font-medium text-emerald-400">{r.cell_id}</td>
                      <td className="px-3.5 py-2.5 text-slate-400">
                        {r.experimental_batch} <span className="text-slate-600">r{r.replicate}</span>
                      </td>
                      <td className="px-3.5 py-2.5 font-sans text-slate-200">
                        {r.experimental_condition}
                      </td>
                      <td className="px-3.5 py-2.5 text-slate-300">{r.temperature_celsius}°C</td>
                      <td className="px-3.5 py-2.5 text-slate-400">G{r.generation}</td>
                      <td className="px-3.5 py-2.5 font-semibold text-white">
                        {r.division_duration_minutes.toFixed(1)} m
                      </td>
                      <td className="px-3.5 py-2.5 text-slate-300">
                        {r.cell_cycle_duration_hours.toFixed(2)} h
                      </td>
                      <td className="px-3.5 py-2.5 text-blue-400 font-semibold">
                        {r.growth_rate_per_hour.toFixed(3)} h⁻¹
                      </td>
                      <td className="px-3.5 py-2.5 font-sans">
                        {r.is_outlier ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/15 text-amber-300 border border-amber-500/30">
                            <AlertTriangle className="w-3 h-3" />
                            {r.quality_flag}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 className="w-3 h-3" />
                            PASS
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: KINETICS & OUTLIER SIMULATOR */}
        {activeTab === "calculator" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Cpu className="w-5 h-5 text-emerald-400" />
                Interactive Kinetics Calculator & Outlier Simulator
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Real-time validation engine mimicking the exact backend logic executed in{" "}
                <code className="text-emerald-300">app.utils.biology</code>. Test formulas,
                perturbation limits, and automated quality control flags.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Input Controls */}
              <div className="lg:col-span-7 p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                  Observation Parameters
                </h3>

                {/* Organism Selector */}
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5">
                    Target Biological Organism
                  </label>
                  <select
                    id="sim-organism-select"
                    value={simOrganism}
                    onChange={(e) => setSimOrganism(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="Saccharomyces cerevisiae">Saccharomyces cerevisiae (Budding Yeast)</option>
                    <option value="Escherichia coli">Escherichia coli (Gram-negative Bacterium)</option>
                    <option value="Homo sapiens (HeLa)">Homo sapiens (HeLa Epithelial)</option>
                    <option value="Mus musculus (NIH/3T3)">Mus musculus (NIH/3T3 Fibroblast)</option>
                  </select>
                </div>

                {/* Mitotic Timestamps (Duration) */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Prophase / Start (min)
                    </label>
                    <input
                      id="sim-start-min"
                      type="number"
                      value={simStartMin}
                      onChange={(e) => setSimStartMin(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1.5">
                      Cytokinesis / End (min)
                    </label>
                    <input
                      id="sim-end-min"
                      type="number"
                      value={simEndMin}
                      onChange={(e) => setSimEndMin(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white font-mono focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                </div>

                {/* Cell Cycle Duration */}
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-xs font-medium text-slate-300">
                      Total Cell-Cycle / Doubling Time ($T_d$ in hours)
                    </label>
                    <span className="font-mono text-xs text-blue-400 font-semibold">
                      {simCycleHours} hours
                    </span>
                  </div>
                  <input
                    id="sim-cycle-slider"
                    type="range"
                    min="0.2"
                    max="40"
                    step="0.1"
                    value={simCycleHours}
                    onChange={(e) => setSimCycleHours(Number(e.target.value))}
                    className="w-full accent-blue-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                    <span>Fast doubling (0.2h ~ E. coli)</span>
                    <span>Intermediate (2h ~ Yeast)</span>
                    <span>Slow (24h ~ Human)</span>
                  </div>
                </div>

                {/* Temperature */}
                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-xs font-medium text-slate-300">
                      Incubator Temperature (°C)
                    </label>
                    <span className="font-mono text-xs text-amber-400 font-semibold">
                      {simTemperature}°C
                    </span>
                  </div>
                  <input
                    id="sim-temp-slider"
                    type="range"
                    min="5"
                    max="60"
                    step="0.5"
                    value={simTemperature}
                    onChange={(e) => setSimTemperature(Number(e.target.value))}
                    className="w-full accent-amber-500 cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                    <span>Cold (5°C)</span>
                    <span>Physiological (30-37°C)</span>
                    <span>Heat Shock (45°C+)</span>
                  </div>
                </div>

                {/* Quick Presets */}
                <div className="pt-2 border-t border-slate-800/80">
                  <span className="text-[11px] text-slate-400 block mb-2 font-medium">
                    Load Stress & Anomaly Scenarios:
                  </span>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => {
                        setSimOrganism("Saccharomyces cerevisiae");
                        setSimStartMin(0);
                        setSimEndMin(25);
                        setSimCycleHours(2.1);
                        setSimTemperature(30.0);
                      }}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 transition-colors"
                    >
                      Healthy Yeast WT
                    </button>
                    <button
                      onClick={() => {
                        setSimOrganism("Saccharomyces cerevisiae");
                        setSimStartMin(0);
                        setSimEndMin(130); // Excessive
                        setSimCycleHours(2.5);
                        setSimTemperature(30.0);
                      }}
                      className="px-2.5 py-1 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 text-xs transition-colors"
                    >
                      Metaphase Arrest (+4.5x)
                    </button>
                    <button
                      onClick={() => {
                        setSimOrganism("Escherichia coli");
                        setSimStartMin(0);
                        setSimEndMin(20);
                        setSimCycleHours(0.8);
                        setSimTemperature(52.0); // Severe heat
                      }}
                      className="px-2.5 py-1 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30 text-xs transition-colors"
                    >
                      Thermal Shock (52°C)
                    </button>
                  </div>
                </div>
              </div>

              {/* Dynamic Live Result Cards */}
              <div className="lg:col-span-5 space-y-4">
                {/* Calculated Metrics */}
                <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
                    Derived Kinetics Output
                  </h3>

                  <div className="space-y-3 font-mono">
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                      <span className="text-xs text-slate-400">Active Division (T_div)</span>
                      <span className="text-base font-bold text-emerald-400">
                        {simDuration.toFixed(1)} min
                      </span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                      <span className="text-xs text-slate-400">Growth Rate (μ = ln(2)/Td)</span>
                      <span className="text-base font-bold text-blue-400">
                        {simGrowthRate.toFixed(4)} hr⁻¹
                      </span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                      <span className="text-xs text-slate-400">Division / Cycle Fraction</span>
                      <span className="text-base font-bold text-purple-400">
                        {((simDuration / (simCycleHours * 60)) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Outlier & Quality Flag Decision */}
                <div
                  className={`p-6 rounded-2xl border ${
                    simEvaluation.isOutlier
                      ? "bg-amber-950/20 border-amber-500/40"
                      : "bg-emerald-950/20 border-emerald-500/40"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {simEvaluation.isOutlier ? (
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                    ) : (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    )}
                    <h4 className="text-sm font-bold text-white">
                      Quality Control Status: {simEvaluation.flag}
                    </h4>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed mt-2">
                    {simEvaluation.reason}
                  </p>
                  <div className="mt-4 pt-3 border-t border-slate-800/80 flex justify-between text-[11px] text-slate-400">
                    <span>Validation Engine</span>
                    <span className="font-mono text-emerald-400">evaluate_biological_metrics()</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: ANALYTICS & BATCH QC */}
        {activeTab === "analytics" && (
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-emerald-400" />
                Scientific Analytics & Kinetic Profiling
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Real-time descriptive distributions and batch quality control aggregates corresponding to{" "}
                <code className="text-emerald-300">GET /api/v1/analytics/*</code>.
              </p>
            </div>

            {/* Overarching KPIs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Total Observations
                </span>
                <div className="mt-2 text-3xl font-bold text-white font-mono">{totalObs}</div>
                <div className="mt-1 text-xs text-slate-500">Across 4 cell lines & 4 batches</div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Mean Division Duration
                </span>
                <div className="mt-2 text-3xl font-bold text-emerald-400 font-mono">
                  {avgDivision.toFixed(1)} <span className="text-sm font-normal text-slate-400">min</span>
                </div>
                <div className="mt-1 text-xs text-slate-500">Across all 100 observations</div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Mean Specific Growth Rate
                </span>
                <div className="mt-2 text-3xl font-bold text-blue-400 font-mono">
                  {avgGrowth.toFixed(3)} <span className="text-sm font-normal text-slate-400">hr⁻¹</span>
                </div>
                <div className="mt-1 text-xs text-slate-500">Average doubling constant</div>
              </div>

              <div className="p-5 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">
                  Biological Outlier Rate
                </span>
                <div className="mt-2 text-3xl font-bold text-amber-400 font-mono">
                  {((outlierObs / (totalObs || 1)) * 100).toFixed(1)}%
                </div>
                <div className="mt-1 text-xs text-amber-500/80">{outlierObs} flagged observations</div>
              </div>
            </div>

            {/* Kinetics Stratified by Condition */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-emerald-400" />
                Division Kinetics Stratified by Perturbation Condition
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 uppercase font-semibold">
                    <tr>
                      <th className="px-4 py-2.5">Experimental Condition</th>
                      <th className="px-4 py-2.5">Observations</th>
                      <th className="px-4 py-2.5">Mean Div Duration</th>
                      <th className="px-4 py-2.5">Mean Cycle (Td)</th>
                      <th className="px-4 py-2.5">Outliers</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {conditionStats.map((cs) => (
                      <tr key={cs.condition} className="hover:bg-slate-800/30">
                        <td className="px-4 py-3 font-sans text-white font-medium">
                          {cs.condition}
                        </td>
                        <td className="px-4 py-3 text-slate-300">{cs.count}</td>
                        <td className="px-4 py-3 text-emerald-400 font-semibold">{cs.avgDiv} min</td>
                        <td className="px-4 py-3 text-blue-400">{cs.avgCycle} hr</td>
                        <td className="px-4 py-3">
                          {cs.outliers > 0 ? (
                            <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/20 text-[10px]">
                              {cs.outliers} flagged
                            </span>
                          ) : (
                            <span className="text-emerald-400 text-[11px]">0 (100% clean)</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Batch Quality Control */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-purple-400" />
                Batch-Level Quality Control Aggregates
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {["BATCH-2024-Q1", "BATCH-2024-Q2", "BATCH-2024-Q3", "BATCH-2024-Q4"].map((b) => {
                  const bRecords = records.filter((r) => r.experimental_batch === b);
                  const bOutliers = bRecords.filter((r) => r.is_outlier).length;
                  const bRate = ((bOutliers / (bRecords.length || 1)) * 100).toFixed(1);
                  return (
                    <div key={b} className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                      <div className="font-mono text-xs text-purple-400 font-bold">{b}</div>
                      <div className="mt-2 flex justify-between text-xs text-slate-300">
                        <span>Observations:</span>
                        <strong className="text-white font-mono">{bRecords.length}</strong>
                      </div>
                      <div className="mt-1 flex justify-between text-xs text-slate-300">
                        <span>Outlier Rejections:</span>
                        <span
                          className={`font-mono font-bold ${
                            bOutliers > 0 ? "text-amber-400" : "text-emerald-400"
                          }`}
                        >
                          {bOutliers} ({bRate}%)
                        </span>
                      </div>
                      <div className="mt-3 pt-2 border-t border-slate-800/80 flex justify-between text-[11px] text-slate-500">
                        <span>Replicates:</span>
                        <span>r1, r2, r3</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: REST API SPECIFICATION */}
        {activeTab === "api" && (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <Code2 className="w-5 h-5 text-emerald-400" />
                  FastAPI Versioned API & Header Routing Explorer
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Explore production v1 stable endpoints, preview v2-beta kinetics, and test header-based version negotiation.
                </p>
              </div>

              {/* Version Selector Tabs */}
              <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs self-start">
                <button
                  onClick={() => setApiVersionTab("v1")}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    apiVersionTab === "v1"
                      ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-semibold"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  v1 (Stable)
                </button>
                <button
                  onClick={() => setApiVersionTab("v2")}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    apiVersionTab === "v2"
                      ? "bg-purple-500/20 text-purple-400 border border-purple-500/30 font-semibold"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  v2 (Beta Preview)
                </button>
                <button
                  onClick={() => setApiVersionTab("headers")}
                  className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                    apiVersionTab === "headers"
                      ? "bg-blue-500/20 text-blue-400 border border-blue-500/30 font-semibold"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  Header-Based Routing
                </button>
              </div>
            </div>

            {/* Version Overview Banner */}
            {apiVersionTab === "v1" && (
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-slate-300 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  <span className="font-semibold text-emerald-300">API v1 Stable:</span> Production contract for cell lineage registration, single observation kinetics, and bulk CSV streaming.
                </div>
                <code className="text-slate-400 font-mono text-[11px]">Lifecycle: production (stable)</code>
              </div>
            )}

            {apiVersionTab === "v2" && (
              <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 text-xs text-slate-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                  <span className="font-semibold text-purple-300">API v2 Beta:</span> Enhanced with mitotic subphase resolution, high-throughput batch analysis, and Arrhenius Q10 temperature modeling.
                </div>
                <code className="text-purple-300 font-mono text-[11px] bg-purple-950/60 px-2 py-1 rounded border border-purple-800">
                  X-API-Warning: 299 Experimental Preview
                </code>
              </div>
            )}

            {apiVersionTab === "headers" && (
              <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs text-slate-300 space-y-2">
                <div className="flex items-center gap-2 font-semibold text-blue-300">
                  <Cpu className="w-4 h-4" />
                  ASGI APIVersioningMiddleware Mechanics
                </div>
                <p className="text-slate-400 leading-relaxed text-[11px]">
                  Clients can call unversioned endpoints (e.g. <code className="text-blue-300">/api/divisions</code>) with the <code className="text-white font-mono">X-API-Version: 2</code> header, <code className="text-white font-mono">Accept: application/vnd.celldivision.v2+json</code>, or <code className="text-white font-mono">?api-version=2</code>. The middleware intercepts the request, rewrites the ASGI scope path to <code className="text-emerald-300">/api/v2/...</code>, injects <code className="text-white font-mono">X-API-Version: v2-beta</code> and <code className="text-white font-mono">X-API-Lifecycle: beta</code> response headers, and gracefully rejects invalid version identifiers with HTTP 400.
                </p>
              </div>
            )}

            {/* Tab Endpoints */}
            <div className="space-y-4">
              {(apiVersionTab === "v1"
                ? [
                    {
                      method: "GET",
                      path: "/health",
                      tag: "System",
                      desc: "Returns operational status and active DB ping latency",
                      curl: "curl -X GET http://localhost:8000/health",
                      sampleResp: `{\n  "status": "healthy",\n  "app_name": "Cell Division Timer API",\n  "version": "1.0.0",\n  "database": {\n    "connected": true,\n    "latency_ms": 0.45\n  }\n}`,
                    },
                    {
                      method: "POST",
                      path: "/api/v1/divisions",
                      tag: "Divisions",
                      desc: "Create division observation; computes division duration and growth rate automatically",
                      curl: `curl -X POST http://localhost:8000/api/v1/divisions \\\n  -H "Content-Type: application/json" \\\n  -d '{\n    "cell_id": "CELL-SC-001",\n    "experimental_batch": "BATCH-2024-Q1",\n    "replicate": 1,\n    "experimental_condition": "Control",\n    "medium": "YPD Broth",\n    "temperature_celsius": 30.0,\n    "generation": 1,\n    "division_start_time": "2024-03-01T10:00:00Z",\n    "division_end_time": "2024-03-01T10:28:30Z",\n    "cell_cycle_duration_hours": 2.1\n  }'`,
                      sampleResp: `{\n  "id": 1,\n  "cell_id": "CELL-SC-001",\n  "organism": "Saccharomyces cerevisiae",\n  "division_duration_minutes": 28.5,\n  "cell_cycle_duration_hours": 2.1,\n  "growth_rate": 0.3301,\n  "is_outlier": false,\n  "quality_flag": "PASS"\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/v1/divisions?organism=cerevisiae&is_outlier=false&sort_by=growth_rate&sort_order=desc",
                      tag: "Divisions",
                      desc: "Multi-dimensional query filtering with pagination and sorting",
                      curl: 'curl -X GET "http://localhost:8000/api/v1/divisions?organism=cerevisiae&is_outlier=false&page=1&page_size=20"',
                      sampleResp: `{\n  "items": [...],\n  "total": 23,\n  "page": 1,\n  "page_size": 20,\n  "total_pages": 2\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/v1/analytics/summary",
                      tag: "Analytics",
                      desc: "Descriptive statistics across all observations (mean, median, std_dev, cv_percent)",
                      curl: "curl -X GET http://localhost:8000/api/v1/analytics/summary",
                      sampleResp: `{\n  "total_observations": 100,\n  "clean_observation_count": 96,\n  "division_duration_minutes": {\n    "mean": 51.4,\n    "median": 42.1,\n    "std_dev": 28.3,\n    "cv_percent": 55.0\n  }\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/v1/data/export/csv",
                      tag: "Data Transfer",
                      desc: "Streams entire dataset as downloadable CSV",
                      curl: "curl -X GET http://localhost:8000/api/v1/data/export/csv -o export.csv",
                      sampleResp: `record_id,cell_id,organism,batch...\n1,CELL-SC-001,Saccharomyces cerevisiae...`,
                    },
                  ]
                : apiVersionTab === "v2"
                ? [
                    {
                      method: "GET",
                      path: "/api/v2/beta/status",
                      tag: "v2 Lifecycle",
                      desc: "Query active v2-beta capabilities, changelog, and backward-compatibility matrix",
                      curl: "curl -X GET http://localhost:8000/api/v2/beta/status",
                      sampleResp: `{\n  "version": "2.0.0-beta.1",\n  "status": "beta",\n  "lifecycle": "active-development",\n  "features": [\n    "Mitotic sub-phase temporal breakdown",\n    "Batch kinetic analysis profiler",\n    "Arrhenius Q10 temperature modeling"\n  ]\n}`,
                    },
                    {
                      method: "POST",
                      path: "/api/v2/divisions/batch-analyze",
                      tag: "v2 High-Throughput",
                      desc: "Batch kinetic analysis across observations; derives population distributions & Q10 coefficient",
                      curl: `curl -X POST http://localhost:8000/api/v2/divisions/batch-analyze \\\n  -H "Content-Type: application/json" \\\n  -d '{\n    "batch_name": "BATCH-2024-V2-EXP1",\n    "observations": [\n      {"cell_id": "CELL-SC-001", "temperature_celsius": 30.0, "division_duration_minutes": 25.0, "cell_cycle_duration_hours": 2.0, "experimental_condition": "Control"},\n      {"cell_id": "CELL-SC-001", "temperature_celsius": 35.0, "division_duration_minutes": 32.0, "cell_cycle_duration_hours": 1.7, "experimental_condition": "Thermal Shift"}\n    ]\n  }'`,
                      sampleResp: `{\n  "batch_name": "BATCH-2024-V2-EXP1",\n  "total_processed": 2,\n  "mean_division_minutes": 28.5,\n  "mean_growth_rate_per_hour": 0.3771,\n  "outlier_count": 0,\n  "arrhenius_q10_estimate": 1.95\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/v2/analytics/predictive-kinetics?ref_temp=30.0&elevated_temp=35.0",
                      tag: "v2 Thermodynamics",
                      desc: "Computes Arrhenius activation energy (Ea) and biological Q10 thermal sensitivity index",
                      curl: 'curl -X GET "http://localhost:8000/api/v2/analytics/predictive-kinetics?ref_temp=30.0&elevated_temp=35.0"',
                      sampleResp: `{\n  "reference_temperature_celsius": 30.0,\n  "elevated_temperature_celsius": 35.0,\n  "q10_temperature_coefficient": 1.62,\n  "activation_energy_kj_mol": 37.4,\n  "biological_interpretation": "Cell population exhibits a Q10 coefficient of 1.62. Normal enzyme-catalyzed mitotic progression."\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/v2/analytics/mitotic-phases",
                      tag: "v2 Kinetics",
                      desc: "Quantifies global population distribution across prophase, metaphase, anaphase, and telophase",
                      curl: "curl -X GET http://localhost:8000/api/v2/analytics/mitotic-phases",
                      sampleResp: `{\n  "mean_prophase_minutes": 15.8,\n  "mean_metaphase_minutes": 13.5,\n  "mean_anaphase_minutes": 6.8,\n  "mean_telophase_minutes": 9.0,\n  "mean_total_mitosis_minutes": 45.1\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/v2/divisions",
                      tag: "v2 Divisions",
                      desc: "Paginated division records enriched with mitotic subphase breakdown and SAC arrest scoring",
                      curl: "curl -X GET http://localhost:8000/api/v2/divisions?page=1&page_size=20",
                      sampleResp: `{\n  "items": [\n    {\n      "id": 1,\n      "cell_id": "CELL-SC-001",\n      "division_duration_minutes": 28.5,\n      "mitotic_subphases": {\n        "prophase_minutes": 10.0,\n        "metaphase_minutes": 8.5,\n        "anaphase_minutes": 4.3,\n        "telophase_minutes": 5.7\n      },\n      "checkpoint_delay_index": 1.0,\n      "arrest_probability_score": 0.05\n    }\n  ],\n  "total": 100\n}`,
                    },
                  ]
                : [
                    {
                      method: "GET",
                      path: "/api/divisions (Unversioned URL)",
                      tag: "Header Routing",
                      desc: "Route directly to v2 Beta by supplying X-API-Version header",
                      curl: 'curl -i -X GET http://localhost:8000/api/divisions \\\n  -H "X-API-Version: 2"',
                      sampleResp: `HTTP/1.1 200 OK\nx-api-version: v2-beta\nx-api-lifecycle: beta\nx-api-warning: 299 - "v2-beta is an active preview and subject to experimental evolution."\nvary: X-API-Version, Accept\n\n{\n  "items": [...v2 records with subphase telemetry...]\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/divisions (Vendor MIME)",
                      tag: "Content Negotiation",
                      desc: "Route to v2 Beta using standard REST vendor Accept header",
                      curl: 'curl -i -X GET http://localhost:8000/api/divisions \\\n  -H "Accept: application/vnd.celldivision.v2+json"',
                      sampleResp: `HTTP/1.1 200 OK\nx-api-version: v2-beta\nx-api-lifecycle: beta\nvary: X-API-Version, Accept\n\n{\n  "items": [...]\n}`,
                    },
                    {
                      method: "GET",
                      path: "/api/divisions (Invalid Version)",
                      tag: "Validation Rejection",
                      desc: "Requesting an unsupported version safely returns 400 Bad Request with supported directory",
                      curl: 'curl -i -X GET http://localhost:8000/api/divisions \\\n  -H "X-API-Version: 99"',
                      sampleResp: `HTTP/1.1 400 Bad Request\nx-api-supported-versions: v1, v2-beta\n\n{\n  "detail": "Unsupported API version '99'. Supported versions: v1, v2-beta.",\n  "code": "UNSUPPORTED_API_VERSION",\n  "requested_version": "99",\n  "supported_versions": ["v1", "v2-beta"],\n  "default_version": "v1"\n}`,
                    },
                  ]
              ).map((ep, idx) => (
                <div
                  key={idx}
                  className="p-5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`px-2.5 py-1 rounded text-xs font-bold font-mono ${
                          ep.method === "POST"
                            ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                            : "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                        }`}
                      >
                        {ep.method}
                      </span>
                      <code className="text-sm font-semibold text-white font-mono">
                        {ep.path}
                      </code>
                    </div>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded font-medium ${
                        ep.tag.includes("v2")
                          ? "bg-purple-900/40 text-purple-300 border border-purple-800/40"
                          : ep.tag.includes("Header")
                          ? "bg-blue-900/40 text-blue-300 border border-blue-800/40"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {ep.tag}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300">{ep.desc}</p>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 pt-2">
                    <div>
                      <div className="text-[11px] text-slate-400 mb-1 font-semibold">cURL Request:</div>
                      <pre className="p-3 rounded-lg bg-slate-950 text-slate-300 font-mono text-[11px] overflow-x-auto border border-slate-800/80">
                        {ep.curl}
                      </pre>
                    </div>
                    <div>
                      <div className="text-[11px] text-slate-400 mb-1 font-semibold">Sample Response (JSON / HTTP):</div>
                      <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono text-[11px] overflow-x-auto border border-slate-800/80">
                        {ep.sampleResp}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 6: DEVOPS & DEPLOYMENT */}
        {activeTab === "deployment" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Terminal className="w-5 h-5 text-emerald-400" />
                DevOps, Testing, and Deployment Instructions
              </h2>
              <p className="text-xs text-slate-400 mt-1">
                Instructions for running migrations, executing pytest suites, and launching multi-container Docker Compose.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Local Dev & Testing */}
              <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                  <Play className="w-4 h-4 text-emerald-400" />
                  Local Development & Pytest
                </h3>
                <div className="space-y-3 text-xs text-slate-300">
                  <p>1. Install requirements in virtual environment:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono border border-slate-800">
                    pip install -r requirements.txt
                  </pre>

                  <p>2. Execute database migrations with Alembic:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono border border-slate-800">
                    alembic upgrade head
                  </pre>

                  <p>3. Seed 100 synthetic benchmark records:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono border border-slate-800">
                    python scripts/seed.py
                  </pre>

                  <p>4. Run the complete Pytest verification suite (26 tests):</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono border border-slate-800">
                    pytest -v
                  </pre>

                  <p>5. Launch local FastAPI Uvicorn dev server:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-emerald-300 font-mono border border-slate-800">
                    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
                  </pre>
                </div>
              </div>

              {/* Docker Compose */}
              <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
                <h3 className="text-sm font-semibold text-white uppercase tracking-wider flex items-center gap-2">
                  <Server className="w-4 h-4 text-blue-400" />
                  Docker Compose Orchestration (PostgreSQL)
                </h3>
                <div className="space-y-3 text-xs text-slate-300">
                  <p>Launch PostgreSQL 16 database and FastAPI container stack:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-blue-300 font-mono border border-slate-800">
                    docker compose up --build -d
                  </pre>

                  <p>Execute migrations within container:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-blue-300 font-mono border border-slate-800">
                    docker compose exec api alembic upgrade head
                  </pre>

                  <p>Seed synthetic benchmark records inside container:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-blue-300 font-mono border border-slate-800">
                    docker compose exec api python scripts/seed.py
                  </pre>

                  <p>Access live Swagger documentation:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-blue-300 font-mono border border-slate-800">
                    open http://localhost:8000/docs
                  </pre>

                  <p>Stop containers:</p>
                  <pre className="p-3 rounded-lg bg-slate-950 text-blue-300 font-mono border border-slate-800">
                    docker compose down
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
