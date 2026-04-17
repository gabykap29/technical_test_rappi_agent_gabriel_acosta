# Rappi Operations Intelligence

Sistema local para explorar metricas operacionales de Rappi con un agente
conversacional basado en LangGraph, providers LLM configurables y un generador
de insights ejecutivos.

## Alcance

- Bot conversacional con LangGraph para preguntas de filtrado, comparacion,
  tendencias, agregaciones, analisis multivariable e inferencias sobre
  crecimiento.
- Selector de provider LLM: OpenAI, Anthropic, Gemini u Ollama.
- Ollama soporta dos modos: local (`http://localhost:11434`) y cloud
  (`https://ollama.com` con token Bearer).
- Guardado local de API keys en SQLite cifrado con `cryptography` y Fernet.
- Memoria conversacional simple para reutilizar metrica, pais o zona reciente.
- Sugerencias proactivas para guiar al usuario no tecnico.
- Reporte automatico en Markdown con anomalias, tendencias,
  benchmarking, correlaciones y oportunidades.
- Interfaz web migrada a Next.js + React para preparar despliegue en Vercel.
- API Python local con FastAPI para exponer agente, credenciales y reportes.

## Setup

```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

Para la interfaz Next.js se necesita Node.js 20+:

```powershell
cd frontend
npm install
```

El proyecto detecta automaticamente el workbook `.xlsx` ubicado en la raiz. Si
se prefiere usar CSV, crear una carpeta `data/` con:

- `metrics_input.csv`
- `orders.csv`
- `metric_dictionary.csv` opcional

## Uso Web Next.js

Levantar backend Python:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```

Levantar frontend Next:

```powershell
cd frontend
npm run dev
```

Con Bun:

```powershell
cd frontend
bun run dev
```

Con Deno, si Bun presenta problemas:

```powershell
cd frontend
deno task dev
```

Build recomendado si Bun falla en Windows:

```powershell
cd frontend
deno task build
```

Abrir:

```text
http://localhost:3000
```

La app Next usa `RAPPI_API_BASE_URL` para apuntar al backend. Por defecto:

```text
http://localhost:8000
```

## Preguntas de demo

- Cuales son las 5 zonas con mayor Lead Penetration esta semana?
- Compara Perfect Order entre zonas Wealthy y Non Wealthy en Mexico
- Muestra la evolucion de Gross Profit UE en Chapinero ultimas 8 semanas
- Cual es el promedio de Lead Penetration por pais?
- Que zonas tienen alto Lead Penetration pero bajo Perfect Order?
- Cuales zonas crecen mas en ordenes en las ultimas 5 semanas?

## Verificacion

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m pytest
.\env\Scripts\ruff.exe check .
```

## Arquitectura LLM

El flujo principal usa LangGraph:

1. Nodo `plan`: el LLM interpreta la pregunta y genera un plan JSON.
2. Nodo `execute`: pandas ejecuta el analisis sobre el dataset.
3. Nodo `respond`: el LLM redacta la respuesta final usando solo la evidencia.

Los calculos numericos no los inventa el LLM. El modelo interpreta y redacta,
pero las tablas y metricas salen de herramientas pandas auditables.

## Arquitectura Frontend

La app Next esta en `frontend/` y sigue una separacion por capas:

- `src/app`: rutas Next, layout y API routes proxy.
- `src/features/agent`: caso de uso principal del agente y cliente API.
- `src/components`: componentes visuales reutilizables.
- `src/lib`: configuracion, HTTP client y helpers de Ollama.
- `src/types`: contratos TypeScript compartidos.

Para Vercel, el frontend se puede desplegar como proyecto Next. El backend
Python debe publicarse por separado o exponerse como servicio HTTP y configurar
`RAPPI_API_BASE_URL` en las variables de entorno de Vercel.

## Costo estimado

Depende del provider y modelo elegido. Ollama local no consume API paga. OpenAI,
Anthropic y Gemini consumen segun tokens de entrada/salida. Para una demo corta
con 5 a 10 preguntas y modelos livianos, el costo esperado suele ser bajo, pero
debe validarse contra el pricing vigente del provider elegido.
