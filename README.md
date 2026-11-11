# Demo Expense Tracker Agent

Agente de inteligencia artificial en Python diseñado para auditar gastos personales, detectar patrones de consumo y emitir recomendaciones accionables.

Este proyecto corresponde al **Día 2** de una serie de sesiones prácticas sobre el impacto de los agentes de IA durante campañas de alto consumo como Black Friday:

- **Día 1**: Creación de un cazador de ofertas automatizado mediante _vibecoding_ con Claude.
- **Día 2 (este repositorio)**: Construcción desde cero de un agente financiero en Python que analiza el impacto real de esas compras en las finanzas personales.
- **Día 3**: Mesa redonda y conversación sobre la era agéntica.

---

## Principios Técnicos y Pedagógicos

| Área                | Decisión                                                                                                                              |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------------------ |
| **Nivel de código** | Python claro, directo y fácil de seguir para perfiles con bases iniciales del lenguaje, manteniendo buenas prácticas de arquitectura. |
| **Persistencia**    | **TinyDB** (`data/db.json`) como única base de datos local con escritura idempotente (sin duplicados al reimportar).                  |
| **Entorno**         | Contenedores **Docker** multi-etapa (`dev` con `debugpy` expuesto en `:5678`, `test` y `prod`).                                       |
| **Testing**         | **TDD** con `unittest` (librería estándar de Python), cobertura objetivo **>80%** y foco en casos borde y seguridad.                  |
| **Frontend**        | Dashboard estilo v0 (React + Vite + Tailwind) gestionado con **pnpm**, con **Dark Mode por defecto** y selector a Light Mode.         |

---

## Estrategia de Modelos por Caso de Uso (OpenRouter)

Cada agente utiliza el tipo de modelo adecuado según la carga cognitiva de su tarea (**System One vs System Two**).

