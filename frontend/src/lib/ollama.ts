import type { OllamaMode } from "@/types/api";

export function getOllamaBaseUrl(mode: OllamaMode): string {
  return mode === "cloud" ? "https://ollama.com" : "http://localhost:11434";
}

export function formatOllamaMode(mode: OllamaMode): string {
  return mode === "cloud" ? "Ollama Cloud" : "Localhost";
}
