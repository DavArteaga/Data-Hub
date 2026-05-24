# DataCore Hub

> Reto #6 SAPIENCIA 2026 · Softline S.A. · Equipo **DataCore Solutions** (Grupo 1)
> David Arteaga · Edwin Molina · Andrea Cifuentes
> Demo: lunes 25/05/2026 13:00

Plataforma de ingesta multifuente, normalización a modelo común y exposición
REST con **score de confiabilidad** explícito por dato, para el Observatorio
TIC de Softline.

- Backend: FastAPI + SQLAlchemy + SQLite + Playwright
- Frontend: React 18 + Vite + TypeScript + Tailwind + shadcn-style UI
- Diseño: Google Stitch (design tokens en `frontend/tailwind.config.ts`)

---

## Quick start local

### Backend (puerto 8000)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate           # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
python -m playwright install chromium   # opcional, sólo si se va a probar RUES/SIIS
uvicorn app.main:app --reload
```

El primer arranque crea SQLite vacío y lo siembra automáticamente (6 fuentes,
3 indicadores, 6 empresas ficticias, 10 años de histórico).

Swagger: <http://localhost:8000/docs>
Health:  <http://localhost:8000/api/v1/health>

### Frontend (puerto 5173)

```bash
cd frontend
npm install
npm run dev
```

`.env` ya apunta a `http://localhost:8000/api/v1` por defecto.

App: <http://localhost:5173>

---

## Endpoints REST (`/api/v1`)

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/health` | Healthcheck |
| GET | `/empresas?ciiu={code}&page={n}&size={s}` | Búsqueda paginada |
| GET | `/empresas/{nit}` | Detalle consolidado con score global |
| GET | `/empresas/{nit}/score?indicador={codigo}` | Desglose del score con consenso entre fuentes |
| GET | `/empresas/{nit}/historico?indicador={codigo}` | Serie temporal 2015–2024 |
| GET | `/indicadores` | Catálogo de indicadores |
| GET | `/fuentes` | Catálogo de fuentes con tier |
| POST | `/ingesta/{fuente_nombre}` | Dispara ingesta |
| GET | `/bitacora?limit={n}` | Últimas N entradas de bitácora |

Documentación interactiva en `/docs`.

---

## Score de confiabilidad

```
score = 0.3 · completitud + 0.3 · actualidad + 0.4 · tier_fuente
```

- `completitud` ∈ [0,1] — fracción de campos esperados no nulos
- `actualidad`  ∈ [0,1] — `max(0, 1 - años_desde_dato / 10)`
- `tier_fuente` ∈ [0,1] — viene de la tabla `fuentes` (0.70–0.95)

Implementado en `backend/app/services/score.py` con `explain()` que devuelve el
paso a paso (lo consume la pantalla hero `/empresas/:nit/score/:indicador`).

---

## Estado de los scrapers (verificación 2026-05-24)

| Fuente | Scraper | Estado |
|---|---|---|
| MockScraper (CSV) | `mock_scraper.py` | ✅ OK |
| datos.gov.co | `datos_gov_scraper.py` (Socrata API) | ✅ OK con NITs reales |
| DIAN | fallback → Mock | ✅ OK (no hay scraper real implementado) |
| Cámara de Comercio | fallback → Mock | ✅ OK (no hay scraper real implementado) |
| RUES | `rues_scraper.py` (Playwright) | ❌ Selectores frágiles |
| Superintendencia | `siis_scraper.py` (Playwright) | ❌ Selectores frágiles |
| DANE | `dane_scraper.py` (httpx Excel) | ❌ URL del Excel obsoleta |

Para correr el diagnóstico completo:
```bash
cd backend
python scripts/verify_scrapers.py
```

---

## Deploy

El stack de deploy es **Render (backend) + Vercel (frontend)**.
Ambos servicios despliegan automáticamente desde GitHub.

### 1. Subir a GitHub (una sola vez)

```bash
git init
git branch -m main
git add .
git commit -m "Initial commit: DataCore Hub MVP"
# Crea el repo en https://github.com/new (vacío, sin README/license)
git remote add origin https://github.com/<usuario>/datacore-hub.git
git push -u origin main
```

> ⚠ Confirma que `.gitignore` excluyó `.venv/`, `node_modules/`, `*.db`, `.env`
> y `key*.env`. Si por error se cuela alguno, **NO** subas y limpia primero.

### 2. Backend en Render

1. Entra a <https://dashboard.render.com>.
2. **New +** → **Blueprint**.
3. Conecta el repo de GitHub.
4. Render detecta automáticamente `backend/render.yaml` y crea el servicio
   `datacore-hub-api` (free tier, runtime Python 3.11, region Oregon).
5. Click **Apply** y espera ~3–5 min al primer build.
6. La URL pública queda en `https://datacore-hub-api.onrender.com`.
   Verifica con: `curl https://datacore-hub-api.onrender.com/api/v1/health`.

