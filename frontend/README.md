# MeteoFusion frontend

## Desarrollo

Con el backend ejecutandose en `http://127.0.0.1:8000`:

```powershell
npm.cmd ci
npm.cmd run dev
```

La aplicacion estara disponible en `http://127.0.0.1:5173`.

Para usar otro backend, crea `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Comprobaciones

```powershell
npm.cmd run typecheck
npm.cmd run build
npm.cmd run test:e2e
```

La prueba de navegador usa Microsoft Edge, instalado por defecto en Windows.
