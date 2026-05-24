# Data Hub — Project Development Brief
> Reto #6 SAPIENCIA 2026 · Empresa: **Softline S.A.** · Equipo: **DataCore Solutions** (Grupo 1)
> Integrantes: David Arteaga · Edwin Molina · Andrea Cifuentes
> Generado para Claude Code · 21 de mayo de 2026 · Demo final: lunes 25/05/2026, 13:00

---

## 0. Cómo usar este documento

Eres Claude Code. Este `.md` es la fuente de verdad del proyecto.

1. Léelo de principio a fin **antes** de generar cualquier código.
2. Si tienes acceso al MCP de Stitch (`mcp__Stitch__*`), úsalo para leer el archivo de diseño cuyo URL está en la sección 10. Genera el frontend **fiel al diseño**, no improvises layouts.
3. Si tienes acceso a Bash, levanta el entorno y corre los tests al final de cada hito.
4. Marca cada criterio de aceptación de la sección 12 conforme avances. No declares el proyecto terminado hasta que todos estén ✓.
5. Si dudas entre dos opciones, escoge la más simple y deja un `TODO:` claro en el código.

---

## 1. Contexto del reto

Softline S.A. opera un **Observatorio TIC** para el sector de Tecnologías de la Información en Colombia. Hoy el equipo técnico debe consolidar manualmente información empresarial pública de múltiples fuentes (RUES, Cámara de Comercio, Superintendencia de Sociedades, DIAN, DANE), todas en formatos distintos (CSV, Excel, PDF, tableros web). El proceso es lento, frágil, y los mismos datos suelen reportarse diferente entre fuentes.

**Reto:** construir un DataHub que automatice la ingesta multifuente, normalice los datos a un modelo común, y exponga una API REST con un score de confiabilidad explícito por dato.

**Confirmaciones importantes**
- Llave única confirmada: **NIT** (= RUT).
- Llave secundaria: **códigos CIIU** para filtrar el sector TI (6201, 6202, 6209…).
- Cobertura ideal: **10 años de histórico** por indicador.
- La mayoría de fuentes **no exponen API**: se requiere **web scraping**.
- El **score de confiabilidad es el diferenciador** exigido por la empresa.

---

## 2. Insumos previos (entregables académicos hechos)

| Sesión | Entregable | Archivos |
|---|---|---|
| S5 | Problem Statement + Árbol de problemas | `Grupo1-Sesion5_*.docx` |
| S6 | Lienzo VP + Mapa de Encaje + Enunciado refinado | `Sesion6_*.docx` |
| S7 (P1) | Paper prototype: 5 pantallas (P1–P5) | `Sesion7_Paper_Prototype_p1.docx` |
| S7 (P2) | Customer Journey Map del equipo técnico de Softline | `Sesion7_Journey_Map_y_Service_Blueprint_p2.docx` |
| S7 — bonus | Mock funcional con Mockoon (7 endpoints, 25 respuestas) | `prototipo_mockoon/datacore-hub-mock.json` |
| S8 | Service Blueprint (FigJam) + pantalla hero del momento de la verdad (v0) | (en curso) |

**Problem Statement (S5):**
La falta de un pipeline automatizado obliga al equipo del Observatorio TIC a normalizar fuentes manualmente, agotando su capacidad operativa. Esto retrasa nuevas integraciones y compromete gravemente la fiabilidad de la plataforma.

**Propuesta de valor (S6):**
Para el equipo del Observatorio TIC de Softline, DataCore Hub es la plataforma automatizada de ingesta y normalización con score de confiabilidad, sin limpieza manual.

**Hipótesis crítica (S8):**
El equipo técnico de Softline, al ver el desglose del score sin guía previa, entiende cómo opera el servicio y declara confiar en el dato sin tener que validar manualmente otra fuente.

---

## 3. Stack técnico (decisiones tomadas, no negociar sin justificar)

**Backend:**
- Python 3.11+
- FastAPI (Swagger automático en `/docs`)
- SQLAlchemy 2 + SQLite (suficiente para MVP)
- Pydantic v2
- Scraping: `requests` + `BeautifulSoup`; `Playwright` solo si una fuente exige JS
- PDF/Excel: `pdfplumber`, `openpyxl`, `pandas`
- Tests: `pytest`

**Frontend:**
- React 18 + Vite + TypeScript
- Tailwind CSS + shadcn/ui (Radix por debajo)
- Routing: `react-router-dom`
- HTTP: `fetch` nativo o `axios`
- Iconos: `lucide-react`
- Charts (para vista histórica): `recharts`
- Tests: `vitest` + `@testing-library/react`

