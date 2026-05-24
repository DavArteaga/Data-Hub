# Prototipo de baja fidelidad — DataCore Hub (Mock API)

**Reto #6 SAPIENCIA 2026 · Softline S.A. · Equipo DataCore Solutions**

Este es el prototipo de baja fidelidad del DataCore Hub para la **Sesión 7 / Demo del 25 de mayo**.
No es la API real: es un *Wizard of Oz* construido con [Mockoon](https://mockoon.com) que responde
con la **forma exacta** del contrato que vamos a construir, usando datos ficticios (Empresa A, B, C…).

Sirve para tres cosas:

1. **Validar el contrato de la API** con el equipo técnico de Softline antes de codificar.
2. **Demostrar la propuesta de valor** end-to-end (búsqueda → detalle → score → histórico) en el pitch.
3. **Desbloquear al equipo de Frontend** del Observatorio: ya pueden integrar contra estos endpoints
   mientras el backend real se construye en paralelo.

---

## 1. Instalar Mockoon

Descargar la app de escritorio (Windows, macOS, Linux): <https://mockoon.com/download/>.
También existe el CLI (`npm i -g @mockoon/cli`) para correrlo sin interfaz.

---

## 2. Importar el entorno

1. Abrir Mockoon Desktop.
2. Menú: **File → Open environment** → elegir `datacore-hub-mock.json`
   *(o arrastrar el archivo a la ventana de Mockoon).*
3. Verificar que aparece el entorno **"DataCore Hub — Mock MVP"** con 7 rutas.
4. Botón verde **▶ Start** (arriba a la izquierda). El servidor arranca en `http://localhost:3001`.

Si prefieres CLI:

```bash
npm install -g @mockoon/cli
mockoon-cli start --data datacore-hub-mock.json --port 3001
```

---

## 3. Endpoints disponibles

Todos cuelgan del prefijo `/api/v1`.

| Método | Endpoint                              | Descripción                                            |
|--------|---------------------------------------|--------------------------------------------------------|
| GET    | `/api/v1/health`                      | Healthcheck del servicio                               |
| GET    | `/api/v1/empresas?ciiu=6201`          | Búsqueda paginada de empresas filtrada por CIIU        |
| GET    | `/api/v1/empresas/{nit}`              | **Detalle consolidado** de una empresa por NIT         |
| GET    | `/api/v1/empresas/{nit}/score`        | **Desglose del score** de confiabilidad por indicador  |
| GET    | `/api/v1/empresas/{nit}/historico`    | **Serie histórica** 2015-2024 de un indicador          |
| GET    | `/api/v1/indicadores`                 | Catálogo de indicadores disponibles                    |
| GET    | `/api/v1/fuentes`                     | Fuentes con tier de confiabilidad y última ingesta     |

### NITs ficticios disponibles

| NIT            | Razón social         | CIIU  | Score global |
|----------------|----------------------|-------|--------------|
| `900111111-1`  | Empresa A S.A.S.     | 6201  | 0.92         |
| `900222222-2`  | Empresa B S.A.S.     | 6201  | 0.85         |
| `900333333-3`  | Empresa C Ltda.      | 6202  | 0.78         |
| `900444444-4`  | Empresa D S.A.       | 6209  | 0.71         |
| `900555555-5`  | Empresa E S.A.S.     | 6201  | 0.66         |
| `900666666-6`  | Empresa F S.A.S.     | 6201  | 0.55         |

Cualquier otro NIT devuelve **404** con un mensaje de error.

---

## 4. Pruebas rápidas (curl)

```bash
# Healthcheck
curl http://localhost:3001/api/v1/health

# Búsqueda
curl "http://localhost:3001/api/v1/empresas?ciiu=6201"

# Detalle consolidado (este es el "wow" del pitch)
curl http://localhost:3001/api/v1/empresas/900111111-1

# Desglose del score (diferenciador exigido por Softline)
curl http://localhost:3001/api/v1/empresas/900111111-1/score

# Serie histórica
curl "http://localhost:3001/api/v1/empresas/900111111-1/historico?indicador=num_empleados"

# Catálogo
curl http://localhost:3001/api/v1/indicadores
curl http://localhost:3001/api/v1/fuentes
```

Si prefieres una UI, abrí los mismos URLs en el navegador o usá Postman / Insomnia / Bruno.

---

## 5. Mapeo con la propuesta de valor

| Flujo del prototipo                   | Gain o Pain Reliever del Lienzo                                             |
|---------------------------------------|------------------------------------------------------------------------------|
| `/empresas?ciiu=` (búsqueda)          | Pain Reliever R3 · API REST única con endpoints centralizados                |
| `/empresas/{nit}` (detalle consolidado)| Gain Creator C1 · Endpoint por ID que retorna info consolidada multifuente   |
| `/empresas/{nit}/score` (desglose)    | Gain Creator C2 · Módulo de score de confiabilidad (diferenciador Softline)  |
| `/empresas/{nit}/historico` (serie)   | Brecha #1 del Mapa de Encaje · Histórico solicitado por la empresa (S6)      |

---

## 6. Cómo iterar el prototipo

1. Abrir el archivo en Mockoon Desktop.
2. Click sobre cualquier ruta → cambiar el **body de la respuesta** (es JSON plano).
3. Guardar (Ctrl+S). Mockoon refresca el servidor automáticamente.
4. Para agregar una respuesta condicional (ej. NIT no encontrado), usar **Rules** en
   cada ruta (`params.nit equals 900xxxxxxx-x`).

---

## 7. Limitaciones (esto es low-fi)

- **No persiste datos**: cada arranque sirve los mismos JSON estáticos.
- **No hace scraping**: los valores son placeholders coherentes con el sector TI.
- **No calcula el score en vivo**: el desglose viene precalculado en el JSON. La fórmula real
  (`0.3·completitud + 0.3·actualidad + 0.4·tier_fuente`) se implementa en la API real (Python/FastAPI).
- **Sin autenticación**: cualquier llamada local responde sin token. La API real usará API Key.

---

## 8. Próximos pasos

- **S7 (esta semana)**: usar este mock para validar el contrato con Softline y para que el
  equipo de Frontend del Observatorio empiece a integrar.
- **S8 → S9**: reemplazar Mockoon por la API real (Python + FastAPI + SQLite) con los scrapers
  de RUES, Cámara de Comercio y Superintendencia conectados a las dos primeras fuentes priorizadas.

---

**Archivo del entorno**: `datacore-hub-mock.json` (en esta misma carpeta).
**Equipo**: David Arteaga · Edwin Molina · Andrea Cifuentes.