> Nota: el free tier hiberna después de 15 min de inactividad. El primer
> request post-hibernación tarda ~30 s en despertar (cold start). Demo-day,
> hacer un health-check 5 min antes para dejarlo caliente.

> Nota: SQLite vive en `/tmp/datahub.db`, que se borra al hibernar; el
> auto-seed reinserta los 6 fuentes + 6 empresas + 10 años de histórico
> en cada arranque (~2 s).

### 3. Frontend en Vercel

1. Entra a <https://vercel.com/new>.
2. **Import Git Repository** → selecciona el mismo repo.
3. En **Framework Preset** debe aparecer **Vite** (auto-detectado por `vercel.json`).
4. **Root Directory** → `frontend`.
5. **Environment Variables** → agrega:
   - Key: `VITE_API_URL`
   - Value: `https://datacore-hub-api.onrender.com/api/v1`
   - Environments: ☑ Production, ☑ Preview, ☑ Development
6. Click **Deploy** y espera ~1–2 min.
7. La URL pública queda en `https://<repo-name>.vercel.app`.

### 4. (Opcional) Endurecer CORS

En el dashboard de Render → datacore-hub-api → Environment, cambia:

```
CORS_ORIGINS=https://<repo-name>.vercel.app
```

Y haz redeploy. Esto reemplaza el wildcard `*` por el host real de Vercel.

---

## Estructura del repositorio

```
DataCoreHub_MVP/
├── PROJECT_BRIEF.md             ← brief original del proyecto
├── README.md                    ← este archivo
├── .gitignore
├── prototipo_mockoon/           ← contrato JSON de referencia (NO modificar)
├── backend/
│   ├── render.yaml              ← config para Render
│   ├── Procfile                 ← alternativa Railway/Heroku
│   ├── runtime.txt              ← Python 3.11.9
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py              ← FastAPI app + lifespan auto-seed
│   │   ├── routers/             ← 5 routers
│   │   ├── models/              ← SQLAlchemy + Pydantic schemas
│   │   ├── services/            ← score + normalizer
│   │   ├── scrapers/            ← 6 scrapers (4 reales + Mock)
│   │   └── etl/pipeline.py
│   ├── scripts/
│   │   ├── init_db.py           ← seed (importado por lifespan)
│   │   └── verify_scrapers.py   ← diagnóstico de salud de scrapers
│   ├── tests/                   ← pytest
│   └── data/raw/sample_empresas.csv
└── frontend/
    ├── vercel.json              ← config para Vercel
    ├── .env                     ← VITE_API_URL local
    ├── .env.production.example  ← plantilla para producción
    ├── package.json
    ├── tailwind.config.ts       ← design tokens de Stitch
    ├── index.html
    └── src/
        ├── App.tsx              ← router + Layout
        ├── lib/api.ts           ← cliente axios tipado
        ├── components/          ← Sidebar, Header, UI primitives
        └── pages/               ← Home, EmpresaDetalle, ScoreDesglose,
                                    ApiExplorer, Bitacora
```

---

## Convención de commits

Una sola cosa por commit. Mensajes en español o inglés (coherente).
Ejemplos:

```
feat(backend): add auto-seed on lifespan startup
fix(score): handle null valor_numerico in completitud
docs: add deploy instructions for Render + Vercel
```

---

## Tests

```bash
cd backend && pytest -v
```

---

## Créditos

Generado con asistencia de Claude Code (Anthropic) a partir del
`PROJECT_BRIEF.md`. Revisión y validación final por el equipo.
