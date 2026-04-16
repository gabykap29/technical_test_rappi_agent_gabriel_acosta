import { PYTHON_API_BASE_URL, REQUEST_TIMEOUT_MS } from "@/lib/api-config";

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
};

export async function requestPythonApi<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${PYTHON_API_BASE_URL}${path}`, {
      method: options.method ?? "GET",
      headers: {
        "Content-Type": "application/json",
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: controller.signal,
      cache: "no-store",
    });

    const payload = await response.json().catch(() => null);
    if (!response.ok) {
      const message =
        payload && typeof payload.detail === "string"
          ? payload.detail
          : `API request failed with status ${response.status}`;
      throw new Error(message);
    }
    return payload as T;
  } finally {
    clearTimeout(timeout);
  }
}
