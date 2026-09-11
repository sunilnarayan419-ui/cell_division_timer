export interface CellBenchmark {
  id: string;
  name: string;
  organism: string;
  cell_type: string;
  passage_number: number;
  source_line: string;
  description: string;
}

export interface DivisionBenchmark {
  record_id: number;
  cell_id: string;
  experimental_batch: string;
  replicate: number;
  experimental_condition: string;
  medium: string;
  temperature_celsius: number;
  generation: number;
  division_start_time: string;
  division_end_time: string;
  division_duration_minutes: number;
  cell_cycle_duration_hours: number;
  growth_rate_per_hour: number;
  is_outlier: boolean;
  quality_flag: string;
}

export const BENCHMARK_CELLS: CellBenchmark[] = [
  {
    id: "CELL-SC-001",
    name: "S. cerevisiae BY4741 WT",
    organism: "Saccharomyces cerevisiae",
    cell_type: "Budding yeast",
    passage_number: 3,
    source_line: "ATCC 204508",
    description: "Standard haploid laboratory yeast strain for cell cycle control studies.",
  },
  {
    id: "CELL-EC-001",
    name: "E. coli K-12 MG1655",
    organism: "Escherichia coli",
    cell_type: "Rod-shaped bacterium",
    passage_number: 1,
    source_line: "ATCC 47076",
    description: "Wild-type prophage-free bacterial model for prokaryotic division timing.",
  },
  {
    id: "CELL-HELA-001",
    name: "HeLa CCL-2",
    organism: "Homo sapiens",
    cell_type: "Epithelial adenocarcinoma",
    passage_number: 14,
    source_line: "ATCC CCL-2",
    description: "Human immortal cell line used extensively for mitosis checkpoint analysis.",
  },
  {
    id: "CELL-NIH3T3-001",
    name: "NIH/3T3 Fibroblast",
    organism: "Mus musculus",
    cell_type: "Embryonic fibroblast",
    passage_number: 8,
    source_line: "ATCC CRL-1658",
    description: "Contact-inhibited murine fibroblast line for growth factor kinetic studies.",
  },
];
