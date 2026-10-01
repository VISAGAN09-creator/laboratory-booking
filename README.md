# RMK Engineering College — Research Facility Booking

Portal for the Center of Research & Development to book lab slots and view reservations.

## Stack

- **Frontend:** React + Vite + TypeScript
- **Backend:** Flask API
- **Storage:** CSV file (`data/bookings.csv`, created locally)

## Setup

1. Copy environment defaults:

```bash
copy .env.example .env
```

2. Backend:

```bash
python -m pip install -r requirements.txt
python app.py
```

API runs at `http://localhost:5000`.

3. Frontend (new terminal):

```bash
npm install
npm run dev
```

App runs at `http://localhost:5173`.

## Notes

- Logos live in `src/assests/` (`rmk.png`, `31yrs.png`).
- Local booking rows stay in `data/bookings.csv` and are gitignored. A header-only template is committed as `data/bookings.example.csv`.
- Set a strong `FLASK_SECRET_KEY` in `.env` before any shared/production use.
