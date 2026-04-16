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
  provider: ProviderName | null;
  model: string | null;
  base_url: string | null;
  require_llm: boolean;
};

export type ChatResponse = {
  answer: string;
  table: Record<string, unknown>[];
  columns: string[];
  suggestions: string[];
  metadata: Record<string, unknown>;
};

export type ReportResponse = {
  markdown: string;
};
