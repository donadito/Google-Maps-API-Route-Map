# Route Optimizer — Algoritmo Genético

Aplicación web que calcula la ruta óptima entre 2 y 15 destinos usando un algoritmo genético. El cálculo corre en una **GCP Cloud Function** (Python); el frontend muestra la ruta en un mapa interactivo de Google Maps con autenticación Firebase.

---

## Arquitectura

```text
[Usuario] → Firebase Auth → [React + Vite (Frontend)]
                                      │  Bearer Token + destinos
                                      ▼
                          [GCP Cloud Function (Python)]
                           ├── Validación de IP
                           ├── Verificación Firebase Token
                           ├── Google Maps Distance Matrix API
                           ├── Algoritmo Genético (GA)
                           └── Google Maps Directions API (polyline)
```

**Stack:**

- **Frontend:** React 19 + TypeScript + Vite, Firebase Auth, Google Maps JS API
- **Backend:** Python 3.12+, `functions-framework` (GCP Cloud Function), `httpx`, Pydantic
- **Autenticación:** Firebase Authentication (email/password)
- **Nube:** Google Cloud Functions (gen 2)
- **APIs externas:** Google Maps Distance Matrix, Google Maps Directions, Google Places Autocomplete

---

## Estructura de carpetas

```text
route-optimizer/
├── README.md
├── .gitignore
│
├── backend/
│   ├── main.py                  # Entry point de la Cloud Function
│   ├── pyproject.toml           # Dependencias Python (uv)
│   ├── uv.lock
│   ├── requirements.txt         # Alternativa pip
│   ├── .env.example
│   └── app/
│       ├── config.py            # Variables de entorno / Settings
│       ├── models.py            # Modelos Pydantic (validación + 100 km)
│       ├── utils.py             # decode_polyline, compute_totals
│       ├── middleware/
│       │   └── auth.py          # Firebase Admin SDK
│       ├── optimizer/
│       │   └── optimizer.py     # Algoritmo genético
│       └── services/
│           ├── cache.py         # Caché SQLite bicapa para Distance Matrix
│           ├── distance_matrix.py
│           └── google_api.py    # Distance Matrix API + Directions API
│
├── Frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── tsconfig.app.json
│   ├── .env.example
│   └── src/
│       ├── App.tsx              # Rutas protegidas (React Router + Firebase)
│       ├── components/
│       │   ├── Login.tsx
│       │   ├── MapCanvas.tsx    # Mapa con marcadores numerados y polyline
│       │   └── PlaceRow.tsx     # Input con Places Autocomplete
│       ├── pages/
│       │   └── RouteOptimizerPage.tsx
│       ├── services/
│       │   ├── firebase.ts
│       │   ├── routeAPI.ts      # POST /optimize con Bearer token
│       │   └── googleMaps.ts
│       ├── hooks/
│       │   └── useGoogleMaps.ts
│       ├── types/
│       │   └── route.tsx
│       └── utils/
│           ├── format.ts
│           ├── geo.ts           # Haversine para validación 100 km
│           └── ids.ts
│
└── Diagramas/
    ├── flow.drawio
    └── architecture.drawio
```

---

## Requisitos previos

- [Node.js 20+](https://nodejs.org/)
- [Python 3.12+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) — gestor de entornos Python
- Cuenta en [Firebase](https://console.firebase.google.com/) con Authentication habilitado (email/password)
- Proyecto en [Google Cloud Platform](https://console.cloud.google.com/) con las siguientes APIs activas:
  - Maps JavaScript API
  - Places API (New)
  - Distance Matrix API
  - Directions API

---

## Instalación y ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-usuario>/Google-Maps-API-Route-Map.git
cd Google-Maps-API-Route-Map
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual e instalar dependencias
uv venv
uv pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env: GOOGLE_MAPS_API_KEY, FIREBASE_CREDENTIALS_PATH, ALLOWED_CLIENT_IPS

# Colocar serviceAccountKey.json en backend/app/serviceAccountKey.json
# (descargar desde Firebase Console > Project Settings > Service Accounts)

# Correr la Cloud Function localmente en el puerto 8080
uv run functions-framework --target optimize --port 8080
```

### 3. Frontend

```bash
cd Frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con las claves de Firebase y Google Maps

# Iniciar servidor de desarrollo
npm run dev
```

La app queda disponible en `http://localhost:5173`.

---

## Variables de entorno

### Backend (`backend/.env`)

| Variable | Descripción |
| --- | --- |
| `GOOGLE_MAPS_API_KEY` | API Key de Google Maps (Distance Matrix + Directions) |
| `FIREBASE_CREDENTIALS_PATH` | Ruta al `serviceAccountKey.json` de Firebase Admin |
| `FIREBASE_PROJECT_ID` | ID del proyecto Firebase (para credenciales por defecto en GCP) |
| `ALLOWED_CLIENT_IPS` | IPs autorizadas separadas por coma. Vacío = permite todas |
| `GA_POPULATION` | Tamaño de la población del GA (default: 180) |
| `GA_GENERATIONS` | Número de generaciones (default: 320) |
| `GA_MUTATION_RATE` | Probabilidad de mutación, 0–1 (default: 0.15) |
| `CORS_ORIGINS` | Orígenes permitidos (default: `http://localhost:5173`) |

### Frontend (`Frontend/.env`)

| Variable | Descripción |
| --- | --- |
| `VITE_FIREBASE_API_KEY` | API Key del proyecto Firebase |
| `VITE_FIREBASE_AUTH_DOMAIN` | Auth domain de Firebase |
| `VITE_FIREBASE_PROJECT_ID` | ID del proyecto Firebase |
| `VITE_FIREBASE_STORAGE_BUCKET` | Storage bucket |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Sender ID |
| `VITE_FIREBASE_APP_ID` | App ID |
| `VITE_API_BASE_URL` | URL de la Cloud Function (local: `http://localhost:8080`) |
| `VITE_GOOGLE_MAPS_API_KEY` | API Key para el mapa en el frontend |

---

## Despliegue en GCP Cloud Functions

```bash
cd backend

gcloud functions deploy optimize \
  --gen2 \
  --runtime python312 \
  --trigger-http \
  --entry-point optimize \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_MAPS_API_KEY=<key>,FIREBASE_PROJECT_ID=<id>,ALLOWED_CLIENT_IPS=<ip>,CORS_ORIGINS=<frontend-url>
```

> **Importante:** las credenciales de Firebase se manejan en GCP con Application Default Credentials — no se sube ningún archivo JSON al repositorio.

---

## Algoritmo Genético

| Componente | Implementación |
| --- | --- |
| **Cromosoma** | Permutación de índices de destinos |
| **Fitness** | Distancia total de la ruta (a minimizar) |
| **Selección** | Torneo de tamaño configurable |
| **Cruce** | Order Crossover (OX) |
| **Mutación** | Swap de dos posiciones aleatorias |
| **Elitismo** | Se preserva el top `elite_rate` de cada generación |
| **Semilla inicial** | Solución greedy (vecino más cercano) + individuos aleatorios |
| **Criterio de parada** | Número fijo de generaciones |
