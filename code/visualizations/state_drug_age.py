import pandas as pd
import json
import os

DATA_DIR = "../../data/state_data"
OUT_PATH = "../../outputs/state_drug_age.html"

states = sorted([f.replace(".csv", "") for f in os.listdir(DATA_DIR) if f.endswith(".csv")])

SUBSTANCES = [
    "All Substances", "Alcohol Only", "Heroin", "Other opiates",
    "Cocaine (smoked)", "Cocaine (other route)", "Marijuana",
    "Amphetamines", "Tranquilizers",
]

COLORS = [
    "#1a2557", "#3d4f8a", "#6b7db3", "#9ba8cc",
    "#c94f7c", "#4a6fa5", "#e07b39", "#5aaa72", "#a05195",
]


def load_state(state_name):
    path = os.path.join(DATA_DIR, f"{state_name}.csv")
    df = pd.read_csv(path)
    label_col = df.columns[1]
    age_df = df[df[label_col].str.contains("years|year", na=False)].copy()
    age_df = age_df.rename(columns={label_col: "Age Group"})
    age_df["Age Group"] = age_df["Age Group"].str.strip()
    return age_df


# Build data dict: { "ALABAMA": { "ages": [...], "SUBSTANCE": [...], ... }, ... }
all_data = {}
age_groups = None
for state in states:
    sd = load_state(state)
    if age_groups is None:
        age_groups = sd["Age Group"].tolist()
    entry = {"ages": sd["Age Group"].tolist()}
    for sub in SUBSTANCES:
        entry[sub] = sd[sub].tolist() if sub in sd.columns else [0] * len(sd)
    all_data[state] = entry

state_labels = {s: s.title().replace("Of", "of") for s in states}

data_json = json.dumps(all_data)
labels_json = json.dumps(state_labels)
substances_json = json.dumps(SUBSTANCES)
colors_json = json.dumps(COLORS)
first_state = states[0]

html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>
  body {{ margin: 0; padding: 0; font-family: sans-serif; background: white; }}
  #controls {{ display: flex; align-items: center; gap: 12px; padding: 10px 14px 0 14px; }}
  select {{ font-size: 13px; padding: 4px 8px; border-radius: 4px; border: 1px solid #ccc; }}
  #chart-title {{ font-size: 15px; font-weight: bold; text-align: center; flex: 1; color: #222; }}
  #chart {{ width: 100%; }}
</style>
</head>
<body>
<div id="controls">
  <select id="state-select" onchange="updateChart()">
{"".join(f'    <option value="{s}">{state_labels[s]}</option>' for s in states)}
  </select>
  <div id="chart-title">Drug Use by Age Group &mdash; {state_labels[first_state]}</div>
</div>
<div id="chart"></div>

<script>
const ALL_DATA = {data_json};
const STATE_LABELS = {labels_json};
const SUBSTANCES = {substances_json};
const COLORS = {colors_json};

function buildTraces(state) {{
  const d = ALL_DATA[state];
  return SUBSTANCES.map((sub, i) => ({{
    type: "bar",
    name: sub,
    x: d.ages,
    y: d[sub],
    marker: {{ color: COLORS[i % COLORS.length] }},
  }}));
}}

const layout = {{
  barmode: "group",
  height: 420,
  margin: {{ l: 40, r: 20, t: 20, b: 120 }},
  xaxis: {{ title: "Age Group" }},
  yaxis: {{ title: "Usage (%)", range: [0, 50] }},
  legend: {{ orientation: "h", x: 0.5, xanchor: "center", y: -0.35, yanchor: "top", font: {{ size: 10 }} }},
  plot_bgcolor: "white",
  paper_bgcolor: "white",
}};

// Initial render
const initState = "{first_state}";
Plotly.newPlot("chart", buildTraces(initState), layout, {{responsive: true, displayModeBar: false}});

function updateChart() {{
  const state = document.getElementById("state-select").value;
  document.getElementById("chart-title").textContent = "Drug Use by Age Group \u2014 " + STATE_LABELS[state];
  Plotly.react("chart", buildTraces(state), layout);
}}
</script>
</body>
</html>"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Saved to {OUT_PATH}")
