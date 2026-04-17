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

export type StreamHandler = (chunk: {
  type: "table" | "chunk" | "error";
  content?: string;
  table?: Record<string, unknown>[];
  columns?: string[];
  suggestions?: string[];
  query?: string;
  error?: string;
}) => void;

export function askAgentStream(
  payload: ChatRequest,
  onChunk: StreamHandler
): Promise<void> {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }
      if (!response.body) {
        throw new Error("Stream response body is empty");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split("\n\n");
        buffer = events.pop() ?? "";

        for (const event of events) {
          for (const line of event.split("\n")) {
            if (!line.startsWith("data: ")) {
              continue;
            }
            try {
              const data = JSON.parse(line.slice(6));
              onChunk(data);
            } catch {
              // Ignore invalid event payloads.
            }
          }
        }
      }

      resolve();
    } catch (error) {
      reject(error);
    }
  });
}

export function getExecutiveReport(): Promise<ReportResponse> {
  return request<ReportResponse>("/api/report", {
    method: "POST",
    body: JSON.stringify({}),
  });
}