**Deploy:**
- Frontend: Vercel (URL `vercel.app` público, sin login).
- Backend MVP: Render free tier o Railway (también sirve `localhost` para la demo si el deploy falla).

**Conexión Frontend → Backend:** variable `VITE_API_URL` apuntando a `http://localhost:8000/api/v1` en dev y al backend desplegado en prod.

---

## 4. Arquitectura objetivo

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                     │
│  Búsqueda → Detalle → Score → Histórico → API Explorer →    │
│  Bitácora                                                    │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTPS (CORS habilitado)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    API REST (FastAPI)                        │
│  /api/v1/empresas        /api/v1/fuentes                     │
│  /api/v1/empresas/{nit}  /api/v1/indicadores                 │
│  /api/v1/empresas/{nit}/score                                │
│  /api/v1/empresas/{nit}/historico                            │
│  /api/v1/ingesta/{fuente}    /api/v1/bitacora                │
└────┬─────────────────┬──────────────────┬───────────────────┘
     │                 │                  │
     ▼                 ▼                  ▼
┌──────────┐    ┌────────────┐    ┌────────────────┐
│ Score    │    │ Normalizer │    │   Scrapers     │
│ engine   │    │ (modelo    │    │  RUES, CC,     │
│          │    │  común)    │    │  Supersoc,…    │
└────┬─────┘    └─────┬──────┘    └─────┬──────────┘
     │                │                  │
     └────────────────▼──────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │   SQLite      │
              │  (modelo      │
              │   común)      │
              └───────────────┘
```

---

## 5. Modelo de datos (SQLAlchemy)

| Tabla | Columnas | Notas |
|---|---|---|
| `empresas` | `nit` (PK), `razon_social`, `ciiu_principal`, `ciiu_secundarios` (JSON), `fecha_constitucion`, `estado` | Llave primaria por NIT (string con guión: "900111111-1") |
| `fuentes` | `id`, `nombre`, `url_base`, `tipo` (api/scraping/file), `tier` (float 0–1), `ultima_ingesta` | Seed con 5 fuentes: ver tabla en sección 8 |
| `indicadores` | `id`, `codigo` (ej: "num_empleados"), `descripcion`, `unidad` | Seed con 3 indicadores: empleados, ingresos, activos |
| `periodos` | `id`, `anio`, `trimestre` (nullable) | |
| `territorios` | `id`, `codigo_dane`, `nombre`, `tipo` (departamento/municipio) | Opcional para MVP |
| `valores` | `id`, `nit` FK, `indicador_id` FK, `territorio_id` FK nullable, `periodo_id` FK, `fuente_id` FK, `valor` (string), `valor_numerico` (float nullable), `score` (float 0–1), `fecha_captura` | El "hecho" del modelo común |
| `bitacora_ingesta` | `id`, `fuente_id` FK, `fecha`, `registros_ingestados`, `registros_rechazados`, `estado` (ok/warn/error), `mensaje` | Auditoría de ingesta |

---

## 6. Endpoints requeridos

Todos bajo prefijo `/api/v1`. Las respuestas deben mantener la forma del mock Mockoon en `prototipo_mockoon/datacore-hub-mock.json` (úsalo como contrato de referencia).

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/health` | Healthcheck (status + version + uptime) |
| GET | `/empresas?ciiu={code}&page={n}&size={s}` | Búsqueda paginada filtrada por CIIU |
| GET | `/empresas/{nit}` | Detalle consolidado por NIT (con indicadores y score global) |
| GET | `/empresas/{nit}/score?indicador={codigo}` | Desglose del score con comparación entre fuentes |
| GET | `/empresas/{nit}/historico?indicador={codigo}` | Serie temporal 2015–2024 |
| GET | `/indicadores` | Catálogo de indicadores |
| GET | `/fuentes` | Catálogo de fuentes con tier |
| POST | `/ingesta/{fuente_nombre}` | Dispara una ingesta (usa mock_scraper por defecto en MVP) |
| GET | `/bitacora?limit={n}` | Últimas N entradas de bitácora |

Documentación Swagger automática debe quedar disponible en `/docs`.

---

## 7. Fórmula del Score de Confiabilidad

```
score_final = 0.3 · completitud + 0.3 · actualidad + 0.4 · tier_fuente
```

