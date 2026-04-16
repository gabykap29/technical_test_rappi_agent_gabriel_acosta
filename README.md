# Rappi Operations Intelligence

Sistema local para explorar metricas operacionales de Rappi con un agente
conversacional y un generador de insights ejecutivos.

## Alcance

- Bot conversacional para preguntas de filtrado, comparacion, tendencias,
  agregaciones, analisis multivariable e inferencias sobre crecimiento.
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

Pregunta unica:

```powershell
$env:PYTHONPATH = "src"
.\env\Scripts\python.exe -m rappi_intelligence.cli --ask "Cuales son las 5 zonas con mayor Lead Penetration esta semana?"
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

## Costo estimado

La solucion actual no usa APIs pagas ni LLM externo. El costo por sesion local
es `0 USD`, fuera del costo de infraestructura de la maquina donde se ejecuta.
