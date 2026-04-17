export type ProviderName = "openai" | "anthropic" | "gemini" | "ollama";

export type OllamaMode = "local" | "cloud";

export type DatasetOverview = {
  countries: number;
  zones: number;
  metrics: number;
  analyticalRows: number;
};

export type ProviderCredential = {
  provider: ProviderName;
  model: string;
  has_api_key: boolean;
  base_url: string | null;
};

export type ProvidersResponse = {
  supported: ProviderName[];
  defaultModels: Record<ProviderName, string>;
  saved: ProviderCredential[];
};

export type ProviderConfigPayload = {
  provider: ProviderName;
  model: string;
  api_key?: string;
  base_url?: string;
  preserve_existing_key?: boolean;
};

export type ChatRequest = {
  question: string;
  history_id?: string | null;
  provider: ProviderName | null;
  model: string | null;
  base_url: string | null;
  require_llm: boolean;
};

export type ReportMetadata = {
  type: "metadata";
  timestamp: string;
  insights_count: number;
  query_info?: {
    metrics_analyzed: string[];
    countries: string[];
    time_period: string;
    total_zones: number;
    total_rows: number;
    technical_query?: string;
  };
};

export type ReportChart = {
  type: "chart";
  chart: {
    type: string;
    title: string;
    data: Record<string, unknown>;
  };
};

export type ReportChunk = ReportMetadata | ReportChart | { type: "chunk"; content: string } | { type: "error"; error: string };

export type HistoryChunk = {
  type: "history";
  history_id: string;
};

export type ChatResponse = {
  answer: string;
  table: Record<string, unknown>[];
  columns: string[];
  suggestions: string[];
  metadata: Record<string, unknown>;
  query: string;
  history_id?: string;
};