- **completitud** ∈ [0, 1]: fracción de campos esperados no nulos del registro.
- **actualidad** ∈ [0, 1]: `max(0, 1 - (años_desde_dato / 10))`. Datos de hace más de 10 años → 0.
- **tier_fuente** ∈ [0, 1]: viene de la tabla `fuentes`.

Implementar también `explain(score)` que devuelve el desglose paso a paso (lo consume `/empresas/{nit}/score`).

---

## 8. Datos placeholder (seed)

**Fuentes (con tier confirmado en la reunión del 19/05):**

| Nombre | Tier | Tipo | URL base |
|---|---|---|---|
| Superintendencia de Sociedades | 0.95 | scraping | https://www.supersociedades.gov.co |
| DIAN | 0.95 | scraping | https://www.dian.gov.co |
| RUES | 0.90 | scraping | https://www.rues.org.co |
| Cámara de Comercio | 0.85 | scraping | https://www.ccmedellin.com.co |
| DANE | 0.70 | file | https://www.dane.gov.co |

**Indicadores:**

| Código | Descripción | Unidad |
|---|---|---|
| `num_empleados` | Número de empleados | personas |
| `ingresos_anuales` | Ingresos operacionales anuales | COP |
| `activos_totales` | Activos totales | COP |

**Empresas ficticias (5):**

| NIT | Razón social | CIIU | Score global esperado |
|---|---|---|---|
| 900111111-1 | Empresa A S.A.S. | 6201 | ~0.92 |
| 900222222-2 | Empresa B S.A.S. | 6201 | ~0.85 |
| 900333333-3 | Empresa C Ltda.  | 6202 | ~0.78 |
| 900444444-4 | Empresa D S.A.   | 6209 | ~0.71 |
| 900555555-5 | Empresa E S.A.S. | 6201 | ~0.66 |

---

## 9. Frontend — Pantallas requeridas

5 pantallas conectadas (cumple Punto 7.2 del entregable 8):

1. **`/`** — Búsqueda inicial: input NIT + select CIIU + botón Consultar.
2. **`/empresas/:nit`** — Detalle consolidado: header con razón social + NIT + score global en círculo grande + 3 cards de indicadores.
3. **`/empresas/:nit/score/:indicador`** — Desglose del score: fórmula visible, 3 mini-cards de factores, tabla comparativa por fuente, alert de consenso. **(Pantalla hero / momento de la verdad)**.
4. **`/api-explorer`** — Swagger embebido o redirect a `/docs` del backend.
5. **`/bitacora`** — Tabla operativa con estado por fuente, semáforo, botón "Reintentar" en filas con error.

Layout común: sidebar izquierdo con 3 ítems (Búsqueda, API Explorer, Bitácora) + header superior con logo "DataCore Hub · Observatorio TIC".

---

## 10. Integración con Google Stitch (MCP)

El diseño se construye en Google Stitch (no Figma). El MCP de Stitch se conecta vía HTTP con autenticación por API key de Google Cloud.

**Setup del MCP en Claude Code (correr una sola vez por máquina del equipo):**

```bash
# 1) Exporta la API key en una variable de entorno local (no la pegues en archivos)
export STITCH_API_KEY="<TU_API_KEY_AQUI>"

# 2) Agrega el MCP a Claude Code
claude mcp add stitch \
  --transport http \
  --header "X-Goog-Api-Key: $STITCH_API_KEY" \
  https://stitch.googleapis.com/mcp

# 3) Verifica que quedó conectado
claude mcp list
```

⚠ **Seguridad — no negociar:**
- La API key NO va en este archivo ni en ningún archivo del repo.
- Crea `.env` en la raíz con `STITCH_API_KEY=...` y agrega `.env` al `.gitignore`.
- Si la key se filtra accidentalmente (commit por error, pegada en chat, screenshot), revócala inmediatamente en `console.cloud.google.com` y emite una nueva.

**ID o URL del proyecto Stitch:** `claude mcp add stitch \
  --transport http \
  --header "X-Goog-Api-Key: <TU_API_KEY_AQUI>" \
  https://stitch.googleapis.com/mcp`

> ⚠ La key real va en `STITCH_API_KEY` (variable de entorno local). NUNCA en este archivo.

**Cómo usar el MCP de Stitch (Claude Code):**

Al iniciar la sesión, inspecciona los tools disponibles que empiezan con `mcp__stitch__*` y mapéalos al flujo siguiente. Como Stitch es un producto reciente, los nombres exactos de las tools pueden variar; usa el más parecido en cada paso:

