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
- Reporte automatico en Markdown y HTML con anomalias, tendencias,
  benchmarking, correlaciones y oportunidades.
- Interfaz CLI y app Streamlit para demo local.

## Setup

```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
```

El proyecto detecta automaticamente el workbook `.xlsx` ubicado en la raiz. Si
se prefiere usar CSV, crear una carpeta `data/` con:

- `metrics_input.csv`
- `orders.csv`
- `metric_dictionary.csv` opcional

## Uso CLI

Guardar una API key cifrada:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli --save-key --provider openai --model gpt-4o-mini --api-key "TU_API_KEY"
```

Configurar Ollama local:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli --save-key --provider ollama --ollama-mode local --model llama3.1
```

Configurar Ollama Cloud:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli --save-key --provider ollama --ollama-mode cloud --model llama3.1 --api-key "TU_OLLAMA_TOKEN"
```

Pregunta unica:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli --provider openai --ask "Cuales son las 5 zonas con mayor Lead Penetration esta semana?"
```

Modo interactivo:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli
```

Generar reportes:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli --report
```

Los reportes se escriben en `reports/executive_report.md` y
`reports/executive_report.html`.

## Uso Streamlit

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\streamlit.exe run streamlit_app.py
```

En la sidebar:

1. Elegir provider: `openai`, `anthropic`, `gemini` u `ollama`.
2. Si el provider es `ollama`, elegir `Localhost` u `Ollama Cloud`.
3. Confirmar o cambiar el modelo.
4. Pegar API key si el provider la requiere. Ollama local no requiere key;
   Ollama Cloud si requiere token.
5. Click en `Save encrypted provider config`.
6. Mantener activo `Use LangGraph LLM agent`.

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

## Costo estimado

Depende del provider y modelo elegido. Ollama local no consume API paga. OpenAI,
Anthropic y Gemini consumen segun tokens de entrada/salida. Para una demo corta
con 5 a 10 preguntas y modelos livianos, el costo esperado suele ser bajo, pero
debe validarse contra el pricing vigente del provider elegido.
