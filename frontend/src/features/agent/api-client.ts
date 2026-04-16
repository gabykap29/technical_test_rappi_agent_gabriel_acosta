import type {
  ChatRequest,
  ChatResponse,
  DatasetOverview,
  ProviderConfigPayload,
  ProvidersResponse,
  ReportResponse,
} from "@/types/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      payload && typeof payload.error === "string"
        ? payload.error
        : `Request failed with status ${response.status}`;
    throw new Error(message);
  }
  return payload as T;
}

export function getDatasetOverview(): Promise<DatasetOverview> {
  return request<DatasetOverview>("/api/dataset/overview");
}

export function getProviders(): Promise<ProvidersResponse> {
  return request<ProvidersResponse>("/api/providers");
}

export function saveProvider(payload: ProviderConfigPayload): Promise<void> {
  return request<void>("/api/providers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function askAgent(payload: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getExecutiveReport(): Promise<ReportResponse> {
  return request<ReportResponse>("/api/report", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
