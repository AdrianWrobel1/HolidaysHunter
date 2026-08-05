# HolidaysHunter

Najwygodniej uruchamiać projekt w trybie developerskim w 3 krokach:

1. Postgres:
   ```powershell
   docker compose up -d postgres
   ```
2. Backend:
   ```powershell
   Set-Location .\backend
   .\.venv\Scripts\python.exe -m alembic upgrade head
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
3. Frontend:
   ```powershell
   Set-Location .\frontend
   npm run dev
   ```

Adresy lokalne:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Healthcheck backendu: `http://localhost:8000/health`

## Najczęstsze problemy

- `localhost:5432` nie działa: backend ma połączenie do Postgresa w `backend/.env`, więc bez uruchomionej bazy endpointy `/api/*` będą zwracały błędy.
- Port `8000` jest zajęty: jeśli `uvicorn` zgłasza `WinError 10048`, zamknij wcześniejszy proces Pythona na tym porcie albo uruchom backend na innym.
- Frontend nie widzi backendu: ustaw `NEXT_PUBLIC_API_URL` na `http://localhost:8000/api` albo samo `http://localhost:8000` - frontend obsłuży teraz oba warianty.

## Cały stack w Dockerze

Jeśli chcesz odpalić wszystko w kontenerach:

```powershell
docker compose -f .\docker-compose.prod.yml up --build
```

To uruchomi Postgresa, backend i frontend razem.
