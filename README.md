# RMK Engineering College — Research Facility Booking

Public booking portal for the Center of Research & Development.

## Stack

- **Frontend:** React + Vite + TypeScript
- **Backend:** Flask API (also serves the built UI in production)
- **Database:** SQLite

## Local development

1. Copy env file:

```bash
copy .env.example .env
```

2. Backend:

```bash
python -m pip install -r requirements.txt
python app.py
```

3. Frontend (new terminal):

```bash
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to Flask on port 5000.

## Deploy on Render (SQLite)

### A. Push this repo to GitHub

Make sure the latest code is on GitHub first.

### B. Create a Web Service on Render

1. Go to [https://dashboard.render.com](https://dashboard.render.com)
2. **New → Web Service**
3. Connect the `laboratory-booking` GitHub repo
4. Use these settings:

| Setting | Value |
|---------|--------|
| Runtime | Python |
| Build Command | `bash build.sh` |
| Start Command | `gunicorn "app:app" --bind 0.0.0.0:$PORT --workers 2 --threads 4` |

5. Environment variables:

| Key | Value |
|-----|--------|
| `FLASK_SECRET_KEY` | Generate a long random string (Render can auto-generate) |
| `ADMIN_API_KEY` | Separate long random string used to delete bookings |
| `DATABASE_PATH` | `data/bookings.db` |
| `PYTHON_VERSION` | `3.12.8` |
| `NODE_VERSION` | `20.18.0` |

6. Deploy. Render will give you a URL like `https://rd-facility-booking.onrender.com`.

You can also use the included `render.yaml` via **New → Blueprint**.

### Important about SQLite on free Render

On the free plan, the filesystem is **ephemeral**. Bookings survive while the service stays up, but a **redeploy/restart can wipe the database**.

For permanent storage:

1. Upgrade to a paid Render plan
2. Add a **Persistent Disk** mounted at `/var/data`
3. Set `DATABASE_PATH=/var/data/bookings.db`

## Production check

After deploy, open:

- Site home: `https://YOUR-APP.onrender.com/`
- Health: `https://YOUR-APP.onrender.com/api/health`
- Bookings API: `https://YOUR-APP.onrender.com/api/bookings`

## Admin delete

Admins can remove bookings from **Booked Details**:

1. Enter the `ADMIN_API_KEY` value and click **Unlock delete**
2. Use **Delete** on any row

API equivalent:

```bash
curl -X DELETE https://YOUR-APP.onrender.com/api/bookings/RD-XXXXXXXX-XXXX ^
  -H "X-Admin-Key: YOUR_ADMIN_API_KEY"
```

## Notes

- Logos: `src/assests/rmk.png`, `src/assests/31yrs.png`
- Local DB file `data/bookings.db` is gitignored
- The portal is currently open (no login). Add CAPTCHA/auth later if spam becomes an issue.