**Jev** (`typesafe/jev-1.14` / `~typesafe/jev-latest`) es un modelo de **decisión tipada** de TypeSafe, disponible en OpenRouter con la misma API key. No genera texto libre: recibe un `state` + preguntas tipadas y devuelve respuestas con probabilidades y confianza. Se llama por la [Decisions API](https://openrouter.ai/docs/guides/community/jev) (`POST /api/alpha/decisions`) o por la System One API. Primitivas útiles en esta demo:

| Primitiva  | Pregunta                           | Uso en el proyecto                                 |
| :--------- | :--------------------------------- | :------------------------------------------------- |
| **Choice** | ¿Cuál de estas opciones?           | Fase 1: asignar categoría a un movimiento          |
| **Score**  | ¿Dónde cae en una escala ordenada? | Fase 3: nivel de necesidad 1–5 (`NECESSITY_SCALE`) |
| **Noul**   | ¿Se cumple esta condición?         | Opcional: validar umbrales / casos ambiguos        |

| Fase / Agente                        | Rol Cognitivo                                  | Tipo de Modelo           | Modelo propuesto (OpenRouter)                          | Justificación                                                                                                                      |
| :----------------------------------- | :--------------------------------------------- | :----------------------- | :----------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------- |
| **Fase 1: Ingesta y Categorización** | **System One** (clasificación rápida y tipada) | Decision model (Jev)     | `typesafe/jev-1.14` — primitiva **Choice**             | Etiqueta categorías fijas sin parsear prosa. Fallback chat: `google/gemini-2.5-flash` si hace falta demo conversacional.           |
| **Fase 3: Evaluador de Necesidad**   | **System One** (juicio acotado a escala)       | Decision model (Jev)     | `typesafe/jev-1.14` — primitiva **Score**              | Escala ordenada 1–5 alineada con `NECESSITY_SCALE`; el código usa el nivel tipado y la UI expande etiqueta/descripción.            |
| **Fase 4: Analista Financiero**      | **System Two** (razonamiento + prosa)          | LLM razonador / Frontier | `deepseek/deepseek-r1` / `anthropic/claude-3.7-sonnet` | Cruza fechas, importes y niveles para inferir anomalías y redactar recomendaciones. Jev no sirve aquí: no genera informe en texto. |

---

## Arquitectura del Proyecto

La estructura se inicializa desde la Fase 0 orientada al producto final. Los agentes viven como módulos independientes que pueden ejecutarse manualmente por consola (`python -m src.agents.<agente>`) e importarse desde la API.

```text
demo-expense-tracker-agent/
├── docker/
│   ├── Dockerfile.backend       # Multi-stage: dev (con debugpy :5678), test, prod
│   └── Dockerfile.frontend      # Node + pnpm (dev, build, prod)
├── docker-compose.yml           # Orquestación de entornos (dev, test, prod)
├── data/                        # WORKDIR confinado para las tools de archivos
│   ├── expenses_log.csv        # Seed Junio - Noviembre
│   └── db.json                  # Almacenamiento local TinyDB
├── src/
│   ├── main.py                  # Aplicación FastAPI (activa desde Fase 0)
│   ├── config.py                # Variables de entorno, WORKDIR y NECESSITY_SCALE
│   ├── db.py                    # Operaciones TinyDB con control de unicidad
│   ├── llm.py                   # Cliente chat OpenRouter (Agent Loop / Fase 4)
│   ├── decisions.py             # Cliente Decisions API (Jev Choice / Score)
│   ├── agent.py                 # Clase Agent base (Loop -> Tools -> Guardrails)
│   ├── tools.py                 # Tools de lectura de CSV y consultas a TinyDB
│   └── agents/
│       ├── ingester.py          # Fase 1: Lee CSV, categoriza con Jev Choice y persiste
│       ├── evaluator.py         # Fase 3: Evalúa necesidad con Jev Score (escala 1-5)
│       └── analyst.py          # Fase 4: Detecta patrones, excesos y sugiere acciones
├── tests/                       # Suite TDD con unittest (>80% coverage)
└── frontend/                    # Fase 2: Dashboard UI (pnpm, Dark/Light mode)
```

---

## Plan de Implementación por Fases

### Fase 0: Entorno Docker, Esqueleto FastAPI y Documento Seed

1. **Infraestructura Docker y Depuración**:
   - Configuración de `Dockerfile.backend`, `Dockerfile.frontend` y `docker-compose.yml` para entornos de desarrollo, pruebas y producción.
   - Integración de `debugpy` en el contenedor de desarrollo para depuración directa desde el editor.
   - Convención de trazas en consola mediante `print('variable_name', variable_name)`.
2. **Esqueleto inicial de FastAPI (`src/main.py`)**:
   - Creación del punto de entrada HTTP desde el inicio para mantener la estructura final del proyecto estable mientras se desarrollan los agentes por separado.
3. **Documento `data/expenses_log.csv`**:
   - **Volumen**: ~20-30 movimientos mensuales durante 6 meses (junio a noviembre).
   - **Estructura**: `date,concept,amount`. El tipo de movimiento se determina por el signo del importe: positivo (`+`) para ingresos y negativo (`-`) para egresos.
   - **Distribución mensual base (junio - octubre)**:
     - Ingreso mensual fijo: `+1350.00 €`
     - Alquiler de habitación: `-700.00 €`
     - Teléfono e internet: `-60.00 €`
     - Comida / supermercado: `~ -150.00 €` (con variación mensual de `-10 €` a `+20 €`)
     - Transporte: `-50.00 €`
     - Ocio y restaurantes: entre `-150.00 €` y `-250.00 €`
     - Compras puntuales ocasionales de ropa o electrónica menor.
   - **Anomalía de noviembre (sin etiquetas explícitas)**:
     - Durante la última semana de noviembre se concentran varios cargos adicionales en tiendas de tecnología y ropa que consumen el margen del mes y parte del ahorro acumulado en los meses previos.
     - **Restricción clave**: Ningún concepto incluye las palabras _"Black Friday"_ ni _"Oferta"_; el agente analista debe inferirlo por las fechas y la naturaleza del gasto.

---

### Fase 1: Agente Básico en Python (`src/llm.py`, `src/agent.py`, `src/agents/ingester.py`)

Desarrollo progresivo en 4 bloques para mostrar en vivo la evolución arquitectónica de un agente:

1. **Conexión con OpenRouter y Agent Loop (`src/llm.py`, `src/agent.py`)**:
   - Cliente ligero conectado a OpenRouter.
   - Clase `Agent` con memoria conversacional (`self.messages`) y ciclo base de interacción.
2. **Creación de Tools (`src/tools.py`)**:
   - Tool de lectura de archivos CSV para extraer los movimientos y presentarlos al modelo.
3. **Incorporación de Guardrails (TDD)**:
   - **Confinamiento de directorio (`WORKDIR = /data`)**: Validación estricta de rutas resueltas. La suite de tests verifica intentos de _Path Traversal_ incluyendo construcciones como `WORKDIR + '../'`, `../../etc/passwd` y rutas absolutas externas.
   - **Control de ejecución**: Límite máximo de iteraciones del bucle (`max_iterations`) y límite de llamadas a tools por turno (`max_tool_calls`).
4. **Persistencia Idempotente en TinyDB (`src/db.py`)**:
   - Categorización con **Jev** (`typesafe/jev-1.14`) vía Decisions API y primitiva **Choice** sobre un conjunto cerrado de categorías (`Vivienda`, `Servicios`, `Alimentación`, `Transporte`, `Ocio`, `Compras`, `Ingresos`, etc.).
   - Generación de clave unívoca determinista por movimiento para garantizar que múltiples ejecuciones de importación no dupliquen registros en TinyDB.

---

### Fase 2: API en FastAPI y Dashboard (`src/main.py`, `frontend/`)

1. **Endpoints en FastAPI**:
   - Importación de la capa de datos y agentes construidos en la Fase 1.
   - Endpoints para listar movimientos categorizados y obtener métricas agregadas (porcentajes por categoría y promedio mensual de los últimos meses).
2. **Dashboard Frontend (base v0)**:
   - Interfaz construida con React, Vite, Tailwind CSS y gestionada con `pnpm`.
   - Tema oscuro (**Dark Mode**) activo por defecto con conmutador a modo claro (**Light Mode**).
   - Visualización de porcentajes de gasto por categoría, comparativa del promedio mensual frente al pico de noviembre y listado detallado de transacciones.
   - Verificación obligatoria del empaquetado mediante `pnpm build`.

---

### Fase 3: Agente Evaluador de Movimientos (`src/agents/evaluator.py`)

1. **Escala Determinista en Código (`src/config.py`)**:
   - Definición de una estructura de datos centralizada con los 5 niveles de necesidad (desde `1: Indispensable` hasta `5: Innecesario`), incluyendo etiqueta, descripción detallada y metadatos visuales.
   - Esta estructura se inyecta dinámicamente en el prompt del agente y se reutiliza en la API/Frontend para expandir la información de cada etiqueta en la interfaz.
2. **Flujo de Evaluación (Jev — primitiva Score)**:
   - El evaluador lee los egresos en TinyDB, envía a Jev el estado del movimiento + la escala ordenada `NECESSITY_SCALE` y recibe un nivel tipado `1..5` (con probabilidad y confianza).
   - Actualiza cada registro con `necessity_level`. La UI/API expanden la etiqueta y la descripción a partir del diccionario en código (Jev no genera texto explicativo).

---

### Fase 4: Agente de Análisis y Sugerencias (`src/agents/analyst.py`)

1. **Tool de Lectura Analítica**:
   - Extracción de todos los movimientos desde TinyDB incluyendo fecha, importe, categoría y nivel de necesidad asignado en la Fase 3.
2. **Diagnóstico con Modelo Razonador (System 2)**:
   - Generación de un informe estructurado en tres bloques:
     - **Patrones de consumo identificados**: Comportamiento habitual de gasto y capacidad de ahorro entre junio y octubre.
     - **Casos que exceden los patrones**: Detección de la ráfaga de compras prescindibles/innecesarias en la última semana de noviembre y cálculo del impacto sobre el ahorro acumulado de meses anteriores.
     - **Acciones sugeridas**: Medidas concretas de control presupuestario para campañas de descuentos y límites por categoría.
