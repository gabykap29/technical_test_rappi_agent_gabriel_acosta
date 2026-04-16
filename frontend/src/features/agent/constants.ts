import type { ProviderName } from "@/types/api";

export const QUICK_QUESTIONS = {
  Rankings: [
    "Cuales son las 5 zonas con mayor Lead Penetration esta semana?",
    "Cuales son las 5 zonas con menor Perfect Order esta semana?",
  ],
  Comparaciones: [
    "Compara Perfect Order entre zonas Wealthy y Non Wealthy en Mexico",
    "Cual es el promedio de Lead Penetration por pais?",
  ],
  Diagnostico: [
    "Que zonas tienen alto Lead Penetration pero bajo Perfect Order?",
    "Cuales zonas problematicas hay esta semana?",
  ],
  Tendencias: [
    "Muestra la evolucion de Gross Profit UE en Chapinero ultimas 8 semanas",
    "Cuales zonas crecen mas en ordenes en las ultimas 5 semanas?",
  ],
} as const;

export const PROVIDERS: ProviderName[] = [
  "openai",
  "anthropic",
  "gemini",
  "ollama",
];
