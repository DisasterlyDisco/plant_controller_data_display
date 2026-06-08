# Plant Controller Data Display

Live web dashboard for a plant controller system running on the local network.

## Architecture

- **Plant controller API**: FastAPI service at `192.168.0.139:8099` (OpenAPI spec at `/docs`)
- **Dashboard server** (`server.py`): Flask app that proxies the controller API and serves a single-page Plotly.js dashboard
  - Binds to `0.0.0.0:8050` for LAN-wide access
  - All API requests proxied through `/api/...` (GET and PUT) to avoid CORS issues
  - Frontend polls the backend at intervals that vary by time window (5s–5min)
  - HTML/CSS/JS is embedded as a string in the Python file (no separate static files)

## Plant Controller API

Two units:
- `purple_ufo` — soil sensors (moisture, temperature, EC at 1s intervals) + pump actuation (watering schedule & events)
- `greenhouse` — 9-channel spectral light sensor (415nm–910nm at 15s intervals) + air temperature & humidity

Key endpoints:
- `GET /sensing/{unit}/{parameter}?limit=N&since_timestamp=YYYYMMDD-hhmmss`
- `GET /actuation/{unit}/watering_events?since_timestamp=...`
- `GET /actuation/{unit}/show_schedule` — returns `{"type": "daily", "description": "...", "schedule": [{"time": "HH:MM:SS", "dose": N}]}`
- `PUT /actuation/{unit}/update_schedule` — body: `{"type": "...", "schedule": ...}`, returns 204 on success

Watering events return `{"physical_unit": "...", "time": "ISO8601", "value": N, "units": "ml"}`.

## Dashboard Features

- **Live charts**: soil moisture, soil temperature, soil EC, greenhouse air (dual-axis temp+humidity), 9-channel spectral light, watering history bar chart
- **Stat cards**: latest values for soil moisture, soil temp, air temp, humidity
- **Time window selector**: 30min, 4h, 8h, 12h, 24h, 7d — adjusts data range and poll interval
- **Ad hoc watering** ("Water Now" button):
  - Dose picker with slider (0–500ml) and input field (any non-negative integer; confirms if >500ml)
  - Saves current schedule, uploads a one-shot daily schedule (event 15s in the future), polls for the watering event (up to 45s), then restores the original schedule regardless of outcome
  - Full-screen overlay shows progress and success/failure

## Running

```bash
nix-shell --run "python3 server.py"
```

## Environment

NixOS system — use `shell.nix` for dependencies (Python 3 with flask, matplotlib, requests). No venv or pip.
