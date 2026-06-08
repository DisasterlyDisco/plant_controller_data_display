import requests
from flask import Flask, request, Response

app = Flask(__name__)

CONTROLLER_API = "http://192.168.0.139:8099"


def proxy_get(path):
    r = requests.get(f"{CONTROLLER_API}{path}", params=request.args)
    return Response(r.content, status=r.status_code,
                    content_type=r.headers.get("content-type", "application/json"))


@app.route("/api/sensing")
def sensing():
    return proxy_get("/sensing")


@app.route("/api/sensing/<unit>")
def sensing_unit(unit):
    return proxy_get(f"/sensing/{unit}")


@app.route("/api/sensing/<unit>/<parameter>")
def sensing_data(unit, parameter):
    return proxy_get(f"/sensing/{unit}/{parameter}")


@app.route("/api/actuation")
def actuation():
    return proxy_get("/actuation")


@app.route("/api/actuation/<unit>/show_schedule")
def show_schedule(unit):
    return proxy_get(f"/actuation/{unit}/show_schedule")


@app.route("/api/actuation/<unit>/watering_events")
def watering_events(unit):
    return proxy_get(f"/actuation/{unit}/watering_events")


@app.route("/")
def dashboard():
    return DASHBOARD_HTML


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Plant Controller Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.35.0.min.js"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         background: #1a1a2e; color: #e0e0e0; }
  header { background: #16213e; padding: 12px 24px; display: flex;
           justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; }
  header h1 { font-size: 1.3rem; color: #e0e0e0; }
  .header-right { display: flex; align-items: center; gap: 16px; }
  #status { font-size: 0.85rem; color: #888; }
  #status .dot { display: inline-block; width: 8px; height: 8px;
                 border-radius: 50%; margin-right: 6px; background: #555; }
  #status.live .dot { background: #4caf50; }
  .window-btns { display: flex; gap: 4px; }
  .window-btns button { background: #2a2a4a; color: #aaa; border: 1px solid #3a3a5a;
    border-radius: 4px; padding: 5px 12px; cursor: pointer; font-size: 0.8rem; }
  .window-btns button.active { background: #4fc3f7; color: #1a1a2e; border-color: #4fc3f7; }
  .window-btns button:hover:not(.active) { background: #3a3a5a; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
          padding: 12px; max-width: 1600px; margin: 0 auto; }
  .card { background: #16213e; border-radius: 8px; padding: 12px;
          border: 1px solid #2a2a4a; }
  .card h2 { font-size: 0.9rem; color: #aaa; margin-bottom: 4px; }
  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
               padding: 0 12px; max-width: 1600px; margin: 0 auto; }
  .stat-card { background: #16213e; border-radius: 8px; padding: 16px;
               border: 1px solid #2a2a4a; text-align: center; }
  .stat-card h2 { font-size: 0.8rem; color: #888; margin-bottom: 6px; }
  .stat-card .value { font-size: 1.6rem; font-weight: 700; }
  .stat-card .unit { font-size: 0.8rem; color: #666; }
  .plot { width: 100%; height: 280px; }
  @media (max-width: 900px) {
    .grid { grid-template-columns: 1fr; }
    .stats-row { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>

<header>
  <h1>Plant Controller Dashboard</h1>
  <div class="header-right">
    <div class="window-btns">
      <button class="active" data-minutes="30">30 min</button>
      <button data-minutes="240">4 hours</button>
      <button data-minutes="480">8 hours</button>
      <button data-minutes="720">12 hours</button>
      <button data-minutes="1440">24 hours</button>
      <button data-minutes="10080">7 days</button>
    </div>
    <div id="status"><span class="dot"></span>Connecting...</div>
  </div>
</header>

<div class="stats-row" style="margin-top: 12px; margin-bottom: 0;">
  <div class="stat-card">
    <h2>Soil Moisture</h2>
    <div class="value" id="val-moisture" style="color:#4fc3f7">--</div>
    <div class="unit">% RH</div>
  </div>
  <div class="stat-card">
    <h2>Soil Temperature</h2>
    <div class="value" id="val-soil-temp" style="color:#ef5350">--</div>
    <div class="unit">&deg;C</div>
  </div>
  <div class="stat-card">
    <h2>Air Temperature</h2>
    <div class="value" id="val-air-temp" style="color:#ff7043">--</div>
    <div class="unit">&deg;C</div>
  </div>
  <div class="stat-card">
    <h2>Air Humidity</h2>
    <div class="value" id="val-humidity" style="color:#42a5f5">--</div>
    <div class="unit">%</div>
  </div>
</div>

<div class="grid">
  <div class="card">
    <h2>Soil Moisture</h2>
    <div id="plot-moisture" class="plot"></div>
  </div>
  <div class="card">
    <h2>Soil Temperature</h2>
    <div id="plot-soil-temp" class="plot"></div>
  </div>
  <div class="card">
    <h2>Greenhouse Air</h2>
    <div id="plot-air" class="plot"></div>
  </div>
  <div class="card">
    <h2>Soil Electrical Conductivity</h2>
    <div id="plot-ec" class="plot"></div>
  </div>
  <div class="card">
    <h2>Light Levels Over Time</h2>
    <div id="plot-light-time" class="plot"></div>
  </div>
  <div class="card">
    <h2>Watering History</h2>
    <div id="plot-watering" class="plot"></div>
  </div>
</div>

<script>
const WINDOWS = {
  30:    { pollMs: 5000,   bucketLabel: "minute" },
  240:   { pollMs: 15000,  bucketLabel: "hour" },
  480:   { pollMs: 15000,  bucketLabel: "hour" },
  720:   { pollMs: 30000,  bucketLabel: "hour" },
  1440:  { pollMs: 30000,  bucketLabel: "hour" },
  10080: { pollMs: 300000, bucketLabel: "day" },
};

let windowMinutes = 30;
let pollTimer = null;
let initialized = false;

const plotLayout = {
  paper_bgcolor: "transparent", plot_bgcolor: "transparent",
  font: { color: "#aaa", size: 11 },
  margin: { l: 50, r: 20, t: 10, b: 35 },
  xaxis: { gridcolor: "#2a2a4a", type: "date" },
  yaxis: { gridcolor: "#2a2a4a" },
};

const plotConfig = { displayModeBar: false, responsive: true };

const WL_COLORS = {
  "415nm": "#7b00ff", "445nm": "#0028ff", "480nm": "#00b0ff",
  "515nm": "#00ff2b", "555nm": "#7bff00", "590nm": "#ffb000",
  "630nm": "#ff4400", "680nm": "#cc0000", "910nm": "#800000",
};

const LIGHT_CHANNELS = [
  "light_level_415nm", "light_level_445nm", "light_level_480nm",
  "light_level_515nm", "light_level_555nm", "light_level_590nm",
  "light_level_630nm", "light_level_680nm", "light_level_infrared_910nm",
];

function sinceParam() {
  const d = new Date(Date.now() - windowMinutes * 60000);
  const pad = (n, w=2) => String(n).padStart(w, "0");
  return `${d.getFullYear()}${pad(d.getMonth()+1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

function channelLabel(param) {
  return param.replace("light_level_", "").replace("infrared_", "");
}

async function fetchJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${r.status}`);
  return r.json();
}

function parseSeries(data) {
  const times = data.map(d => d.time);
  const values = data.map(d => d.value);
  return { times, values };
}

function makeLine(times, values, color) {
  return { x: times, y: values, type: "scattergl", mode: "lines",
           line: { color, width: 1.5 } };
}

function localISO(d) {
  const pad = (n, w=2) => String(n).padStart(w, "0");
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function truncateToBucket(d) {
  const b = WINDOWS[windowMinutes].bucketLabel;
  if (b === "minute") return new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours(), d.getMinutes());
  if (b === "hour")   return new Date(d.getFullYear(), d.getMonth(), d.getDate(), d.getHours());
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function aggregateWatering(events) {
  const stepMs = { minute: 60000, hour: 3600000, day: 86400000 }[WINDOWS[windowMinutes].bucketLabel];
  const start = truncateToBucket(new Date(Date.now() - windowMinutes * 60000));
  const end = truncateToBucket(new Date());

  const buckets = new Map();
  for (let t = start.getTime(); t <= end.getTime(); t += stepMs) {
    buckets.set(t, 0);
  }
  for (const ev of events) {
    const key = truncateToBucket(new Date(ev.time)).getTime();
    if (buckets.has(key)) buckets.set(key, buckets.get(key) + (ev.value || 0));
  }

  const sorted = Array.from(buckets.entries()).sort((a, b) => a[0] - b[0]);
  return { times: sorted.map(e => localISO(new Date(e[0]))), values: sorted.map(e => e[1]) };
}

// Window button handling
document.querySelectorAll(".window-btns button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".window-btns button").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    windowMinutes = parseInt(btn.dataset.minutes);
    initialized = false;
    if (pollTimer) clearInterval(pollTimer);
    update();
    pollTimer = setInterval(update, WINDOWS[windowMinutes].pollMs);
  });
});

async function update() {
  const since = sinceParam();
  const qs = `?since_timestamp=${since}`;

  try {
    const results = await Promise.all([
      fetchJSON(`/api/sensing/purple_ufo/soil_moisture${qs}`),
      fetchJSON(`/api/sensing/purple_ufo/soil_temperature${qs}`),
      fetchJSON(`/api/sensing/purple_ufo/soil_electrical_conductivity${qs}`),
      fetchJSON(`/api/sensing/greenhouse/air_temperature${qs}`),
      fetchJSON(`/api/sensing/greenhouse/air_humidity${qs}`),
      fetchJSON(`/api/actuation/purple_ufo/watering_events${qs}`).catch(() => []),
      ...LIGHT_CHANNELS.map(ch => fetchJSON(`/api/sensing/greenhouse/${ch}${qs}`)),
    ]);

    const [moisture, soilTemp, ec, airTemp, humidity, wateringEvents, ...lightData] = results;

    // Update stat cards
    if (moisture.length) document.getElementById("val-moisture").textContent = moisture[0].value.toFixed(1);
    if (soilTemp.length) document.getElementById("val-soil-temp").textContent = soilTemp[0].value.toFixed(1);
    if (airTemp.length) document.getElementById("val-air-temp").textContent = airTemp[0].value.toFixed(1);
    if (humidity.length) document.getElementById("val-humidity").textContent = humidity[0].value.toFixed(1);

    const fn = initialized ? Plotly.react : Plotly.newPlot;
    const xRange = [localISO(new Date(Date.now() - windowMinutes * 60000)), localISO(new Date())];
    const rangedX = { ...plotLayout.xaxis, range: xRange };

    // Soil moisture
    const m = parseSeries(moisture);
    fn("plot-moisture", [makeLine(m.times, m.values, "#4fc3f7")],
       { ...plotLayout, xaxis: rangedX, yaxis: { ...plotLayout.yaxis, title: "% RH" } }, plotConfig);

    // Soil temp
    const st = parseSeries(soilTemp);
    fn("plot-soil-temp", [makeLine(st.times, st.values, "#ef5350")],
       { ...plotLayout, xaxis: rangedX, yaxis: { ...plotLayout.yaxis, title: "\u00b0C" } }, plotConfig);

    // EC
    const e = parseSeries(ec);
    fn("plot-ec", [makeLine(e.times, e.values, "#66bb6a")],
       { ...plotLayout, xaxis: rangedX, yaxis: { ...plotLayout.yaxis, title: "\u03bcS/cm" } }, plotConfig);

    // Air temp + humidity (dual y-axis)
    const at = parseSeries(airTemp);
    const ah = parseSeries(humidity);
    fn("plot-air", [
      { ...makeLine(at.times, at.values, "#ef5350"), name: "Temp \u00b0C", yaxis: "y" },
      { ...makeLine(ah.times, ah.values, "#42a5f5"), name: "Humidity %", yaxis: "y2" },
    ], {
      ...plotLayout, xaxis: rangedX, showlegend: true,
      legend: { x: 0, y: 1, font: { size: 10 } },
      yaxis: { ...plotLayout.yaxis, title: "\u00b0C", titlefont: { color: "#ef5350" } },
      yaxis2: { overlaying: "y", side: "right", title: "%",
                titlefont: { color: "#42a5f5" }, gridcolor: "transparent" },
    }, plotConfig);

    // All light channels over time
    const lightTraces = [];
    LIGHT_CHANNELS.forEach((ch, i) => {
      if (lightData[i] && lightData[i].length) {
        const s = parseSeries(lightData[i]);
        const label = channelLabel(ch);
        lightTraces.push({
          ...makeLine(s.times, s.values, WL_COLORS[label] || "#888"),
          name: label,
        });
      }
    });
    fn("plot-light-time", lightTraces, {
      ...plotLayout, xaxis: rangedX, showlegend: true,
      legend: { x: 0, y: 1, font: { size: 10 } },
      yaxis: { ...plotLayout.yaxis, title: "photons/s" },
    }, plotConfig);

    // Watering history bar chart
    const w = aggregateWatering(wateringEvents);
    fn("plot-watering", [{
      x: w.times, y: w.values, type: "bar",
      marker: { color: "#4fc3f7" },
    }], {
      ...plotLayout, xaxis: rangedX,
      yaxis: { ...plotLayout.yaxis, title: "ml" },
    }, plotConfig);

    initialized = true;
    document.getElementById("status").className = "live";
    document.getElementById("status").innerHTML =
      `<span class="dot"></span>Live &mdash; updated ${new Date().toLocaleTimeString()}`;

  } catch (err) {
    document.getElementById("status").className = "";
    document.getElementById("status").innerHTML =
      `<span class="dot" style="background:#f44336"></span>Error: ${err.message}`;
  }
}

update();
pollTimer = setInterval(update, WINDOWS[windowMinutes].pollMs);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