1. **Inventario del proyecto** — obtén todos los frames/pantallas y sus IDs. Busca una tool tipo `list_designs`, `get_project`, `list_frames` o equivalente.
2. **Detalle de cada pantalla** — por cada frame, obtén la estructura de componentes, jerarquía, posiciones y tamaños. Busca `get_design`, `get_frame`, `get_design_context` o similar.
3. **Design tokens globales** — extrae colores, tipografías y espaciados y mapéalos al `tailwind.config.ts`. Busca `get_tokens`, `get_variables`, `get_design_system`.
4. **Render visual** — si quedan dudas, pide el PNG del frame. Busca `get_screenshot`, `export_frame`, `render` o equivalente.
5. **Código exportado** — si Stitch expone código (React/HTML) directamente, úsalo como referencia pero reescríbelo con la convención del proyecto (React + Vite + Tailwind + shadcn/ui).

**Si el MCP no conecta — troubleshooting:**

| Error | Causa probable | Acción |
|---|---|---|
| `401 Unauthorized` | API key inválida o no exportada | `echo $STITCH_API_KEY` debe devolver la key; regenerar en Google Cloud Console si fue revocada |
| `403 Forbidden` | API key sin permisos sobre Stitch | Habilitar la API de Stitch en el mismo proyecto de Google Cloud que emitió la key |
| `Connection refused` o timeout | Firewall corporativo bloquea `*.googleapis.com` | Probar en red personal o configurar proxy |
| `MCP server not found` tras `add` | Versión vieja de Claude Code | `npm i -g @anthropic-ai/claude-code` y reiniciar la sesión |
| Tools no aparecen en `/mcp` | Conectado pero sin tools expuestas | `claude mcp list` para verificar status; si dice connected sin tools, revisa scopes de la key |

Si después de ~10 min de troubleshooting el MCP sigue sin responder, hay plan B: en Stitch usa **"Export to Figma"** o **"Export code"** y pega el resultado en `/frontend/design/`. Si tampoco eso funciona, **detén el frontend** y sigue con backend; avisa al equipo (David, Edwin, Andrea) por el canal del proyecto.

---

## 11. Estructura de carpetas objetivo

```
DataCoreHub_MVP/
├── PROJECT_BRIEF.md                  ← este archivo
├── prototipo_mockoon/                ← contrato de referencia (NO modificar)
│   ├── datacore-hub-mock.json
│   └── README.md
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── main.py                   ← FastAPI app + CORS
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── db.py                 ← SQLAlchemy models
│   │   │   └── schemas.py            ← Pydantic schemas (response)
│   │   ├── routers/
│   │   │   ├── empresas.py
│   │   │   ├── indicadores.py
│   │   │   ├── fuentes.py
│   │   │   ├── ingesta.py
│   │   │   └── bitacora.py
│   │   ├── services/
│   │   │   ├── score.py
│   │   │   └── normalizer.py
│   │   ├── scrapers/
│   │   │   ├── base.py
│   │   │   ├── rues.py               ← placeholder con NotImplementedError
│   │   │   └── mock_scraper.py       ← Wizard-of-Oz desde data/raw/sample_empresas.csv
│   │   └── etl/
│   │       └── pipeline.py
│   ├── data/
│   │   ├── raw/
│   │   │   └── sample_empresas.csv   ← seed para mock_scraper
│   │   └── processed/
│   ├── scripts/
│   │   ├── init_db.py
│   │   └── ingest_sample.py
│   └── tests/
│       ├── test_score.py
│       └── test_api.py
├── frontend/
│   ├── README.md
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                   ← Router
│   │   ├── lib/
│   │   │   ├── api.ts                ← fetch helpers
│   │   │   └── utils.ts              ← cn() de shadcn
│   │   ├── components/
│   │   │   ├── ui/                   ← shadcn primitives (Button, Card, Table, …)
│   │   │   ├── Sidebar.tsx
│   │   │   └── Header.tsx
│   │   └── pages/
│   │       ├── Home.tsx              ← /
│   │       ├── EmpresaDetalle.tsx    ← /empresas/:nit
│   │       ├── ScoreDesglose.tsx     ← /empresas/:nit/score/:indicador
│   │       ├── ApiExplorer.tsx       ← /api-explorer
│   │       └── Bitacora.tsx          ← /bitacora
│   └── tests/
└── README.md                         ← cómo levantar todo
```

---

## 12. Acceptance Criteria (Puntos 6.3 y 7 del entregable 8)

