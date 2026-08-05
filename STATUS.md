# HolidaysHunter — STATUS

## Aktualny stan: MVP Backend & Frontend PWA COMPLETE ✅

Cały projekt HolidaysHunter został ukończony zgodnie z architekturą i specyfikacją PRD.

## Etapy

| Etap | Zakres | Status |
|------|--------|--------|
| 1 | Konfiguracja, baza danych, model Offer, pierwszy importer | DONE |
| 2 | Pozostali operatorzy, normalizacja, historia cen | DONE |
| 3 | Explorer, filtry, Backend API | DONE |
| 4 | Travel Profiles, Travel Score, Alert Engine | DONE |
| 5 | Telegram, testy, optymalizacja | DONE |
| 6 | Frontend PWA (Next.js + TypeScript + Tailwind) | DONE |

## Architektura i Przepływ Systemu

```
Travel APIs (Itaka, TUI, Rainbow, Wakacje.pl)
     |
     v
 Importers (4 providery + normalizery)
     |
     v
 Import Service (upsert + price history)
     |
     v
 Database (PostgreSQL + Alembic migracje)
     |
     v
 Scoring Engine (Travel Score 0-100)
     |
     v
 Alert Engine (5 reguł alertów)
     |
     v
 Notification Service (Telegram Bot API)
     |
     v
 Backend API (FastAPI REST)
     |
     v
 Frontend (Next.js PWA + Glassmorphism UI)
```

## Podsumowanie komponentów

### Backend
- **Framework**: FastAPI (Python 3.12+), SQLAlchemy 2.0 Async, Pydantic v2.
- **Testy**: 107/107 passed (Pytest).
- **Providery**: Itaka, TUI, Rainbow, Wakacje.pl.
- **Analiza & Scoring**: Algorytm Travel Score 0-100 oparty o 5 metryk.
- **Powiadomienia**: Telegram Bot API z formatowaniem HTML.

### Frontend PWA
- **Framework**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS.
- **Komponenty**:
  - **Explorer**: wyszukiwarka z 17 filtrami, sortowaniem, paginacją i podglądem kart ofert.
  - **OfferModal & PriceHistoryChart**: os czasu i wykres zmian cen ofert.
  - **Travel Profiles**: panel tworzenia i automatycznego śledzenia budżetu/krajów 24/7.
  - **Smart Alerts**: powiadomienia z oznaczaniem jako przeczytane i licznikami unread.
  - **PWA Support**: Web App Manifest (`manifest.json`), ikony SVG i meta tagi.

## Jak uruchomić projekt

1. **Baza danych**:
   ```bash
   docker-compose up -d
   ```
2. **Backend**:
   ```bash
   cd backend
   .venv\Scripts\activate
   alembic upgrade head
   uvicorn app.main:app --reload
   ```
3. **Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
   Aplikacja będzie dostępna pod adresem: `http://localhost:3000`.
