# Plant Controller Data Display

Live web dashboard for a plant controller system running on the local network.

## Architecture

- **Plant controller API**: FastAPI service at `192.168.0.139:8099` (OpenAPI spec at `/docs`)
- **Dashboard server** (`server.py`): Flask app that proxies the controller API and serves a single-page Plotly.js dashboard
  - Binds to `0.0.0.0:8050` for LAN-wide access
  - All API requests proxied through `/api/...` to avoid CORS issues
  - Frontend polls the backend at intervals that vary by time window (5s–5min)
  - HTML/CSS/JS is embedded as a string in the Python file (no separate static files)

## Plant Controller API

Two units:
- `purple_ufo` — soil sensors (moisture, temperature, EC at 1s intervals) + pump actuation (watering schedule & events)
- `greenhouse` — 9-channel spectral light sensor (415nm–910nm at 15s intervals) + air temperature & humidity

Key endpoints:
- `GET /sensing/{unit}/{parameter}?limit=N&since_timestamp=YYYYMMDD-hhmmss`
- `GET /actuation/{unit}/watering_events?since_timestamp=...`
- `GET /actuation/{unit}/show_schedule`
- `PUT /actuation/{unit}/update_schedule` (body: `{"type": "...", "schedule": ...}`)

Watering events return `{"time": "...", "value": 100, "units": "ml"}`.

## Running

```bash
nix-shell --run "python3 server.py"
```

## Environment

NixOS system — use `shell.nix` for dependencies (Python 3 with flask, matplotlib, requests). No venv or pip.