**Verificación humana (6.3):**
- [ ] El equipo puede levantar el proyecto en su máquina siguiendo el README sin ayuda externa.
- [ ] No hay datos personales reales en el repo ni en la DB seed.
- [ ] Cualquier asset generado por IA tiene propósito funcional en el flujo (no decorativo).
- [ ] Cualquier integrante del equipo puede explicar cómo funciona cada módulo del backend y del frontend.

**Checklist final (7):**
- [ ] El URL del frontend en Vercel abre desde Chrome y Safari sin login.
- [ ] Hay 5 pantallas conectadas con navegación real (≥ 3 mínimo, cumple sobrado).
- [ ] El prototipo refleja el Problem Statement (S5) y la Propuesta de Valor (S6).
- [ ] La hipótesis crítica (sección 2) se puede validar el 25/05 con la empresa formuladora.
- [ ] Las herramientas IA están documentadas en este `.md` (sección 13) y hay ≥ 3 prompts clave registrados.
- [ ] El producto es "suficiente para validar", no "perfecto" — Lean Startup.
- [ ] Probado desde celular y computador antes de la demo.

---

## 13. Herramientas IA usadas y prompts clave

| Herramienta | Para qué | Ajuste humano |
|---|---|---|
| Claude Code | Generación del backend + frontend a partir de este brief | Revisión por el equipo de cada PR, ajuste de detalles visuales, validación de tests |
| Figma MCP | Lectura del diseño Figma para que el código sea fiel al mockup | Curaduría manual del diseño en Figma antes del MCP |
| v0 (Vercel) | Pantalla hero del momento de la verdad (entregable S8) | Ajuste de paleta y datos placeholder |
| Mockoon | Contrato JSON de referencia | Curaduría de datos placeholder |

**Prompts clave (mínimo 3, ver versiones completas en `entregable8.md` punto 6.2):**
1. Generación de la pantalla hero "Desglose del Score" en v0.
2. Generación del scaffold del backend FastAPI con Claude Code (este brief).
3. Generación del frontend React + Tailwind + shadcn con lectura desde Figma MCP.

---

## 14. Plan de trabajo sugerido (orden de ataque para Claude Code)

1. **Validación inicial** (5 min): leer este brief, listar dudas, confirmar acceso a Figma MCP y a Bash.
2. **Backend scaffolding** (1 h): estructura de carpetas, `requirements.txt`, `main.py` con `/health`, configuración CORS, `init_db.py` con seed de fuentes e indicadores. Test: `curl localhost:8000/api/v1/health` responde 200.
3. **Modelo de datos** (45 min): tablas SQLAlchemy + Pydantic schemas. Test: `pytest tests/test_models.py`.
4. **Mock scraper + ETL** (1 h): `mock_scraper.py` lee `sample_empresas.csv`, normaliza y persiste. Genera el seed. Test: `python scripts/ingest_sample.py` deja 5 empresas en la DB.
5. **Score engine** (30 min): `services/score.py` con la fórmula. Test: dos casos contrastantes (score alto y bajo) en `test_score.py`.
6. **Endpoints** (1.5 h): los 9 endpoints del punto 6. Verificar que Swagger en `/docs` muestra todo. Test: TestClient en `test_api.py`.
7. **Frontend scaffolding** (45 min): Vite + Tailwind + shadcn + Router. Layout con Sidebar + Header. Página `/` vacía. Test: `npm run dev` y abre en `localhost:5173`.
8. **Lectura del Figma** (15 min): MCP Figma → extracción de design tokens → mapeo a `tailwind.config.ts`.
9. **5 pantallas frontend** (3 h): una por una en el orden de prioridad: Home → EmpresaDetalle → ScoreDesglose (pantalla hero) → Bitacora → ApiExplorer.
10. **Integración E2E** (30 min): conectar fetch desde frontend al backend, configurar `VITE_API_URL`, manejo de errores.
11. **Deploy** (45 min): backend en Render/Railway, frontend en Vercel. Probar URLs públicas desde celular.
12. **Checklist 12 + ajustes finales** (30 min).

Total estimado: **~10 horas de Claude Code activo**. Distribuirlas entre el 21 y el 24 de mayo.

---

**Última nota:** si en algún punto el MCP de Figma no responde o el archivo no existe aún, sigues con backend y avisas al equipo (David, Edwin, Andrea) por el canal del proyecto. **No improvises diseños** desde texto si el Figma existe — siempre prefiere el MCP.
